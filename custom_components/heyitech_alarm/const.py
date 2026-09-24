DOMAIN = "heyitech_alarm"
PLATFORMS = ["alarm_control_panel", "sensor", "binary_sensor"]

# Config keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_BASE_URL = "base_url"
CONF_DEVICE_ID = "device_id"
CONF_TIMEZONE = "api_timezone"
CONF_LANG = "language_type"
CONF_TERMINAL = "terminal_type"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_TERMINAL_STATE_TYPES = "terminal_state_types"

# Defaults
DEFAULT_LANG = "0001"
DEFAULT_TERMINAL = "0"
DEFAULT_TZ = "+01:00"
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_TERMINAL_STATE_TYPES = "3"

# API paths
CONF_CLOUD_DEFAULT = "https://cloudde.heyitech.com:8038/hysoft"
LOGIN_PATH = "/puserlogin.shtml"
GET_ARM_STATUS_PATH = "/pdevgetArmStatus.shtml"
REMOTE_CONTROL_PATH = "/pdevremoteControl.shtml"
FIND_DEVICE_LIST_PATH = "/pdevfindDeviceList.shtml"
GET_TERMINAL_STATUS_PATH = "/pdevgetTerminalStatus.shtml"
GET_ZONE_NAME_LIST_PATH = "/pdevgetZoneNameList.shtml"

# Heyitech raw levels (status readback)
LEVEL_DISARMED = 0
LEVEL_ARMED = 1
LEVEL_HOME = 2

# Command controlType values (writes)
CMD_DISARM = 3   # NOTE: disarm uses 3 on control endpoint (special case)
CMD_ARMED = 1
CMD_HOME = 2
