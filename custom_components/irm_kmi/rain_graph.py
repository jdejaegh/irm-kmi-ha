"""Create graphs for rain short term forecast."""

import base64
from typing import List

import pytz
from svgwrite import Drawing
from svgwrite.animate import Animate

from custom_components.irm_kmi.data import (AnimationFrameData,
                                            RadarAnimationData)


class RainGraph:
    def __init__(self,
                 animation_data: RadarAnimationData,
                 background_image_path: str,
                 background_size: (int, int),
                 dark_mode: bool = False,
                 tz: str = 'UTC',
                 svg_width: float = 640,
                 inset: float = 20,
                 graph_height: float = 150,
                 top_text_space: float = 30,
                 top_text_y_pos: float = 20,
                 bottom_text_space: float = 45,
                 bottom_text_y_pos: float = 215
                 ):

        self._animation_data: RadarAnimationData = animation_data
        self._background_image_path: str = background_image_path
        self._background_size: (int, int) = background_size
        self._dark_mode: bool = dark_mode
        self._tz = pytz.timezone(tz)
        self._svg_width: float = svg_width
        self._inset: float = inset
        self._graph_height: float = graph_height
        self._top_text_space: float = top_text_space + background_size[1]
        self._top_text_y_pos: float = top_text_y_pos + background_size[1]
        self._bottom_text_space: float = bottom_text_space
        self._bottom_text_y_pos: float = bottom_text_y_pos + background_size[1]

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

        self.draw_svg_graph()
        self.draw_current_fame_line()

        self.draw_description_text()
        self.insert_background()
        self.insert_cloud_layer()
        self.draw_location()

    def draw_svg_graph(self):
        """Create the global area to draw the other items"""
        self._dwg.embed_font(name="Roboto Medium", filename='custom_components/irm_kmi/resources/roboto_medium.ttf')
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

        self.draw_hour_bars()
        self.draw_chances_path()
        self.draw_data_line()
        self.write_hint()

    def draw_description_text(self):
        """For the given frame idx, write the amount of precipitation and the time at the top of the graph"""

        times = [e['time'].astimezone(tz=self._tz).isoformat(sep=' ', timespec='minutes') for e in
                 self._animation_data['sequence']]
        rain_levels = [f"{e['value']}{self._animation_data['unit']}" for e in self._animation_data['sequence']]

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

            paragraph.add(self._dwg.text(f"{time}", insert=(self._offset, self._top_text_y_pos),
                                         text_anchor="start",
                                         font_size="14px",
                                         fill="white",
                                         stroke='none'))

            paragraph.add(self._dwg.text(f"{rain_level}", insert=(self._svg_width / 2, self._top_text_y_pos),
                                         text_anchor="middle",
                                         font_size="14px",
                                         fill="white",
                                         stroke='none'))

    def write_hint(self):
        """Add the hint text at the bottom of the graph"""
        paragraph = self._dwg.add(self._dwg.g(class_="roboto", ))

        hint = self._animation_data['hint']

        paragraph.add(self._dwg.text(f"{hint}", insert=(self._svg_width / 2, self._bottom_text_y_pos),
                                     text_anchor="middle",
                                     font_size="14px",
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
                graph_rect_center_y = self._graph_bottom + 15

                paragraph = self._dwg.add(self._dwg.g(class_="roboto", ))
                paragraph.add(self._dwg.text(f"{time_image.hour}h", insert=(graph_rect_center_x, graph_rect_center_y),
                                             text_anchor="middle",
                                             font_size="14px",
                                             fill="white",
                                             stroke='none'))

            horizontal_inset += self._interval_width

        self._dwg.add(self._dwg.line(start=(self._offset, self._graph_bottom),
                                     end=(self._graph_width + self._interval_width / 2, self._graph_bottom),
                                     stroke='white'))

    def draw_current_fame_line(self):
        """Draw a solid white line on the timeline at the position of the given frame index"""
        x_position = self._offset
        now = self._dwg.add(self._dwg.line(start=(x_position, self._top_text_space),
                                           end=(x_position, self._graph_bottom),
                                           id='now',
                                           stroke='white',
                                           opacity=1,
                                           stroke_width=2))
        now.add(self._dwg.animateTransform("translate", "transform",
                                           id="now",
                                           from_=f"{self._offset} 0",
                                           to=f"{self._graph_width - self._offset} 0",
                                           dur=f"{self._frame_count * 0.3}s",
                                           repeatCount="indefinite"))

    def get_svg_string(self):
        return self._dwg.tostring()

    def insert_background(self):
        with open(self._background_image_path, 'rb') as f:
            png_data = base64.b64encode(f.read()).decode('utf-8')
        image = self._dwg.image("data:image/png;base64," + png_data, insert=(0, 0), size=self._background_size)
        self._dwg.add(image)

    def insert_cloud_layer(self):
        imgs = [e['image'] for e in self._animation_data['sequence']]

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

    def draw_location(self):
        img = self._animation_data['location']
        png_data = base64.b64encode(img).decode('utf-8')
        image = self._dwg.image("data:image/png;base64," + png_data, insert=(0, 0), size=self._background_size)
        self._dwg.add(image)
