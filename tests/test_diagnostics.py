"""Tests for diagnostics module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adjustable_bed.const import (
    BED_TYPE_LINAK,
    CONF_BED_TYPE,
    CONF_DISABLE_ANGLE_SENSING,
    CONF_HAS_MASSAGE,
    CONF_MOTOR_COUNT,
    CONF_PREFERRED_ADAPTER,
    CONF_PROTOCOL_VARIANT,
    DOMAIN,
)
from custom_components.adjustable_bed.diagnostics import (
    TO_REDACT,
    async_get_config_entry_diagnostics,
)


@pytest.fixture
def mock_diagnostics_config_entry_data() -> dict:
    """Return mock config entry data for diagnostics test."""
    return {
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_NAME: "Test Bed",
        CONF_BED_TYPE: BED_TYPE_LINAK,
        CONF_MOTOR_COUNT: 2,
        CONF_HAS_MASSAGE: False,
        CONF_DISABLE_ANGLE_SENSING: True,
        CONF_PREFERRED_ADAPTER: "auto",
    }


@pytest.fixture
def mock_diagnostics_config_entry(
    hass: HomeAssistant, mock_diagnostics_config_entry_data: dict
) -> MockConfigEntry:
    """Return a mock config entry for diagnostics test."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Bed",
        data=mock_diagnostics_config_entry_data,
        unique_id="AA:BB:CC:DD:EE:FF",
        entry_id="diagnostics_test_entry",
    )
    entry.add_to_hass(hass)
    return entry


class TestDiagnosticsRedaction:
    """Test diagnostics data redaction."""

    def test_redact_keys(self):
        """Test that sensitive keys are in redaction list."""
        assert CONF_ADDRESS in TO_REDACT
        assert CONF_NAME in TO_REDACT
        assert "address" in TO_REDACT


class TestDiagnosticsOutput:
    """Test diagnostics output structure."""

    async def test_diagnostics_not_connected(
        self,
        hass: HomeAssistant,
        mock_diagnostics_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test diagnostics when not connected."""
        from custom_components.adjustable_bed.coordinator import AdjustableBedCoordinator

        # Set up the coordinator and add to hass data
        coordinator = AdjustableBedCoordinator(hass, mock_diagnostics_config_entry)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_diagnostics_config_entry.entry_id] = coordinator

        # Mock disconnected state
        mock_bleak_client.is_connected = False

        result = await async_get_config_entry_diagnostics(hass, mock_diagnostics_config_entry)

        # Check structure
        assert "entry" in result
        assert "config" in result
        assert "coordinator" in result
        assert "ble" in result
        assert "controller" in result
        assert "position_data" in result
        assert "supported_bed_types" in result

    async def test_diagnostics_connected(
        self,
        hass: HomeAssistant,
        mock_diagnostics_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test diagnostics when connected."""
        from custom_components.adjustable_bed.coordinator import AdjustableBedCoordinator

        # Set up the coordinator
        coordinator = AdjustableBedCoordinator(hass, mock_diagnostics_config_entry)
        await coordinator.async_connect()

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_diagnostics_config_entry.entry_id] = coordinator

        result = await async_get_config_entry_diagnostics(hass, mock_diagnostics_config_entry)

        # Check entry data
        assert result["entry"]["entry_id"] == "diagnostics_test_entry"
        assert result["entry"]["title"] == "Test Bed"

        # Check config
        assert result["config"]["bed_type"] == BED_TYPE_LINAK
        assert result["config"]["motor_count"] == 2
        assert result["config"]["has_massage"] is False
        assert result["config"]["disable_angle_sensing"] is True

        # Check coordinator
        assert "is_connected" in result["coordinator"]
        assert "is_connecting" in result["coordinator"]

        # Check BLE info
        assert "connected" in result["ble"]

        # Check controller info
        assert "initialized" in result["controller"]

    async def test_diagnostics_redacts_sensitive_data(
        self,
        hass: HomeAssistant,
        mock_diagnostics_config_entry,
        mock_coordinator_connected,
    ):
        """Test that sensitive data is redacted."""
        from custom_components.adjustable_bed.coordinator import AdjustableBedCoordinator

        coordinator = AdjustableBedCoordinator(hass, mock_diagnostics_config_entry)
        await coordinator.async_connect()

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_diagnostics_config_entry.entry_id] = coordinator

        result = await async_get_config_entry_diagnostics(hass, mock_diagnostics_config_entry)

        # The address should be redacted in entry.data
        entry_data = result["entry"]["data"]
        assert entry_data.get(CONF_ADDRESS) == "**REDACTED**"
        assert entry_data.get(CONF_NAME) == "**REDACTED**"

    async def test_diagnostics_controller_info(
        self,
        hass: HomeAssistant,
        mock_diagnostics_config_entry,
        mock_coordinator_connected,
    ):
        """Test diagnostics includes controller info when connected."""
        from custom_components.adjustable_bed.coordinator import AdjustableBedCoordinator

        coordinator = AdjustableBedCoordinator(hass, mock_diagnostics_config_entry)
        await coordinator.async_connect()

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_diagnostics_config_entry.entry_id] = coordinator

        result = await async_get_config_entry_diagnostics(hass, mock_diagnostics_config_entry)

        controller_info = result["controller"]
        assert controller_info["initialized"] is True
        assert "class" in controller_info
        assert controller_info["class"] == "LinakController"
        assert "characteristic_uuid" in controller_info

    async def test_diagnostics_supported_bed_types(
        self,
        hass: HomeAssistant,
        mock_diagnostics_config_entry,
        mock_coordinator_connected,
    ):
        """Test diagnostics includes supported bed types."""
        from custom_components.adjustable_bed.coordinator import AdjustableBedCoordinator

        coordinator = AdjustableBedCoordinator(hass, mock_diagnostics_config_entry)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_diagnostics_config_entry.entry_id] = coordinator

        result = await async_get_config_entry_diagnostics(hass, mock_diagnostics_config_entry)

        assert len(result["supported_bed_types"]) > 0
        assert "linak" in result["supported_bed_types"]
