import asyncio
from datetime import datetime
from typing import Dict
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

KNOWN_MARKERS = {
    '0000fe95-0000-1000-8000-00805f9b34fb': 'Xiaomi MiBeacon',
    '0000181a-0000-1000-8000-00805f9b34fb': 'Environmental Sensing',
    '0000fcd2-0000-1000-8000-00805f9b34fb': 'BTHome',
    '0000fdcd-0000-1000-8000-00805f9b34fb': 'Qingping',
}

KNOWN_NAME_PREFIXES = (
    'LYWSD', 'MJ_HT', 'MHO', 'CGG', 'CGH', 'CGDK', 'Miaomiaoce', 'ATC', 'PVVX', 'ClearGrass'
)

KNOWN_DEVICES: Dict[str, str] = {}


class Analyzer:
    DEFAULT_NAME = 'Unknown'

    def __init__(self, device: BLEDevice, adv: AdvertisementData):
        self._device = device
        self._adv = adv
        self._name, self._old_name, self._address = None, None, None
        self._is_new_device = False
        self._hints = []

    @staticmethod
    def _format_hex(data: bytes) -> str:
        """ Format to HEX: 01 0A FF """
        return ' '.join(f'{b:02X}' for b in data)

    def analyze_device(self):
        self._address = self._device.address
        self._name = self._adv.local_name or self._device.name or self.DEFAULT_NAME

        self._is_new_device = self._address not in KNOWN_DEVICES
        name_has_changed = not self._is_new_device \
                           and self._name != self.DEFAULT_NAME \
                           and KNOWN_DEVICES[self._address] != self._name

        if not self._is_new_device and not name_has_changed:
            return

        self._old_name = KNOWN_DEVICES.get(self._address)
        KNOWN_DEVICES[self._address] = self._name

        self._analyze()

    def _analyze(self):
        self._check_name()
        self._check_uuids(self._adv.service_data.keys())
        self._check_uuids(self._adv.service_uuids)
        self._print_device()

    def _check_name(self):
        for prefix in KNOWN_NAME_PREFIXES:
            if self._name.upper().startswith(prefix.upper()):
                self._hints.append(f'Name matches with sensor ({prefix})')

    def _check_uuids(self, uuids):
        for uuid in uuids:
            uuid_lower = uuid.lower()
            if uuid_lower in KNOWN_MARKERS:
                self._hints.append(KNOWN_MARKERS[uuid_lower])

    def _print_device(self):
        self._print_base_info()

        if self._hints:
            print('  🔍 HINTS:')
            for hint in self._hints:
                print(f'     👉 {hint}')

        if self._adv.service_data:
            print('  📦 Service Data:')
            for uuid, data in self._adv.service_data.items():
                print(f'     - {uuid} : {self._format_hex(data)}')

        if self._adv.manufacturer_data:
            print('  🏭 Manufacturer Data:')
            for comp_id, data in self._adv.manufacturer_data.items():
                print(f'     - ID 0x{comp_id:04X} : {self._format_hex(data)}')

        if self._adv.service_uuids:
            print(f'  🏷️ Service UUIDs: {', '.join(self._adv.service_uuids)}')

    def _print_base_info(self):
        time_str = datetime.now().strftime('%H:%M:%S')
        if self._is_new_device:
            tag = '🔥 [POSSIBLE CANDIDATE]' if self._hints else '📡 [NEW DEVICE]'
        else:
            tag = f'🔄 [NAME UPDATED: {self._old_name} -> {self._name}]'

        print('=' * 65)
        print(f'{tag} | {time_str} | Total found: {len(KNOWN_DEVICES)}')
        print(f'  MAC : {self._address}')
        print(f'  Name: {self._name}')
        print(f'  RSSI: {self._adv.rssi} dBm')


def callback(device: BLEDevice, adv: AdvertisementData):
    Analyzer(device, adv).analyze_device()


async def sniff():
    print('Running BLE-sniffer...')
    print('Waiting for packets (Ctrl+C for interrupt)\n')

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()

    try:
        while True:
            await asyncio.sleep(1000)
    except asyncio.CancelledError:
        pass
    finally:
        await scanner.stop()
        print(f'\nScan ended. Total devices found: {len(KNOWN_DEVICES)}')
