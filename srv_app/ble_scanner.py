import time
from bleak import BleakScanner, BLEDevice, AdvertisementData
from habluetooth import BluetoothServiceInfoBleak

from srv_app.settings import Settings
from state import State
from srv_app.parsers.base import BaseBleParser
from srv_app.parsers.factory import BleParserFactory


class BleScanner:

    def __init__(self, state: State, settings: Settings):
        self.__state: State = state
        self.__mac_filter = settings.mac or None
        self.__parser = self.__create_parser(settings.device_type)
        self.__scanner = BleakScanner(detection_callback=self.__ble_callback)

    def __create_parser(self, device_type: str) -> BaseBleParser:
        if not device_type:
            raise ValueError('Config error: no TARGET_DEVICE_TYPE in .env')
        parser = BleParserFactory.create(device_type)
        print(f'[*] Type: {device_type}')
        print(f'[*] MAC filter: {self.__mac_filter or "-"}')
        return parser

    @staticmethod
    def __to_info(device: BLEDevice, advertisement_data: AdvertisementData) -> BluetoothServiceInfoBleak:
        return BluetoothServiceInfoBleak.from_scan(
            source='local',
            device=device,
            advertisement_data=advertisement_data,
            connectable=False,
            monotonic_time=time.monotonic(),
        )

    def __ble_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        dev_mac = device.address.upper()
        if self.__mac_filter and dev_mac != self.__mac_filter:
            return
        bt_info = self.__to_info(device, advertisement_data)
        if not self.__parser.supported(bt_info):
            return
        air_state = self.__parser.parse(bt_info)
        if air_state:
            air_state.address = dev_mac
            air_state.name = device.name or advertisement_data.local_name or 'Unknown sensor'
            air_state.rssi = advertisement_data.rssi
            air_state.last_updated = time.time()

            self.__state.current = air_state
            print(air_state)

    async def run(self):
        await self.__scanner.start()
        print(f'[*] BLE scan started')

    async def stop(self):
        await self.__scanner.stop()
