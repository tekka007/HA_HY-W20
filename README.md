Heyitech HY-W20 Alarm integration for Home Assistant (unofficial).

This custom integration connects Home Assistant to a Heyitech HY-W20 alarm panel through the Heyitech cloud API.

Features:
- Alarm entity with disarm, arm_home, and arm_away actions.
- Zone state sensors (1-32) from terminal status endpoint.
- Zone triggered binary sensors (1-32) for automation-friendly on/off status.
- Polling coordinator with configurable refresh interval.
- Optional advanced cloud settings (timezone, terminal type, language type).
- Configurable terminal state types query (comma-separated, default: 3).
- Debug service to send raw control values.

Installation:
1. Copy this folder to your Home Assistant custom integrations path:
	 custom_components/heyitech_alarm/
2. Restart Home Assistant.
3. Add the integration from Settings > Devices & Services > Add Integration.

Configuration fields:
- Base URL: cloud endpoint, defaults to https://cloudde.heyitech.com:8038/hysoft
- Username: Heyitech account username
- Password: Heyitech account password
- Device ID: HY-W20 cloud device identifier
- API timezone, language type, terminal type: optional advanced API parameters
- Terminal state types: comma-separated stateType values for terminal status query (default: 3)
- Update interval: polling interval in seconds (5-3600)

Alarm attributes:
- alarm_state_bits/device_state_bits: raw bit strings from device snapshot.
- alarm_state_map/device_state_map: decoded per-zone booleans from bit strings.
- zone_state_list/zone_state_map: per-zone state payload from pdevgetTerminalStatus.

Zone binary sensor interpretation:
- A zone binary sensor is ON when zone state value is not 1.
- A zone binary sensor is OFF when zone state value is 1.
- Raw zone value remains available as an entity attribute.

Custom service:
- Service: heyitech_alarm.set_raw_state
- Field: state
- Allowed values:
	- 1: arm away
	- 2: arm home
	- 3: disarm

Notes:
- This is an unofficial integration and may break if cloud endpoints or payload formats change.
- Credentials are stored in the Home Assistant config entry storage.
