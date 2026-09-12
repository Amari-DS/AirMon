import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AirState:
    address: str = 'unknown'
    name: str = 'Unknown device'
    rssi: int | None = None
    battery: int | None = None
    co2: int | None = None
    temperature: float | None = None
    humidity: float | None = None
    pressure: float | None = None
    last_updated: float = 0.0

    def to_dict(self) -> dict:
        return {
            'timestamp': int(self.last_updated),
            'device': {
                'name': self.name,
                'address': self.address,
                'battery': self.battery,
                'rssi': self.rssi,
            },
            'sensors': {
                'co2': self.co2,
                'temperature': self.temperature,
                'humidity': self.humidity,
                'pressure': self.pressure,
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        time_str = (
            datetime.fromtimestamp(self.last_updated).strftime('%H:%M:%S')
            if self.last_updated > 0
            else '--:--'
        )
        temperature_str = f'{self.temperature:.1f}' if self.temperature else '-'
        humidity_str = f'{self.humidity:.0f}' if self.humidity else '-'
        return (f'[{time_str}] "{self.name}" @ {self.address} | {self.co2 or "-"}ppm {temperature_str}°C '
                f'{humidity_str}% | Battery: {self.battery or "-"}% Pressure: {self.pressure or "-"}')


@dataclass
class State:
    current: AirState
