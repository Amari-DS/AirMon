from srv_app.parsers.base import BaseBleParser


class BleParserFactory:
    _registry: dict[str, type[BaseBleParser]] = {}

    @classmethod
    def register(cls, type_str: str):
        def decorator(parser_cls: type[BaseBleParser]):
            cls._registry[type_str] = parser_cls
            return parser_cls

        return decorator

    @classmethod
    def create(cls, type_str: str) -> BaseBleParser:
        parser_cls = cls._registry.get(type_str)
        if not parser_cls:
            raise ValueError(f'No parser for parser_type={type_str}')
        return parser_cls()
