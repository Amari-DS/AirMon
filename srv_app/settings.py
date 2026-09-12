import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from srv_app.misc import get_base_dir

DEFAULT_PORT = 27111
DEFAULT_BROADCAST_INTERVAL = 10


DEFAULT_ENV_TEMPLATE = """# Device type: "qingping_tlv" or "bt_home"
TARGET_DEVICE_TYPE=qingping_tlv
# MAC filter
#MAC_FILTER=11:22:33:AA:BB:FF
# Local server port
HTTP_PORT=27111
BROADCAST_INTERVAL_SEC=10
"""

@dataclass(frozen=True)
class Settings:
    device_type: str
    mac: str
    http_port: int
    broadcast_interval: int

    @staticmethod
    def _read_port(env_var: str = 'HTTP_PORT', default: int = DEFAULT_PORT) -> int:
        raw_val = os.getenv(env_var, '').strip()
        if not raw_val:
            return default

        try:
            port = int(raw_val)
            if 1 <= port <= 65535:
                return port
        except ValueError:
            pass

        print(f'[!] WARNING: wrong http_port="{raw_val}", default value used ({default})')
        return default

    @staticmethod
    def _read_int(
        env_var: str,
        default: int,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> int:
        raw_val = os.getenv(env_var, '').strip()
        if not raw_val:
            return default

        try:
            val = int(raw_val)
            if min_val is not None and val < min_val:
                raise ValueError(f'value is less than {min_val}')
            if max_val is not None and val > max_val:
                raise ValueError(f'value is greater than {max_val}')
            return val
        except ValueError as err:
            print(f'[!] WARNING: wrong {env_var}="{raw_val}" ({err}), default value used ({default})')
            return default


    @staticmethod
    def _ensure_env_exists(env_path: Path) -> None:
        if not env_path.exists():
            env_path.write_text(DEFAULT_ENV_TEMPLATE, encoding='utf-8')
            print(f'[!] Default .env created')
            print('[!] Please, specify correct TARGET_DEVICE_TYPE')

    @classmethod
    def load(cls) -> 'Settings':
        env_path = get_base_dir() / '.env'
        cls._ensure_env_exists(env_path)
        load_dotenv(dotenv_path=env_path)

        return cls(
            device_type=os.getenv('TARGET_DEVICE_TYPE', 'qingping').strip(),
            mac=os.getenv('MAC_FILTER', '').strip().upper(),
            http_port=cls._read_int(
                'HTTP_PORT',
                default=DEFAULT_PORT,
                min_val=1,
                max_val=65535
            ),
            broadcast_interval=cls._read_int(
                'BROADCAST_INTERVAL_SEC',
                default=DEFAULT_BROADCAST_INTERVAL,
                min_val=1
            )
        )
