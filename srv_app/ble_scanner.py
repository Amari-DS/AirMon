import time

from bleak import BleakScanner, BLEDevice, AdvertisementData

from state import State, AirState

QINGPING_SERVICE_UUID = '0000fdcd-0000-1000-8000-00805f9b34fb'


class BleScanner:

    def __init__(self, state: State):
        self.__state: State = state
        self.__scanner = BleakScanner(detection_callback=self.__ble_callback)

    def __parse_qingping_payload(self, raw_data: bytes) -> AirState | None:
        """ Парсер TLV-структуры пакетов Qingping """
        if len(raw_data) < 8:
            return None

        air_state = AirState()
        offset = 8
        length = len(raw_data)

        while offset < length:
            data_type = raw_data[offset]
            data_len = raw_data[offset + 1]
            val_start = offset + 2
            val_end = val_start + data_len

            if val_end > length:
                break

            val_bytes = raw_data[val_start:val_end]
            self.__parse_value(data_type, data_len, val_bytes, air_state)
            offset = val_end

        return air_state

    @staticmethod
    def __parse_value(data_type, data_len, val_bytes, air_state: AirState) -> int | None:
        if data_type == 0x01 and data_len == 4:
            # 0x01: Температура и влажность (4 байта)
            air_state.temperature = int.from_bytes(val_bytes[0:2], 'little', signed=True) / 10.0
            air_state.humidity = int.from_bytes(val_bytes[2:4], 'little', signed=False) / 10.0
        elif data_type == 0x02 and data_len == 1:
            # 0x02: Батарея (1 байт)
            air_state.battery = val_bytes[0]
        elif data_type == 0x07 and data_len == 2:
            # 0x07: Давление (2 байта)
            air_state.pressure = int.from_bytes(val_bytes, 'little') / 10.0
        elif data_type in (0x12, 0x13, 0x18) and data_len == 2:
            # 0x12, 0x13, 0x18: CO2 (2 байта)
            air_state.co2 = int.from_bytes(val_bytes, 'little')

    def __ble_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """ Callback при получении BLE-пакета """
        for uuid, raw_data in advertisement_data.service_data.items():
            if uuid.lower() == QINGPING_SERVICE_UUID:
                air_state = self.__parse_qingping_payload(raw_data)
                if air_state:
                    air_state.address = device.address
                    air_state.name = device.name or 'Unknown device'
                    air_state.rssi = advertisement_data.rssi
                    air_state.last_updated = time.time()
                    self.__state.current = air_state
                    print(air_state)

    async def run(self):
        # Запуск BLE-сканера
        await self.__scanner.start()
        print('[*] BLE сканирование запущено. Ожидание данных от монитора...')

    async def stop(self):
        await self.__scanner.stop()
