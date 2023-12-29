import json
from datetime import datetime
from io import BytesIO
from unittest.mock import AsyncMock

import pytz
from freezegun import freeze_time
from homeassistant.components.weather import (ATTR_CONDITION_CLOUDY,
                                              ATTR_CONDITION_PARTLYCLOUDY,
                                              ATTR_CONDITION_RAINY, Forecast)
from homeassistant.components.zone import Zone
from homeassistant.core import HomeAssistant
from PIL import Image, ImageDraw, ImageFont
from pytest_homeassistant_custom_component.common import load_fixture, MockConfigEntry

from custom_components.irm_kmi.coordinator import IrmKmiCoordinator
from custom_components.irm_kmi.data import CurrentWeatherData, IrmKmiForecast


def get_api_data(fixture: str) -> dict:
    return json.loads(load_fixture(fixture))


@freeze_time(datetime.fromisoformat('2023-12-26T18:30:00'))
def test_current_weather_be() -> None:
    api_data = get_api_data("forecast.json")
    result = IrmKmiCoordinator.current_weather_from_data(api_data)

    expected = CurrentWeatherData(
        condition=ATTR_CONDITION_CLOUDY,
        temperature=7,
        wind_speed=5,
        wind_gust_speed=None,
        wind_bearing='WSW',
        pressure=1020,
        uv_index=.7
    )

    assert result == expected


@freeze_time(datetime.fromisoformat("2023-12-28T15:30:00"))
def test_current_weather_nl() -> None:
    api_data = get_api_data("forecast_nl.json")
    result = IrmKmiCoordinator.current_weather_from_data(api_data)

    expected = CurrentWeatherData(
        condition=ATTR_CONDITION_CLOUDY,
        temperature=11,
        wind_speed=40,
        wind_gust_speed=None,
        wind_bearing='SW',
        pressure=1008,
        uv_index=1
    )

    assert expected == result


@freeze_time(datetime.fromisoformat('2023-12-26T18:30:00.028724'))
def test_daily_forecast() -> None:
    api_data = get_api_data("forecast.json").get('for', {}).get('daily')
    result = IrmKmiCoordinator.daily_list_to_forecast(api_data)

    assert isinstance(result, list)
    assert len(result) == 8

    expected = IrmKmiForecast(
        datetime='2023-12-27',
        condition=ATTR_CONDITION_PARTLYCLOUDY,
        native_precipitation=0,
        native_temperature=9,
        native_templow=4,
        native_wind_gust_speed=50,
        native_wind_speed=20,
        precipitation_probability=0,
        wind_bearing='S',
        is_daytime=True,
        text_fr='Bar',
        text_nl='Foo'
    )

    assert result[1] == expected


@freeze_time(datetime.fromisoformat('2023-12-26T18:30:00.028724'))
def test_hourly_forecast() -> None:
    api_data = get_api_data("forecast.json").get('for', {}).get('hourly')
    result = IrmKmiCoordinator.hourly_list_to_forecast(api_data)

    assert isinstance(result, list)
    assert len(result) == 49

    expected = Forecast(
        datetime='2023-12-27T02:00:00',
        condition=ATTR_CONDITION_RAINY,
        native_precipitation=.98,
        native_temperature=8,
        native_templow=None,
        native_wind_gust_speed=None,
        native_wind_speed=15,
        precipitation_probability=70,
        wind_bearing='S',
        native_pressure=1020,
        is_daytime=False
    )

    assert result[8] == expected


@freeze_time(datetime.fromisoformat("2023-12-28T15:30:00+01:00"))
async def test_get_image_nl(
        hass: HomeAssistant,
        mock_image_irm_kmi_api: AsyncMock,
        mock_config_entry: MockConfigEntry) -> None:
    api_data = get_api_data("forecast_nl.json")
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = await coordinator._async_animation_data(api_data)

    # Construct the expected image for the most recent one
    tz = pytz.timezone(hass.config.time_zone)
    background = Image.open("custom_components/irm_kmi/resources/nl.png").convert('RGBA')
    layer = Image.open("tests/fixtures/clouds_nl.png").convert('RGBA')
    localisation = Image.open("tests/fixtures/loc_layer_nl.png").convert('RGBA')
    temp = Image.alpha_composite(background, layer)
    expected = Image.alpha_composite(temp, localisation)
    draw = ImageDraw.Draw(expected)
    font = ImageFont.truetype("custom_components/irm_kmi/resources/roboto_medium.ttf", 16)
    time_image = (datetime.fromisoformat("2023-12-28T14:25:00+00:00")
                  .astimezone(tz=tz))
    time_str = time_image.isoformat(sep=' ', timespec='minutes')
    draw.text((4, 4), time_str, (0, 0, 0), font=font)

    result_image = Image.open(BytesIO(result['sequence'][-1]['image'])).convert('RGBA')

    assert list(result_image.getdata()) == list(expected.getdata())

    thumb_image = Image.open(BytesIO(result['most_recent_image'])).convert('RGBA')
    assert list(thumb_image.getdata()) == list(expected.getdata())

    assert result['hint'] == "No rain forecasted shortly"


@freeze_time(datetime.fromisoformat("2023-12-26T18:31:00+01:00"))
async def test_get_image_be(
        hass: HomeAssistant,
        mock_image_irm_kmi_api: AsyncMock,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("forecast.json")
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = await coordinator._async_animation_data(api_data)

    # Construct the expected image for the most recent one
    tz = pytz.timezone(hass.config.time_zone)
    background = Image.open("custom_components/irm_kmi/resources/be_black.png").convert('RGBA')
    layer = Image.open("tests/fixtures/clouds_be.png").convert('RGBA')
    localisation = Image.open("tests/fixtures/loc_layer_be_n.png").convert('RGBA')
    temp = Image.alpha_composite(background, layer)
    expected = Image.alpha_composite(temp, localisation)
    draw = ImageDraw.Draw(expected)
    font = ImageFont.truetype("custom_components/irm_kmi/resources/roboto_medium.ttf", 16)
    time_image = (datetime.fromisoformat("2023-12-26T18:30:00+01:00")
                  .astimezone(tz=tz))
    time_str = time_image.isoformat(sep=' ', timespec='minutes')
    draw.text((4, 4), time_str, (255, 255, 255), font=font)

    result_image = Image.open(BytesIO(result['sequence'][9]['image'])).convert('RGBA')

    assert list(result_image.getdata()) == list(expected.getdata())

    thumb_image = Image.open(BytesIO(result['most_recent_image'])).convert('RGBA')
    assert list(thumb_image.getdata()) == list(expected.getdata())

    assert result['hint'] == "No rain forecasted shortly"
