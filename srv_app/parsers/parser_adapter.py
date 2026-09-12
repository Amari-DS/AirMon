from bthome_ble import BTHomeBluetoothDeviceData
from habluetooth.models import BluetoothServiceInfoBleak
from qingping_ble import QingpingBluetoothDeviceData
from sensor_state_data import SensorUpdate

from parsers.base import BaseBleParser
from parsers.factory import BleParserFactory


class BleParserAdapter[T: (BTHomeBluetoothDeviceData, QingpingBluetoothDeviceData)](BaseBleParser):

    def __init__(self, target_class: type[T]) -> None:
        self._target_class: type[T] = target_class
        self._cache: T | None = None

    @property
    def __instance(self) -> T:
        if self._cache is None:
            self._cache = self._target_class()
        return self._cache  # noqa

    def supported(self, bt_info: BluetoothServiceInfoBleak) -> bool:
        return self.__instance.supported(bt_info)

    def _parse_internal(self, bt_info: BluetoothServiceInfoBleak) -> SensorUpdate:
        result = self.__instance.update(bt_info)
        self._cache = None  # must be expendable or .supported(...) will be always True
        return result


@BleParserFactory.register('qingping_tlv')
class QingpingParser(BleParserAdapter[QingpingBluetoothDeviceData]):

    def __init__(self) -> None:
        super().__init__(QingpingBluetoothDeviceData)


@BleParserFactory.register('bt_home')
class BTHomeParser(BleParserAdapter[BTHomeBluetoothDeviceData]):

    def __init__(self):
        super().__init__(BTHomeBluetoothDeviceData)
