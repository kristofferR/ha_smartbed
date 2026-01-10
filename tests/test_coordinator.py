"""Tests for Adjustable Bed coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bleak.exc import BleakError
from homeassistant.core import HomeAssistant

from custom_components.adjustable_bed.const import (
    BED_MOTOR_PULSE_DEFAULTS,
    BED_TYPE_KEESON,
    BED_TYPE_LINAK,
    BED_TYPE_RICHMAT,
    CONF_BED_TYPE,
    CONF_MOTOR_COUNT,
    CONF_MOTOR_PULSE_COUNT,
    CONF_MOTOR_PULSE_DELAY_MS,
    DEFAULT_MOTOR_PULSE_COUNT,
    DEFAULT_MOTOR_PULSE_DELAY_MS,
    DOMAIN,
)
from custom_components.adjustable_bed.coordinator import AdjustableBedCoordinator

from .conftest import TEST_ADDRESS, TEST_NAME


class TestCoordinatorInit:
    """Test coordinator initialization."""

    async def test_coordinator_properties(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test coordinator properties are set correctly."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)

        assert coordinator.address == TEST_ADDRESS
        assert coordinator.name == TEST_NAME
        assert coordinator.bed_type == BED_TYPE_LINAK
        assert coordinator.motor_count == 2
        assert coordinator.has_massage is False
        assert coordinator.disable_angle_sensing is True
        assert coordinator.controller is None
        assert coordinator.position_data == {}

    async def test_device_info(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test device info is generated correctly."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        device_info = coordinator.device_info

        assert device_info["identifiers"] == {("adjustable_bed", TEST_ADDRESS)}
        assert device_info["name"] == TEST_NAME
        assert device_info["manufacturer"] == "Linak"
        assert "2 motors" in device_info["model"]


class TestCoordinatorConnection:
    """Test coordinator connection handling."""

    async def test_connect_success(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test successful connection."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        result = await coordinator.async_connect()

        assert result is True
        assert coordinator.controller is not None

    async def test_connect_device_not_found(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_bluetooth_adapters,
    ):
        """Test connection fails when device not found."""
        with patch(
            "custom_components.adjustable_bed.coordinator.bluetooth.async_ble_device_from_address",
            return_value=None,
        ):
            coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
            result = await coordinator.async_connect()

        assert result is False
        assert coordinator.controller is None

    async def test_connect_bleak_error(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_async_ble_device_from_address,
        mock_bluetooth_adapters,
    ):
        """Test connection handles BleakError."""
        with patch(
            "custom_components.adjustable_bed.coordinator.establish_connection",
            new_callable=AsyncMock,
            side_effect=BleakError("Connection failed"),
        ):
            coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
            result = await coordinator.async_connect()

        assert result is False

    async def test_disconnect(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test disconnection."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        await coordinator.async_connect()

        await coordinator.async_disconnect()

        mock_bleak_client.disconnect.assert_called_once()

    async def test_ensure_connected_when_connected(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test ensure_connected returns True when already connected."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        await coordinator.async_connect()

        result = await coordinator.async_ensure_connected()

        assert result is True

    async def test_ensure_connected_reconnects(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test ensure_connected reconnects when disconnected."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)

        # First call will connect
        result = await coordinator.async_ensure_connected()

        assert result is True


class TestCoordinatorPositionCallbacks:
    """Test coordinator position callback handling."""

    async def test_register_position_callback(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test registering position callbacks."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        callback = MagicMock()

        unregister = coordinator.register_position_callback(callback)

        assert callback in coordinator._position_callbacks
        assert callable(unregister)

    async def test_unregister_position_callback(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test unregistering position callbacks."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        callback = MagicMock()

        unregister = coordinator.register_position_callback(callback)
        unregister()

        assert callback not in coordinator._position_callbacks

    async def test_position_update_triggers_callbacks(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test position updates trigger all callbacks."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        callback1 = MagicMock()
        callback2 = MagicMock()

        coordinator.register_position_callback(callback1)
        coordinator.register_position_callback(callback2)

        # Simulate position update
        coordinator._handle_position_update("back", 45.0)

        assert coordinator.position_data["back"] == 45.0
        callback1.assert_called_once_with({"back": 45.0})
        callback2.assert_called_once_with({"back": 45.0})


class TestCoordinatorDisconnectTimer:
    """Test coordinator idle disconnect timer."""

    async def test_disconnect_timer_set_on_connect(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
    ):
        """Test disconnect timer is set after connection."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        await coordinator.async_connect()

        assert coordinator._disconnect_timer is not None

    async def test_disconnect_timer_cancelled_on_disconnect(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test disconnect timer is cancelled on disconnect."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        await coordinator.async_connect()
        await coordinator.async_disconnect()

        assert coordinator._disconnect_timer is None


class TestCoordinatorWriteCommand:
    """Test coordinator command writing."""

    async def test_write_command_success(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test writing commands succeeds."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        await coordinator.async_connect()

        command = bytes([0x01, 0x00])
        await coordinator.async_write_command(command)

        # The controller should have written the command
        mock_bleak_client.write_gatt_char.assert_called()

    async def test_write_command_not_connected(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_async_ble_device_from_address,
        mock_bluetooth_adapters,
    ):
        """Test writing commands fails when not connected."""
        # Make connection fail
        with patch(
            "custom_components.adjustable_bed.coordinator.establish_connection",
            new_callable=AsyncMock,
            side_effect=BleakError("Connection failed"),
        ):
            coordinator = AdjustableBedCoordinator(hass, mock_config_entry)

            with pytest.raises(ConnectionError):
                await coordinator.async_write_command(bytes([0x01, 0x00]))


class TestCoordinatorNotifications:
    """Test coordinator notification handling."""

    async def test_start_notify_skipped_when_disabled(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test start_notify is skipped when angle sensing is disabled."""
        # Default config has disable_angle_sensing=True
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)
        await coordinator.async_connect()

        await coordinator.async_start_notify()

        # start_notify should not be called on the client
        mock_bleak_client.start_notify.assert_not_called()

    async def test_start_notify_enabled(
        self,
        hass: HomeAssistant,
        mock_config_entry_data: dict,
        mock_coordinator_connected,
        mock_bleak_client: MagicMock,
    ):
        """Test start_notify subscribes to notifications when enabled."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create entry with angle sensing enabled
        mock_config_entry_data["disable_angle_sensing"] = False
        entry = MockConfigEntry(
            domain=DOMAIN,
            title=TEST_NAME,
            data=mock_config_entry_data,
            unique_id="AA:BB:CC:DD:EE:FF",
            entry_id="test_entry_id_2",
        )

        coordinator = AdjustableBedCoordinator(hass, entry)
        await coordinator.async_connect()

        await coordinator.async_start_notify()

        # start_notify should be called for position characteristics
        assert mock_bleak_client.start_notify.call_count >= 1


class TestMotorPulseConfiguration:
    """Test motor pulse configuration."""

    async def test_default_motor_pulse_values(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test default motor pulse values are used when not configured."""
        coordinator = AdjustableBedCoordinator(hass, mock_config_entry)

        assert coordinator.motor_pulse_count == DEFAULT_MOTOR_PULSE_COUNT
        assert coordinator.motor_pulse_delay_ms == DEFAULT_MOTOR_PULSE_DELAY_MS

    async def test_custom_motor_pulse_values(
        self,
        hass: HomeAssistant,
        mock_config_entry_data: dict,
    ):
        """Test custom motor pulse values from config."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        mock_config_entry_data[CONF_MOTOR_PULSE_COUNT] = 50
        mock_config_entry_data[CONF_MOTOR_PULSE_DELAY_MS] = 100

        entry = MockConfigEntry(
            domain=DOMAIN,
            title=TEST_NAME,
            data=mock_config_entry_data,
            unique_id="AA:BB:CC:DD:EE:FF",
            entry_id="test_entry_custom_pulse",
        )

        coordinator = AdjustableBedCoordinator(hass, entry)

        assert coordinator.motor_pulse_count == 50
        assert coordinator.motor_pulse_delay_ms == 100

    async def test_richmat_bed_type_default_pulses(
        self,
        hass: HomeAssistant,
        mock_config_entry_data: dict,
    ):
        """Test Richmat bed uses its specific default pulse values."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        mock_config_entry_data[CONF_BED_TYPE] = BED_TYPE_RICHMAT
        # Don't set pulse values - should use bed-type defaults

        entry = MockConfigEntry(
            domain=DOMAIN,
            title=TEST_NAME,
            data=mock_config_entry_data,
            unique_id="AA:BB:CC:DD:EE:FF",
            entry_id="test_entry_richmat_pulse",
        )

        coordinator = AdjustableBedCoordinator(hass, entry)

        expected_count, expected_delay = BED_MOTOR_PULSE_DEFAULTS[BED_TYPE_RICHMAT]
        assert coordinator.motor_pulse_count == expected_count  # 30
        assert coordinator.motor_pulse_delay_ms == expected_delay  # 50

    async def test_keeson_bed_type_default_pulses(
        self,
        hass: HomeAssistant,
        mock_config_entry_data: dict,
    ):
        """Test Keeson bed uses its specific default pulse values."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        mock_config_entry_data[CONF_BED_TYPE] = BED_TYPE_KEESON
        # Don't set pulse values - should use bed-type defaults

        entry = MockConfigEntry(
            domain=DOMAIN,
            title=TEST_NAME,
            data=mock_config_entry_data,
            unique_id="AA:BB:CC:DD:EE:FF",
            entry_id="test_entry_keeson_pulse",
        )

        coordinator = AdjustableBedCoordinator(hass, entry)

        expected_count, expected_delay = BED_MOTOR_PULSE_DEFAULTS[BED_TYPE_KEESON]
        assert coordinator.motor_pulse_count == expected_count  # 25
        assert coordinator.motor_pulse_delay_ms == expected_delay  # 200

    async def test_custom_pulse_overrides_bed_default(
        self,
        hass: HomeAssistant,
        mock_config_entry_data: dict,
    ):
        """Test custom pulse config overrides bed-type defaults."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        mock_config_entry_data[CONF_BED_TYPE] = BED_TYPE_RICHMAT
        mock_config_entry_data[CONF_MOTOR_PULSE_COUNT] = 15
        mock_config_entry_data[CONF_MOTOR_PULSE_DELAY_MS] = 75

        entry = MockConfigEntry(
            domain=DOMAIN,
            title=TEST_NAME,
            data=mock_config_entry_data,
            unique_id="AA:BB:CC:DD:EE:FF",
            entry_id="test_entry_custom_override",
        )

        coordinator = AdjustableBedCoordinator(hass, entry)

        # Custom values should override bed-type defaults
        assert coordinator.motor_pulse_count == 15
        assert coordinator.motor_pulse_delay_ms == 75


class TestMultiMotorConfiguration:
    """Test multi-motor configuration."""

    @pytest.mark.parametrize("motor_count", [2, 3, 4])
    async def test_motor_count_configurations(
        self,
        hass: HomeAssistant,
        mock_config_entry_data: dict,
        motor_count: int,
    ):
        """Test different motor count configurations."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        mock_config_entry_data[CONF_MOTOR_COUNT] = motor_count

        entry = MockConfigEntry(
            domain=DOMAIN,
            title=TEST_NAME,
            data=mock_config_entry_data,
            unique_id="AA:BB:CC:DD:EE:FF",
            entry_id=f"test_entry_{motor_count}_motors",
        )

        coordinator = AdjustableBedCoordinator(hass, entry)

        assert coordinator.motor_count == motor_count

    async def test_device_info_reflects_motor_count(
        self,
        hass: HomeAssistant,
        mock_config_entry_data: dict,
    ):
        """Test device info model includes motor count."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        for motor_count in [2, 3, 4]:
            mock_config_entry_data[CONF_MOTOR_COUNT] = motor_count

            entry = MockConfigEntry(
                domain=DOMAIN,
                title=TEST_NAME,
                data=mock_config_entry_data,
                unique_id=f"AA:BB:CC:DD:EE:{motor_count:02X}",
                entry_id=f"test_entry_model_{motor_count}",
            )

            coordinator = AdjustableBedCoordinator(hass, entry)
            device_info = coordinator.device_info

            assert f"{motor_count} motors" in device_info["model"]
