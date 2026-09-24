import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "custom_components" / "heyitech_alarm"


def _install_homeassistant_stubs() -> None:
    if "homeassistant" in sys.modules:
        return

    homeassistant = types.ModuleType("homeassistant")
    homeassistant.__path__ = []
    sys.modules["homeassistant"] = homeassistant

    core = types.ModuleType("homeassistant.core")
    class HomeAssistant:  # pragma: no cover - simple stub
        pass
    core.HomeAssistant = HomeAssistant
    sys.modules["homeassistant.core"] = core

    config_entries = types.ModuleType("homeassistant.config_entries")
    class ConfigEntry:  # pragma: no cover - simple stub
        pass
    config_entries.ConfigEntry = ConfigEntry
    sys.modules["homeassistant.config_entries"] = config_entries

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    sys.modules["homeassistant.helpers"] = helpers

    update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")
    class DataUpdateCoordinator:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, *args, **kwargs):
            pass
    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator
    class UpdateFailed(Exception):
        pass
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.CoordinatorEntity = CoordinatorEntity
    update_coordinator.UpdateFailed = UpdateFailed
    sys.modules["homeassistant.helpers.update_coordinator"] = update_coordinator

    aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = lambda hass: object()
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client

    components = types.ModuleType("homeassistant.components")
    components.__path__ = []
    sys.modules["homeassistant.components"] = components

    binary_sensor = types.ModuleType("homeassistant.components.binary_sensor")
    class BinarySensorEntity:
        pass
    class BinarySensorDeviceClass:
        DOOR = "door"
    binary_sensor.BinarySensorEntity = BinarySensorEntity
    binary_sensor.BinarySensorDeviceClass = BinarySensorDeviceClass
    sys.modules["homeassistant.components.binary_sensor"] = binary_sensor

    sensor = types.ModuleType("homeassistant.components.sensor")
    class SensorEntity:
        pass
    sensor.SensorEntity = SensorEntity
    sys.modules["homeassistant.components.sensor"] = sensor


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_install_homeassistant_stubs()

custom_components_pkg = types.ModuleType("custom_components")
custom_components_pkg.__path__ = [str(ROOT / "custom_components")]
sys.modules["custom_components"] = custom_components_pkg

heyitech_pkg = types.ModuleType("custom_components.heyitech_alarm")
heyitech_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules["custom_components.heyitech_alarm"] = heyitech_pkg

const = _load_module("custom_components.heyitech_alarm.const", PACKAGE_ROOT / "const.py")
api = _load_module("custom_components.heyitech_alarm.api", PACKAGE_ROOT / "api.py")
coordinator = _load_module("custom_components.heyitech_alarm.coordinator", PACKAGE_ROOT / "coordinator.py")


def test_device_state_byte_array_uses_zone_position_order():
    assert coordinator._decode_bit_array("10110") == {
        "1": True,
        "2": False,
        "3": True,
        "4": True,
        "5": False,
    }
    assert coordinator._decode_bit_array([1, 0, 1, 1, 0]) == {
        "1": True,
        "2": False,
        "3": True,
        "4": True,
        "5": False,
    }
