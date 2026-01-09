"""Diagnostics support for Smart Bed integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BED_TYPE,
    CONF_DISABLE_ANGLE_SENSING,
    CONF_HAS_MASSAGE,
    CONF_MOTOR_COUNT,
    CONF_PREFERRED_ADAPTER,
    DOMAIN,
)
from .coordinator import SmartBedCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: SmartBedCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get connection status
    is_connected = (
        coordinator._client is not None and coordinator._client.is_connected
    )

    return {
        "config": {
            "address": entry.data.get(CONF_ADDRESS),
            "bed_type": entry.data.get(CONF_BED_TYPE),
            "motor_count": entry.data.get(CONF_MOTOR_COUNT),
            "has_massage": entry.data.get(CONF_HAS_MASSAGE),
            "disable_angle_sensing": entry.data.get(CONF_DISABLE_ANGLE_SENSING),
            "preferred_adapter": entry.data.get(CONF_PREFERRED_ADAPTER),
        },
        "connection": {
            "connected": is_connected,
            "controller_type": (
                type(coordinator.controller).__name__
                if coordinator.controller
                else None
            ),
        },
        "position_data": coordinator.position_data,
    }
