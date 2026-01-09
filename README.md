# Smart Bed Home Assistant Integration

A Home Assistant custom integration for controlling smart adjustable beds via Bluetooth Low Energy (BLE).

**A massive thanks to the developers of [smartbed-mqtt](https://github.com/richardhopton/smartbed-mqtt)!** This integration wouldn't have been possible without their pioneering work reverse-engineering bed protocols and building the original MQTT-based solution.

> **Warning: Alpha Software**
>
> This project is in early alpha. **Only Linak beds have been fully tested.** Other bed types are implemented but need community testing. Expect bugs, breaking changes, and incomplete features. Use at your own risk.
>
> **Contributions are very welcome!** If you have a different bed type and can help test or improve support, please open an issue or submit a pull request. See [Contributing](#contributing) below.

## Supported Beds

### Implemented

| Brand | Status | Protocol | Notes |
|-------|--------|----------|-------|
| **Linak** | Tested | Linak BLE | Full support with position feedback |
| **Richmat** | Implemented | Nordic / WiLinke | Two protocol variants |
| **Keeson** | Implemented | KSBT / BaseI4/I5 | Member's Mark, Purple, ErgoMotion |
| **Solace** | Implemented | 11-byte packets | Hospital/care beds |
| **MotoSleep** | Implemented | HHC ASCII | Device name starts with "HHC" |
| **Leggett & Platt** | Implemented | Gen2 ASCII / Okin | Two distinct variants |
| **Reverie** | Implemented | XOR checksum | Position-based motor control |
| **Okimat** | Implemented | Okin binary | Requires BLE pairing |

### Not Yet Implemented
- **Octo / Sleeptracker AI** - Cloud-based (Tempur Ergo, BeautyRest, Serta)

## Features

### Common Features (All Brands)

- **Motor Control**: Control head, back, legs, and feet positions (depending on motor count)
- **Memory Presets**: Go to saved positions (number varies by brand)
- **Stop All**: Immediately stop all motor movement

### Brand-Specific Features

| Feature | Linak | Richmat | Keeson | Solace | MotoSleep | Leggett | Reverie | Okimat |
|---------|-------|---------|--------|--------|-----------|---------|---------|--------|
| Memory Presets | 4 | 2 | 4 | 5 | 2 | 4 | 4 | 4 |
| Program Memory | Yes | Yes | - | Yes | Yes | Yes* | Yes | - |
| Under-bed Lights | Yes | Yes | Yes | - | Yes | RGB* | Yes | Yes |
| Massage Control | Yes | Yes | Yes | - | Yes | Yes* | Yes | Yes |
| Position Feedback | Yes | - | - | - | - | - | - | - |
| Zero-G Preset | - | Yes | Yes | Yes | Yes | - | Yes | Yes |
| Anti-Snore | - | Yes | - | Yes | Yes | Yes* | Yes | - |

*Gen2 variant only

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu and select "Custom repositories"
3. Add this repository URL with category "Integration"
4. Search for "Smart Bed" and install
5. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/smartbed` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Automatic Discovery

The integration will automatically discover supported beds via Bluetooth based on their service UUIDs and device names. When discovered:

1. Go to **Settings** → **Devices & Services**
2. You should see a notification about a discovered Smart Bed
3. Click **Configure** and follow the setup wizard

### Manual Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Smart Bed"
4. Enter the Bluetooth address manually or select from discovered devices
5. Configure:
   - **Name**: Friendly name for your bed
   - **Motor Count**: Number of motors (2, 3, or 4)
   - **Has Massage**: Whether your bed has massage functionality

## Bluetooth Setup

This integration uses Home Assistant's native Bluetooth stack, which supports:

- **Local Bluetooth**: Built-in Bluetooth adapter on your HA host
- **ESPHome Bluetooth Proxy**: ESP32 devices running ESPHome as Bluetooth proxies

### ESPHome Bluetooth Proxy

Unlike the old smartbed-mqtt addon, this integration works seamlessly with ESPHome Bluetooth proxies because it uses Home Assistant's Bluetooth stack directly. No need for dedicated proxies!

## Entities

### Cover Entities (Motor Control)

| Entity | Description | Requirements |
|--------|-------------|--------------|
| `cover.<name>_back` | Back/upper body section | 2+ motors |
| `cover.<name>_legs` | Leg section | 2+ motors |
| `cover.<name>_head` | Head section | 3+ motors |
| `cover.<name>_feet` | Feet section | 4 motors |

### Button Entities

| Entity | Description |
|--------|-------------|
| `button.<name>_preset_memory_1` | Go to Memory 1 position |
| `button.<name>_preset_memory_2` | Go to Memory 2 position |
| `button.<name>_preset_memory_3` | Go to Memory 3 position |
| `button.<name>_preset_memory_4` | Go to Memory 4 position |
| `button.<name>_program_memory_*` | Save current position to memory |
| `button.<name>_stop` | Stop all motors |
| `button.<name>_massage_*` | Massage controls (if equipped) |

### Sensor Entities

| Entity | Description | Requirements |
|--------|-------------|--------------|
| `sensor.<name>_back_angle` | Back section angle | 2+ motors |
| `sensor.<name>_leg_angle` | Leg section angle | 2+ motors |
| `sensor.<name>_head_angle` | Head section angle | 3+ motors |
| `sensor.<name>_feet_angle` | Feet section angle | 4 motors |

### Switch Entities

| Entity | Description |
|--------|-------------|
| `switch.<name>_under_bed_lights` | Under-bed lighting |

## Troubleshooting

For detailed troubleshooting steps, see the [Connection Guide](docs/CONNECTION_GUIDE.md).

### Quick Fixes

1. **Check Bluetooth range**: Ensure your Bluetooth adapter or ESPHome proxy is within range
2. **Disconnect manufacturer app**: Most beds only allow one BLE connection
3. **Restart the integration**: Go to Settings → Devices & Services → Smart Bed → Reload
4. **Check logs**: Enable debug logging for `custom_components.smartbed`

### Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smartbed: debug
    homeassistant.components.bluetooth: debug
```

## Documentation

- [Connection Guide](docs/CONNECTION_GUIDE.md) - Detailed setup and troubleshooting
- [ESPHome Bluetooth Proxy Setup](docs/CONNECTION_GUIDE.md#setting-up-an-esphome-bluetooth-proxy)
- [Identifying Your Bed](docs/CONNECTION_GUIDE.md#identifying-your-bed)
- [Technical Protocol Details](docs/CONNECTION_GUIDE.md#technical-details)

## Migration from smartbed-mqtt

If you're migrating from the smartbed-mqtt addon:

1. Install this integration
2. Configure your bed(s)
3. Test that everything works
4. Disable/remove the smartbed-mqtt addon
5. Delete old MQTT entities if desired

**Key Differences from smartbed-mqtt:**
- Uses Home Assistant's native Bluetooth stack (no ESPHome API compatibility issues!)
- Works seamlessly with ESPHome Bluetooth proxies
- No MQTT broker required
- Native Home Assistant entities instead of MQTT discovery

## Contributing

**Contributions are very welcome!** We need help testing the newly implemented bed types.

### How You Can Help

- **Own a supported bed?** Help us test! Report what works and what doesn't.
- **Found a bug?** Please open an issue with as much detail as possible.
- **Have ideas?** Feature requests and suggestions are welcome.
- **Can code?** Pull requests are greatly appreciated.

### Testing New Bed Types

Most bed types are now implemented but need real-world testing:

1. Install the integration and configure your bed
2. Test all features (motors, presets, lights, massage)
3. Report any issues with debug logs enabled
4. Share your bed brand/model for documentation

### Adding Support for New Bed Types

1. Capture BLE traffic using nRF Connect or similar
2. Document the GATT services and characteristics
3. Implement a new controller in `beds/`
4. Add bed detection to `config_flow.py`

See [Technical Details](docs/CONNECTION_GUIDE.md#technical-details) for protocol documentation format.

## License

This project is licensed under the MIT License.
