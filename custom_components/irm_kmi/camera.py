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
        self.content_type = 'image/svg+xml'
        self._name = f"Radar {entry.title}"
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="IRM KMI",
            name=f"Radar {entry.title}"
        )

        self._image_index = False

    @property
    def frame_interval(self) -> float:
        """Return the interval between frames of the mjpeg stream."""
        return 1

    def camera_image(self,
                     width: int | None = None,
                     height: int | None = None) -> bytes | None:
        """Return still image to be used as thumbnail."""
        return self.coordinator.data.get('animation', {}).get('svg_still')

    async def async_camera_image(
            self,
            width: int | None = None,
            height: int | None = None
    ) -> bytes | None:
        """Return still image to be used as thumbnail."""
        return self.camera_image()

    async def handle_async_still_stream(self, request: web.Request, interval: float) -> web.StreamResponse:
        """Generate an HTTP MJPEG stream from camera images."""
        self._image_index = 0
        return await async_get_still_stream(request, self.get_animated_svg, self.content_type, interval)

    async def handle_async_mjpeg_stream(self, request: web.Request) -> web.StreamResponse:
        """Serve an HTTP MJPEG stream from the camera."""
        return await self.handle_async_still_stream(request, self.frame_interval)

    async def get_animated_svg(self) -> bytes | None:
        """Returns the animated svg for camera display"""
        # If this is not done this way, the live view can only be opened once
        self._image_index = not self._image_index
        if self._image_index:
            return self.coordinator.data.get('animation', {}).get('svg_animated')
        else:
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
