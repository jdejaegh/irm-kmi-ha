# IRM KMI Weather integration for Home Assistant

Home Assistant weather provider using data from Belgian IRM KMI. 
The data is collected via their non-public mobile application API.

Although the provider is Belgian, the data is available for Belgium 🇧🇪, Luxembourg 🇱🇺, and The Netherlands 🇳🇱

## Installing via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jdejaegh&repository=irm-kmi-ha&category=integration)

or

1. Go to HACS > Integrations
2. Add this repo into your [HACS custom repositories](https://hacs.xyz/docs/faq/custom_repositories/)
3. Search for IRM KMI and download it
4. Restart Home Assistant

## Set up the integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=irm_kmi)

or

1. Configure the integration via the UI (search for 'IRM KMI')


## Features

This integration provides the following things:

- A weather entity with current weather conditions
- Weather forecasts (hourly, daily and twice-daily) [using the service `weather.get_forecasts`](https://www.home-assistant.io/integrations/weather/#service-weatherget_forecasts)
- Short-term rain forecasts using the radar data using the [custom service `ìrm_kmi.get_forecasts_radar`](#custom-service-irm_kmiget_forecasts_radar)
- A camera entity for rain radar and short-term rain previsions (with different styles)
- A binary sensor for weather warnings
- A sensor with the timestamp for the start of the next warning
- Sensors for active pollens


## Screenshots

<details>
<summary>Show screenshots</summary>
<img src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/sensors.png"/>  <br>
<img src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/forecast.png"/>  <br>
<img src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/camera_light.png"/>  <br>
<img src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/camera_dark.png"/>  <br>
<img src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/camera_sat.png"/>  
</details>

## Limitations

1. The weather provider sometime uses two weather conditions for the same day (see below).  When this is the case, only the first
weather condition is taken into account in this integration.
<br><img src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/monday.png" height="150" alt="Example of two weather conditions">

2. The trends for 14 days are not shown
3. The provider only has data for Belgium, Luxembourg and The Netherlands 

## Mapping between IRM KMI and Home Assistant weather conditions

Mapping was established based on my own interpretation of the icons and conditions.

| HA Condition    | HA Description                    | IRM KMI icon                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | IRM KMI data (`ww-dayNight`)                                                  |
|-----------------|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| clear-night     | Clear night                       | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/0-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/1-n.png" width="64"/>                                                                                                                                                                                                                                                                                                                                                                                                       | `0-n` `1-n`                                                                   |
| cloudy          | Many clouds                       | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/15-d.png" width="64"/>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `14-d` `14-n` `15-d` `15-n`                                                   |
| exceptional     | Exceptional                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                               |
| fog             | Fog                               | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/24-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/24-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/25-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/26-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/26-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/27-d.png" width="64"/> | `24-d` `24-n` `25-d` `25-n` `26-d` `26-n`  `27-d` `27-n`                      |
| hail            | Hail                              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                               |
| lightning       | Lightning/ thunderstorms          |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                               |
| lightning-rainy | Lightning/ thunderstorms and rain | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/2-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/2-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/10-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/10-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/13-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/13-n.png" width="64"/>   | `2-d` `2-n` `5-d` `5-n` `7-d` `7-n` `10-d` `10-n` `13-d` `13-n` `17-d` `17-n` |
| partlycloudy    | A few clouds                      | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/3-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/3-n.png" width="64"/>                                                                                                                                                                                                                                                                                                                                                                                                       | `3-d` `3-n`                                                                   |
| pouring         | Pouring rain                      | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/4-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/4-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/16-d.png" width="64"/>                                                                                                                                                                                                                                                                                                      | `4-d` `4-n` `6-d` `6-n` `16-d` `16-n` `19-d` `19-n`                           |
| rainy           | Rain                              | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/18-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/21-d.png" width="64"/>                                                                                                                                                                                                                                                                                                                                                                                                     | `18-d` `18-n` `21-d` `21-n`                                                   |
| snowy           | Snow                              | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/11-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/11-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/22-d.png" width="64"/>  <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/23-d.png" width="64"/>                                                                                                                                                                                                  | `11-d` `11-n` `12-d` `12-n` `22-d` `22-n` `23-d` `23-n`                       |
| snowy-rainy     | Snow and Rain                     | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/8-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/8-n.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/20-d.png" width="64"/>                                                                                                                                                                                                                                                                                                      | `8-d` `8-n` `9-d` `9-n` `20-d` `20-n`                                         |
| sunny           | Sunshine                          | <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/0-d.png" width="64"/> <img height="64" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/1-d.png" width="64"/>                                                                                                                                                                                                                                                                                                                                                                                                       | `0-d` `1-d`                                                                   |
| windy           | Wind                              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                               |
| windy-variant   | Wind and clouds                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                               |


## Warning details

Warnings are represented with two sensors: 
 - a binary sensor showing if any warning is currently active
 - a timestamp sensor with the start time of the next warning (if any, else `unknown`)

### Binary sensor for ongoing warnings

The warning binary sensor is on if a warning is currently relevant (i.e. warning start time < current time < warning end time). 
Warnings may be issued by the IRM KMI ahead of time but the binary sensor is only on when at least one of the issued warnings is relevant.

The binary sensor has an additional attribute called `warnings`, with a list of warnings for the current location. 
Warnings in the list may be warning issued ahead of time. 

Each element in the list has the following attributes:
 * `slug: str`: warning slug type, can be used for automation and does not change with language setting. Example:  `ice_or_snow`
 * `id: int`: internal id for the warning type used by the IRM KMI api.  
 * `level: int`: warning severity, from 1 (lower risk) to 3 (higher risk)
 * `friendly_name: str`: language specific name for the warning type.  Examples: `Ice or snow`, `Chute de neige ou verglas`, `Sneeuw of ijzel`, `Glätte`
 * `text: str`: language specific additional information about the warning
 * `starts_at: datetime`: time at which the warning starts being relevant
 * `ends_at: datetime`: time at which the warning stops being relevant
 * `is_active: bool`: `true` if `starts_at` < now < `ends_at`

The following table summarizes the different known warning types.  Other warning types may be returned and will have `unknown` as slug.  Feel free to open an issue with the id and the English friendly name to have it added to this integration.

| Warning slug                | Warning id | Friendly name (en, fr, nl, de)                                                           |
|-----------------------------|------------|------------------------------------------------------------------------------------------|
| wind                        | 0          | Wind, Vent, Wind, Wind                                                                   |
| rain                        | 1          | Rain, Pluie, Regen, Regen                                                                |
| ice_or_snow                 | 2          | Ice or snow, Chute de neige ou verglas, Sneeuw of ijzel, Glätte                          |
| thunder                     | 3          | Thunder, Orage, Onweer, Gewitter                                                         |
| fog                         | 7          | Fog, Brouillard, Mist, Nebel                                                             |
| cold                        | 9          | Cold, Froid, Koude, Kalt                                                                 |
| thunder_wind_rain           | 12         | Thunder Wind Rain, Orage, rafales et averses, Onweer Wind Regen, Gewitter Windböen Regen |
| thunderstorm_strong_gusts   | 13         | Thunderstorm & strong gusts, Orage et rafales, Onweer en wind, Gewitter und Windböen     |
| thunderstorm_large_rainfall | 14         | Thunderstorm & large rainfall, Orage et averses, Onweer en regen, Gewitter und Regen     |
| storm_surge                 | 15         | Storm surge, Marée forte, Stormtij, Sturmflut                                            |
| coldspell                   | 17         | Coldspell, Vague de froid, Koude, Koude                                                  |

The sensor has an attribute called `active_warnings_friendly_names`, holding a comma separated list of the friendly names
of the currently active warnings (e.g. `Fog, Ice or snow`).  There is no particular order for the list.

### Timestamp sensor for upcoming warnings

The state is the start time of the earliest next warning, if any; else `unknown`.

The sensor has two additional attributes:
 - `next_warnings`: a list of all the upcoming warnings, with the same data as the `warnings` attribute of the binary sensor (see above)
 - `next_warning_friendly_names` holding a comma separated list of the friendly names of the currently active warnings (e.g. `Fog, Ice or snow`).  There is no particular order for the list.


## Pollen details

One sensor per pollen is created and each sensor can have one of the following values: green, yellow, orange, 
red, purple or none.

The exact meaning of each color can be found on the IRM KMI webpage: [Pollen allergy and hay fever](https://www.meteo.be/en/weather/forecasts/pollen-allergy-and-hay-fever)

<img height="200" src="https://github.com/jdejaegh/irm-kmi-ha/raw/main/img/pollens.png" alt="Pollen data"/>

This data sent to the app would result in grasses have the 'purple' state. 
All the other pollens would be 'none'.

Due to a recent update in the pollen SVG format, there may have some edge cases that are not handled by the integration.

## Custom service `irm_kmi.get_forecasts_radar`

The service returns a list of Forecast objects (similar to `weather.get_forecasts`) but only data about precipitation is available. 
The data is taken from the radar forecast: it is useful for very short-term rain forecast.

The service can optionally include data from the past (like shown on the radar).

Here is an example of service call:

```yaml
service: irm_kmi.get_forecasts_radar
target:
  entity_id: weather.home
data:
  include_past_forecasts: true 
```

The data is optional and defaults to `false`. 

Even when `include_past_forecasts` is `false`, the current 10 minutes interval is returned so the first item in the 
response is in the past (at most 10 minutes in the past).  This can be useful to determine if rain is currently falling 
and how strong it is.

## Disclaimer

This is a personal project and isn't in any way affiliated with, sponsored or endorsed by [The Royal Meteorological 
Institute of Belgium](https://www.meteo.be).

All product names, trademarks and registered trademarks in (the images in) this repository, are property of their 
respective owners. All images in this repository are used by the project for identification purposes only.