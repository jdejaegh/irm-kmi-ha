"""Create graphs for rain short term forecast."""
import asyncio
import base64
import copy
import datetime
import logging
import os
from typing import List, Self, Any, Coroutine

import async_timeout
from aiofile import async_open
from homeassistant.util import dt
from svgwrite import Drawing
from svgwrite.animate import Animate
from svgwrite.container import FONT_TEMPLATE
from svgwrite.utils import font_mimetype

from .api import IrmKmiApiClient
from .radar_data import AnimationFrameData, RadarAnimationData
from .roboto import roboto_b64

_LOGGER = logging.getLogger(__name__)


class RainGraph:
    def __init__(self,
                 animation_data: RadarAnimationData,
                 background_image_path: str,
                 background_size: (int, int),
                 config_dir: str = '.',
                 dark_mode: bool = False,
                 tz: datetime.tzinfo = dt.get_default_time_zone(),
                 svg_width: float = 640,
                 inset: float = 20,
                 graph_height: float = 150,
                 top_text_space: float = 30,
                 top_text_y_pos: float = 20,
                 bottom_text_space: float = 50,
                 bottom_text_y_pos: float = 218,
                 api_client: IrmKmiApiClient | None = None
                 ):

        self._animation_data: RadarAnimationData = animation_data
        self._background_image_path: str = background_image_path
        self._background_size: (int, int) = background_size
        self._config_dir: str = config_dir
        self._dark_mode: bool = dark_mode
        self._tz = tz
        self._svg_width: float = svg_width
        self._inset: float = inset
        self._graph_height: float = graph_height
        self._top_text_space: float = top_text_space + background_size[1]
        self._top_text_y_pos: float = top_text_y_pos + background_size[1]
        self._bottom_text_space: float = bottom_text_space
        self._bottom_text_y_pos: float = bottom_text_y_pos + background_size[1]
        self._api_client = api_client

        self._frame_count: int = len(self._animation_data['sequence'])
        self._graph_width: float = self._svg_width - 2 * self._inset
        self._graph_bottom: float = self._top_text_space + self._graph_height
        self._svg_height: float = self._graph_height + self._top_text_space + self._bottom_text_space
        self._interval_width: float = self._graph_width / self._frame_count
        self._offset: float = self._inset + self._interval_width / 2

        if not (0 <= self._top_text_y_pos <= self._top_text_space):
            raise ValueError("It must hold that 0 <= top_text_y_pos <= top_text_space")

        if not (self._graph_bottom <= self._bottom_text_y_pos <= self._graph_bottom + self._bottom_text_space):
            raise ValueError("bottom_text_y_pos must be below the graph")

        self._dwg: Drawing = Drawing(size=(self._svg_width, self._svg_height), profile='full')
        self._dwg_save: Drawing | None = None
        self._dwg_animated: Drawing | None = None
        self._dwg_still: Drawing | None = None

    async def build(self) -> Self:
        """Build the rain graph by calling all the method in the right order.  Returns self when done"""
        await self.draw_svg_frame()
        self.draw_hour_bars()
        self.draw_chances_path()
        self.draw_data_line()
        self.write_hint()
        await self.insert_background()
        self._dwg_save = copy.deepcopy(self._dwg)

        return self

    async def get_animated(self) -> bytes:
        """Get the animated SVG. If called for the first time since refresh, downloads the images to build the file."""

        _LOGGER.info(f"Get animated with _dwg_animated {self._dwg_animated}")
        if self._dwg_animated is None:
            clouds = self.download_clouds()
            self._dwg = copy.deepcopy(self._dwg_save)
            self.draw_current_fame_line()
            self.draw_description_text()
            await clouds
            self.insert_cloud_layer()
            await self.draw_location()
            self._dwg_animated = self._dwg
        return self.get_svg_string(still_image=False)

    async def get_still(self) -> bytes:
        """Get the animated SVG. If called for the first time since refresh, downloads the images to build the file."""
        _LOGGER.info(f"Get still with _dwg_still {self._dwg_still}")

        if self._dwg_still is None:
            idx = self._animation_data['most_recent_image_idx']
            cloud = self.download_clouds(idx)
            self._dwg = copy.deepcopy(self._dwg_save)
            self.draw_current_fame_line(idx)
            self.draw_description_text(idx)
            await cloud
            self.insert_cloud_layer(idx)
            await self.draw_location()
            self._dwg_still = self._dwg
        return self.get_svg_string(still_image=True)

    async def download_clouds(self, idx = None):
        imgs = [e['image'] for e in self._animation_data['sequence']]

        if idx is not None and type(imgs[idx]) is str:
            _LOGGER.info("Download single cloud image")
            result = await self.download_images_from_api([imgs[idx]])
            self._animation_data['sequence'][idx]['image'] = result[0]

        else:
            _LOGGER.info("Download many cloud images")

            result = await self.download_images_from_api([img for img in imgs if type(img) is str])

            for i in range(len(self._animation_data['sequence'])):
                if type(self._animation_data['sequence'][i]['image']) is str:
                    self._animation_data['sequence'][i]['image'] = result[0]
                    result = result[1:]

    async def download_images_from_api(self, urls: list[str]) -> list[Any]:
        """Download a batch of images to create the radar frames."""
        coroutines = list()

        for url in urls:
            coroutines.append(self._api_client.get_image(url))
        async with async_timeout.timeout(60):
            images_from_api = await asyncio.gather(*coroutines)

        _LOGGER.info(f"Just downloaded {len(images_from_api)} images")
        return images_from_api

    def get_hint(self) -> str:
        return self._animation_data.get('hint', None)

    async def draw_svg_frame(self):
        """Create the global area to draw the other items"""
        mimetype = "application/x-font-ttf"

        content = FONT_TEMPLATE.format(name="Roboto Medium", data=f"data:{mimetype};charset=utf-8;base64,{roboto_b64}")
        self._dwg.embed_stylesheet(content)

        self._dwg.embed_stylesheet("""
            .roboto {
                font-family: "Roboto Medium";
            }
            """)

        fill_color = '#393C40' if self._dark_mode else '#385E95'
        self._dwg.add(self._dwg.rect(insert=(0, 0),
                                     size=(self._svg_width, self._svg_height),
                                     rx=None, ry=None,
                                     fill=fill_color, stroke='none'))

    def draw_description_text(self, idx: int | None = None):
        """For every frame write the amount of precipitation and the time at the top of the graph.
        If idx is set, only do it for the given idx"""

        times = [e['time'].astimezone(tz=self._tz).strftime('%H:%M') for e in
                 self._animation_data['sequence']]
        rain_levels = [f"{e['value']}{self._animation_data['unit']}" for e in self._animation_data['sequence']]

        if idx is not None:
            time = times[idx]
            rain_level = rain_levels[idx]

            paragraph = self._dwg.add(self._dwg.g(class_="roboto", ))

            self.write_time_and_rain(paragraph, rain_level, time)
            return

        for i in range(self._frame_count):
            time = times[i]
            rain_level = rain_levels[i]

            paragraph = self._dwg.add(self._dwg.g(class_="roboto", ))

            values = ['hidden'] * self._frame_count
            values[i] = 'visible'

            paragraph.add(Animate(
                attributeName="visibility",
                values=";".join(values),
                dur=f"{self._frame_count * 0.3}s",
                begin="0s",
                repeatCount="indefinite"
            ))

            self.write_time_and_rain(paragraph, rain_level, time)

    def write_time_and_rain(self, paragraph, rain_level, time):
        """Using the paragraph object, write the time and rain level data"""
        paragraph.add(self._dwg.text(f"{time}", insert=(self._offset, self._top_text_y_pos),
                                     text_anchor="start",
                                     font_size="16px",
                                     fill="white",
                                     stroke='none'))
        paragraph.add(self._dwg.text(f"{rain_level}", insert=(self._svg_width / 2, self._top_text_y_pos),
                                     text_anchor="middle",
                                     font_size="16px",
                                     fill="white",
                                     stroke='none'))

    def write_hint(self):
        """Add the hint text at the bottom of the graph"""
        paragraph = self._dwg.add(self._dwg.g(class_="roboto", ))

        hint = self._animation_data['hint']

        paragraph.add(self._dwg.text(f"{hint}", insert=(self._svg_width / 2, self._bottom_text_y_pos),
                                     text_anchor="middle",
                                     font_size="16px",
                                     fill="white",
                                     stroke='none'))

    def draw_chances_path(self):
        """Draw the prevision margin area around the main forecast line"""
        list_lower_points = []
        list_higher_points = []

        rain_list: List[AnimationFrameData] = self._animation_data['sequence']
        graph_rect_left = self._offset
        graph_rect_top = self._top_text_space

        for i in range(len(rain_list)):
            position_higher = rain_list[i]['position_higher']
            if position_higher is not None:
                list_higher_points.append((graph_rect_left, graph_rect_top + (
                        1.0 - position_higher) * self._graph_height))
            graph_rect_left += self._interval_width

        graph_rect_right = graph_rect_left - self._interval_width
        for i in range(len(rain_list) - 1, -1, -1):
            position_lower = rain_list[i]['position_lower']
            if position_lower is not None:
                list_lower_points.append((graph_rect_right, graph_rect_top + (
                        1.0 - position_lower) * self._graph_height))
                graph_rect_right -= self._interval_width

        if list_higher_points and list_lower_points:
            self.draw_chance_precip(list_higher_points, list_lower_points)

    def draw_chance_precip(self, list_higher_points: List, list_lower_points: List):
        """Draw the blue solid line representing the actual rain forecast"""
        precip_higher_chance_path = self._dwg.path(fill='#63c8fa', stroke='none', opacity=.3)

        list_higher_points[-1] = tuple(list(list_higher_points[-1]) + ['last'])

        self.set_curved_path(precip_higher_chance_path, list_higher_points + list_lower_points)
        self._dwg.add(precip_higher_chance_path)

    @staticmethod
    def set_curved_path(path, points):
        """Pushes points on the path by creating a nice curve between them"""
        if len(points) < 2:
            return

        path.push('M', *points[0])

        for i in range(1, len(points)):
            x_mid = (points[i - 1][0] + points[i][0]) / 2
            y_mid = (points[i - 1][1] + points[i][1]) / 2

            path.push('Q', points[i - 1][0], points[i - 1][1], x_mid, y_mid)
            if points[i][-1] == 'last' or points[i - 1][-1] == 'last':
                path.push('Q', points[i][0], points[i][1], points[i][0], points[i][1])

        path.push('Q', points[-1][0], points[-1][1], points[-1][0], points[-1][1])

    def draw_data_line(self):
        """Draw the main data line for the rain forecast"""
        rain_list: List[AnimationFrameData] = self._animation_data['sequence']
        graph_rect_left = self._offset
        graph_rect_top = self._top_text_space

        entry_list = []

        for i in range(len(rain_list)):
            position = rain_list[i]['position']
            entry_list.append(
                (graph_rect_left,
                 graph_rect_top + (1.0 - position) * self._graph_height))
            graph_rect_left += self._interval_width
        data_line_path = self._dwg.path(fill='none', stroke='#63c8fa', stroke_width=2)
        self.set_curved_path(data_line_path, entry_list)
        self._dwg.add(data_line_path)

    def draw_hour_bars(self):
        """Draw the small bars at the bottom to represent the time"""
        hour_bar_height = 8
        horizontal_inset = self._offset

        for (i, rain_item) in enumerate(self._animation_data['sequence']):
            time_image = rain_item['time'].astimezone(tz=self._tz)
            is_hour_bar = time_image.minute == 0

            x_position = horizontal_inset
            if i == self._animation_data['most_recent_image_idx']:
                self._dwg.add(self._dwg.line(start=(x_position, self._top_text_space),
                                             end=(x_position, self._graph_bottom),
                                             stroke='white',
                                             opacity=0.5,
                                             stroke_dasharray=4))

            self._dwg.add(self._dwg.line(start=(x_position, self._graph_bottom - hour_bar_height),
                                         end=(x_position, self._graph_bottom),
                                         stroke='white' if is_hour_bar else 'lightgrey',
                                         opacity=0.9 if is_hour_bar else 0.7))

            if is_hour_bar:
                graph_rect_center_x = x_position
                graph_rect_center_y = self._graph_bottom + 18

                paragraph = self._dwg.add(self._dwg.g(class_="roboto", ))
                paragraph.add(self._dwg.text(f"{time_image.hour}h", insert=(graph_rect_center_x, graph_rect_center_y),
                                             text_anchor="middle",
                                             font_size="16px",
                                             fill="white",
                                             stroke='none'))

            horizontal_inset += self._interval_width

        self._dwg.add(self._dwg.line(start=(self._offset, self._graph_bottom),
                                     end=(self._graph_width + self._interval_width / 2, self._graph_bottom),
                                     stroke='white'))

    def draw_current_fame_line(self, idx: int | None = None):
        """Draw a solid white line on the timeline at the position of the given frame index"""
        x_position = self._offset if idx is None else self._offset + idx * self._interval_width
        now = self._dwg.add(self._dwg.line(start=(x_position, self._top_text_space),
                                           end=(x_position, self._graph_bottom),
                                           id='now',
                                           stroke='white',
                                           opacity=1,
                                           stroke_width=2))
        if idx is not None:
            return
        now.add(self._dwg.animateTransform("translate", "transform",
                                           id="now",
                                           from_=f"{self._offset} 0",
                                           to=f"{self._graph_width - self._offset} 0",
                                           dur=f"{self._frame_count * 0.3}s",
                                           repeatCount="indefinite"))

    def get_svg_string(self, still_image: bool = False) -> bytes:
        return self._dwg_still.tostring().encode() if still_image else self._dwg_animated.tostring().encode()

    async def insert_background(self):
        bg_image_path = os.path.join(self._config_dir, self._background_image_path)
        async with async_open(bg_image_path, 'rb') as f:
            png_data = base64.b64encode(await f.read()).decode('utf-8')
        image = self._dwg.image("data:image/png;base64," + png_data, insert=(0, 0), size=self._background_size)
        self._dwg.add(image)

    def insert_cloud_layer(self, idx: int | None = None):
        imgs = [e['image'] for e in self._animation_data['sequence']]

        if idx is not None:
            img = imgs[idx]
            png_data = base64.b64encode(img).decode('utf-8')
            image = self._dwg.image("data:image/png;base64," + png_data, insert=(0, 0), size=self._background_size)
            self._dwg.add(image)
            return

        for i, img in enumerate(imgs):
            png_data = base64.b64encode(img).decode('utf-8')
            image = self._dwg.image("data:image/png;base64," + png_data, insert=(0, 0), size=self._background_size)
            self._dwg.add(image)

            values = ['hidden'] * self._frame_count
            values[i] = 'visible'

            image.add(Animate(
                attributeName="visibility",
                values=";".join(values),
                dur=f"{self._frame_count * 0.3}s",
                begin="0s",
                repeatCount="indefinite"
            ))

    async def draw_location(self):
        img = self._animation_data['location']

        _LOGGER.info(f"Draw location layer with img of type {type(img)}")
        if type(img) is str:
            result = await self.download_images_from_api([img])
            img = result[0]
            self._animation_data['location'] = img
        png_data = base64.b64encode(img).decode('utf-8')
        image = self._dwg.image("data:image/png;base64," + png_data, insert=(0, 0), size=self._background_size)
        self._dwg.add(image)

    def get_dwg(self):
        return copy.deepcopy(self._dwg)
