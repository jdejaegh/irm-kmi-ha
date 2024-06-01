import base64
from datetime import datetime, timedelta

from custom_components.irm_kmi.data import (AnimationFrameData,
                                            RadarAnimationData)
from custom_components.irm_kmi.rain_graph import RainGraph


def get_radar_animation_data() -> RadarAnimationData:
    with open("tests/fixtures/clouds_be.png", "rb") as file:
        image_data = file.read()
    with open("tests/fixtures/loc_layer_be_n.png", "rb") as file:
        location = file.read()

    sequence = [
        AnimationFrameData(
            time=datetime.fromisoformat("2023-12-26T18:30:00+00:00") + timedelta(minutes=10 * i),
            image=image_data,
            value=2,
            position=.5,
            position_lower=.4,
            position_higher=.6
        )
        for i in range(10)
    ]

    return RadarAnimationData(
        sequence=sequence,
        most_recent_image_idx=2,
        hint="Testing SVG camera",
        unit="mm/10min",
        location=location
    )


async def test_svg_frame_setup():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    await rain_graph.draw_svg_frame()

    svg_str = rain_graph.get_dwg().tostring()

    with open("custom_components/irm_kmi/resources/roboto_medium.ttf", "rb") as file:
        font_b64 = base64.b64encode(file.read()).decode('utf-8')

    assert '#385E95' in svg_str
    assert 'font-family: "Roboto Medium";' in svg_str
    assert font_b64 in svg_str


def test_svg_hint():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.write_hint()

    svg_str = rain_graph.get_dwg().tostring()

    assert "Testing SVG camera" in svg_str


def test_svg_time_bars():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.draw_hour_bars()

    svg_str = rain_graph.get_dwg().tostring()

    assert "19h" in svg_str
    assert "20h" in svg_str

    assert "<line" in svg_str
    assert 'stroke="white"' in svg_str


def test_draw_chances_path():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.draw_chances_path()

    svg_str = rain_graph.get_dwg().tostring()

    assert 'fill="#63c8fa"' in svg_str
    assert 'opacity="0.3"' in svg_str
    assert 'stroke="none"' in svg_str
    assert '<path ' in svg_str


def test_draw_data_line():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.draw_data_line()

    svg_str = rain_graph.get_dwg().tostring()

    assert 'fill="none"' in svg_str
    assert 'stroke-width="2"' in svg_str
    assert 'stroke="#63c8fa"' in svg_str
    assert '<path ' in svg_str


async def test_insert_background():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    await rain_graph.insert_background()

    with open("custom_components/irm_kmi/resources/be_white.png", "rb") as file:
        png_b64 = base64.b64encode(file.read()).decode('utf-8')

    svg_str = rain_graph.get_dwg().tostring()

    assert png_b64 in svg_str
    assert "<image " in svg_str
    assert 'height="490"' in svg_str
    assert 'width="640"' in svg_str
    assert 'x="0"' in svg_str
    assert 'y="0"' in svg_str


def test_draw_current_frame_line_moving():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.draw_current_fame_line()

    str_svg = rain_graph.get_dwg().tostring()

    assert '<line' in str_svg
    assert 'id="now"' in str_svg
    assert 'opacity="1"' in str_svg
    assert 'stroke="white"' in str_svg
    assert 'stroke-width="2"' in str_svg
    assert 'x1="50' in str_svg
    assert 'x2="50' in str_svg
    assert 'y1="520' in str_svg
    assert 'y2="670' in str_svg

    assert 'animateTransform' in str_svg
    assert 'attributeName="transform"' in str_svg
    assert 'repeatCount="indefinite"' in str_svg
    assert 'type="translate"' in str_svg


def test_draw_current_frame_line_index():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.draw_current_fame_line(0)

    str_svg = rain_graph.get_dwg().tostring()

    assert '<line' in str_svg
    assert 'id="now"' in str_svg
    assert 'opacity="1"' in str_svg
    assert 'stroke="white"' in str_svg
    assert 'stroke-width="2"' in str_svg
    assert 'x1="50' in str_svg
    assert 'x2="50' in str_svg
    assert 'y1="520' in str_svg
    assert 'y2="670' in str_svg

    assert 'animateTransform' not in str_svg
    assert 'attributeName="transform"' not in str_svg
    assert 'repeatCount="indefinite"' not in str_svg
    assert 'type="translate"' not in str_svg


def test_draw_description_text():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.draw_description_text()

    str_svg = rain_graph.get_dwg().tostring()

    assert "18:30" in str_svg
    assert "18:40" in str_svg
    assert "18:50" in str_svg
    assert "19:00" in str_svg
    assert "19:10" in str_svg
    assert "19:20" in str_svg
    assert "19:30" in str_svg
    assert "19:40" in str_svg
    assert "19:50" in str_svg
    assert "20:00" in str_svg

    assert str_svg.count("2mm/10") == 10
    assert 'class="roboto"' in str_svg


def test_draw_cloud_layer():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.insert_cloud_layer()

    str_svg = rain_graph.get_dwg().tostring()

    with open("tests/fixtures/clouds_be.png", "rb") as file:
        png_b64 = base64.b64encode(file.read()).decode('utf-8')

    assert str_svg.count(png_b64) == 10
    assert str_svg.count('height="490"') == 10
    assert str_svg.count('width="640"') == 11  # Is also the width of the SVG itself


def test_draw_location_layer():
    data = get_radar_animation_data()
    rain_graph = RainGraph(
        animation_data=data,
        background_image_path="custom_components/irm_kmi/resources/be_white.png",
        background_size=(640, 490),
    )

    rain_graph.draw_location()

    str_svg = rain_graph.get_dwg().tostring()

    with open("tests/fixtures/loc_layer_be_n.png", "rb") as file:
        png_b64 = base64.b64encode(file.read()).decode('utf-8')

    assert png_b64 in str_svg
