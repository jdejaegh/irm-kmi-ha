"""Create a radar view for IRM KMI weather"""

import logging

from aiohttp import web
from homeassistant.components.camera import Camera, async_get_still_stream
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IrmKmiCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the camera entry."""

    _LOGGER.debug(f'async_setup_entry entry is: {entry}')
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiRadar(coordinator, entry)])


class IrmKmiRadar(CoordinatorEntity, Camera):
    """Representation of a radar view camera."""

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry,
                 ) -> None:
        """Initialize IrmKmiRadar component."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self._name = f"Radar {entry.title}"
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="IRM KMI",
            name=f"Radar {entry.title}"
        )

        self._image_index = 0

    @property
    def frame_interval(self) -> float:
        """Return the interval between frames of the mjpeg stream."""
        return 0.3

    def camera_image(self,
                     width: int | None = None,
                     height: int | None = None) -> bytes | None:
        """Return still image to be used as thumbnail."""
        return self.coordinator.data.get('animation', {}).get('most_recent_image')

    async def async_camera_image(
            self,
            width: int | None = None,
            height: int | None = None
    ) -> bytes | None:
        """Return still image to be used as thumbnail."""
        return self.camera_image()

    async def handle_async_still_stream(self, request: web.Request, interval: float) -> web.StreamResponse:
        """Generate an HTTP MJPEG stream from camera images."""
        _LOGGER.info("handle_async_still_stream")
        self._image_index = 0
        return await async_get_still_stream(request, self.iterate, self.content_type, interval)

    async def handle_async_mjpeg_stream(self, request: web.Request) -> web.StreamResponse:
        """Serve an HTTP MJPEG stream from the camera."""
        _LOGGER.info("handle_async_mjpeg_stream")
        return await self.handle_async_still_stream(request, self.frame_interval)

    async def iterate(self) -> bytes | None:
        """Loop over all the frames when called multiple times."""
        sequence = self.coordinator.data.get('animation', {}).get('sequence')
        if isinstance(sequence, list) and len(sequence) > 0:
            r = sequence[self._image_index].get('image', None)
            self._image_index = (self._image_index + 1) % len(sequence)
            return r
        return None

    @property
    def name(self) -> str:
        """Return the name of this camera."""
        return self._name

    @property
    def extra_state_attributes(self) -> dict:
        """Return the camera state attributes."""
        attrs = {"hint": self.coordinator.data.get('animation', {}).get('hint')}
        return attrs

