"""Switch entities for Smart Bed integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SmartBedCoordinator
from .entity import SmartBedEntity

if TYPE_CHECKING:
    from .beds.base import BedController

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SmartBedSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Smart Bed switch entity."""

    turn_on_fn: Callable[[BedController], Coroutine[Any, Any, None]]
    turn_off_fn: Callable[[BedController], Coroutine[Any, Any, None]]


SWITCH_DESCRIPTIONS: tuple[SmartBedSwitchEntityDescription, ...] = (
    SmartBedSwitchEntityDescription(
        key="under_bed_lights",
        translation_key="under_bed_lights",
        icon="mdi:lightbulb",
        turn_on_fn=lambda ctrl: ctrl.lights_on(),
        turn_off_fn=lambda ctrl: ctrl.lights_off(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Bed switch entities."""
    coordinator: SmartBedCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SmartBedSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
    ]

    async_add_entities(entities)


class SmartBedSwitch(SmartBedEntity, SwitchEntity):
    """Switch entity for Smart Bed."""

    entity_description: SmartBedSwitchEntityDescription

    def __init__(
        self,
        coordinator: SmartBedCoordinator,
        description: SmartBedSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_is_on = False  # We don't have state feedback

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        _LOGGER.info(
            "Switch turn on: %s (device: %s)",
            self.entity_description.key,
            self._coordinator.name,
        )

        try:
            _LOGGER.debug("Sending turn on command for %s", self.entity_description.key)
            await self._coordinator.async_execute_controller_command(
                self.entity_description.turn_on_fn
            )
            self._attr_is_on = True
            self.async_write_ha_state()
            _LOGGER.debug("Switch %s turned on successfully", self.entity_description.key)
        except NotImplementedError:
            _LOGGER.warning(
                "This bed does not support %s feature",
                self.entity_description.key,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to turn on switch %s: %s",
                self.entity_description.key,
                err,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        _LOGGER.info(
            "Switch turn off: %s (device: %s)",
            self.entity_description.key,
            self._coordinator.name,
        )

        try:
            _LOGGER.debug("Sending turn off command for %s", self.entity_description.key)
            await self._coordinator.async_execute_controller_command(
                self.entity_description.turn_off_fn
            )
            self._attr_is_on = False
            self.async_write_ha_state()
            _LOGGER.debug("Switch %s turned off successfully", self.entity_description.key)
        except NotImplementedError:
            _LOGGER.warning(
                "This bed does not support %s feature",
                self.entity_description.key,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off switch %s: %s",
                self.entity_description.key,
                err,
            )

