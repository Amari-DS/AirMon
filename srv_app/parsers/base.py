from abc import ABC, abstractmethod

from habluetooth import BluetoothServiceInfoBleak
from sensor_state_data import SensorUpdate, SensorDeviceClass

from srv_app.state import AirState


class BaseBleParser(ABC):

    @abstractmethod
    def supported(self, bt_info: BluetoothServiceInfoBleak) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _parse_internal(self, bt_info: BluetoothServiceInfoBleak) -> SensorUpdate:
        raise NotImplementedError

    def parse(self, bt_info: BluetoothServiceInfoBleak) -> AirState | None:
        air_state = AirState()
        update_data = self._parse_internal(bt_info)
        for key, entity in update_data.entity_values.items():
            if device_desc := update_data.entity_descriptions.get(key):
                self.__route_val(air_state, device_desc.device_class, entity.native_value)

        if any(v is not None for v in (
                air_state.co2, air_state.temperature, air_state.humidity,
                air_state.battery, air_state.pressure
        )):
            return air_state
        else:
            return None

    @staticmethod
    def __route_val(state: AirState, val_type, val) -> None:
        if val is None:
            return
        match val_type:
            case SensorDeviceClass.CO2:
                state.co2 = int(val)
            case SensorDeviceClass.TEMPERATURE:
                state.temperature = round(float(val), 1)
            case SensorDeviceClass.HUMIDITY:
                state.humidity = round(float(val), 1)
            case SensorDeviceClass.BATTERY:
                state.battery = int(val)
            case SensorDeviceClass.PRESSURE:
                state.pressure = round(float(val), 1)
