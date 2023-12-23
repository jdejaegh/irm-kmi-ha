# IRM KMI Weather integration for Home Assistant

Home Assistant weather provider using data from Belgian IRM KMI. 
The data is collected via their non-public mobile application API.

Although the provider is Belgian, the data is available for Belgium 🇧🇪, Luxembourg 🇱🇺, and The Netherlands 🇳🇱

## Installing via HACS

1. Go to HACS > Integrations
2. Add this repo into your HACS custom repositories
3. Search for IRM KMI and download it
4. Configure the integration via `configuration.yaml`:
    ```yaml
    weather:
      - platform: irm_kmi
        name: "Namur"
        lat: 50.4645871
        lon: 4.8508549
    ```
5. Restart Home Assistant


## Roadmap

- [X] Basic weather provider capability (current weather only)
- [ ] Forecasts
  - [ ] Hourly
  - [ ] Daily
- [ ] Camera entity for the satellite view
- [ ] Use UI to configure the integration

## Mapping between IRM KMI and Home Assistant weather conditions

Mapping was established based on my own interpretation of the icons and conditions.

| HA Condition    | HA Description                    | IRM KMI icon                                                                                                                                                                                                                                                                                        | IRM KMI data (`ww-dayNight`)                                                  |
|-----------------|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| clear-night     | Clear night                       | <img height="64" src="img/0-n.png" width="64"/>                                                                                                                                                                                                                                                     | `0-n`                                                                         |
| cloudy          | Many clouds                       | <img height="64" src="img/3-d.png" width="64"/> <img height="64" src="img/3-n.png" width="64"/> <img height="64" src="img/15-d.png" width="64"/>                                                                                                                                                    | `3-d` `3-n` `14-d` `14-n` `15-d` `15-n`                                       |
| exceptional     | Exceptional                       | <img height="64" src="img/21-d.png" width="64"/> <img height="64" src="img/27-d.png" width="64"/>                                                                                                                                                                                                   | `21-d` `21-n` `27-d` `27-n`                                                   |
| fog             | Fog                               | <img height="64" src="img/24-d.png" width="64"/> <img height="64" src="img/24-n.png" width="64"/> <img height="64" src="img/25-d.png" width="64"/> <img height="64" src="img/26-d.png" width="64"/> <img height="64" src="img/26-n.png" width="64"/>                                                | `24-d` `24-n` `25-d` `25-n` `26-d` `26-n`                                     |
| hail            | Hail                              |                                                                                                                                                                                                                                                                                                     |                                                                               |
| lightning       | Lightning/ thunderstorms          |                                                                                                                                                                                                                                                                                                     |                                                                               |
| lightning-rainy | Lightning/ thunderstorms and rain | <img height="64" src="img/2-d.png" width="64"/> <img height="64" src="img/2-n.png" width="64"/> <img height="64" src="img/10-d.png" width="64"/> <img height="64" src="img/10-n.png" width="64"/> <img height="64" src="img/13-d.png" width="64"/> <img height="64" src="img/13-n.png" width="64"/> | `2-d` `2-n` `5-d` `5-n` `7-d` `7-n` `10-d` `10-n` `13-d` `13-n` `17-d` `17-n` |
| partlycloudy    | A few clouds                      | <img height="64" src="img/1-d.png" width="64"/> <img height="64" src="img/1-n.png" width="64"/>                                                                                                                                                                                                     | `1-d` `1-n`                                                                   |
| pouring         | Pouring rain                      | <img height="64" src="img/4-d.png" width="64"/> <img height="64" src="img/4-n.png" width="64"/> <img height="64" src="img/16-d.png" width="64"/>                                                                                                                                                    | `4-d` `4-n` `6-d` `6-n` `16-d` `16-n` `19-d` `19-n`                           |
| rainy           | Rain                              | <img height="64" src="img/18-d.png" width="64"/>                                                                                                                                                                                                                                                    | `18-d` `18-n`                                                                 |
| snowy           | Snow                              | <img height="64" src="img/11-d.png" width="64"/> <img height="64" src="img/11-n.png" width="64"/> <img height="64" src="img/22-d.png" width="64"/>  <img height="64" src="img/23-d.png" width="64"/>                                                                                                | `11-d` `11-n` `12-d` `12-n` `22-d` `22-n` `23-d` `23-n`                       |
| snowy-rainy     | Snow and Rain                     | <img height="64" src="img/8-d.png" width="64"/> <img height="64" src="img/8-n.png" width="64"/> <img height="64" src="img/20-d.png" width="64"/>                                                                                                                                                    | `8-d` `8-n` `9-d` `9-n` `20-d` `20-n`                                         |
| sunny           | Sunshine                          | <img height="64" src="img/0-d.png" width="64"/>                                                                                                                                                                                                                                                     | `0-d`                                                                         |
| windy           | Wind                              |                                                                                                                                                                                                                                                                                                     |                                                                               |
| windy-variant   | Wind and clouds                   |                                                                                                                                                                                                                                                                                                     |                                                                               |