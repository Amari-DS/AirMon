import asyncio
import sys
from pathlib import Path

from aiohttp import web

from state import State


# Конфигурация
BROADCAST_INTERVAL_SEC = 10  # Частота рассылки по WebSocket (не чаще раза в N сек)
HTTP_HOST = '127.0.0.1'
HTTP_PORT = 27111

# Путь к HTML-файлу
def get_base_dir() -> Path:
    # Если запущено как скомпилированный exe
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)  # noqa
    # Если запущено как обычный .py скрипт
    return Path(__file__).resolve().parent

INDEX_HTML_PATH = get_base_dir() / "index.html"


class WsServer:

    def __init__(self, state: State):
        self.__state = state
        self.__connected_websockets: set[web.WebSocketResponse] = set()
        self.__runner: web.AppRunner = self.__setup()

    def __setup(self) -> web.AppRunner:
        # Настройка и запуск HTTP / WebSocket сервера
        app = web.Application()
        app.router.add_get('/', self.__index_handler)
        app.router.add_get('/ws', self.__websocket_handler)

        return web.AppRunner(app)

    @staticmethod
    async def __index_handler(_: web.Request) -> web.FileResponse | web.Response:
        """ Отдача HTML-файла """
        if not INDEX_HTML_PATH.exists():
            return web.Response(text='index.html not foud', status=404)
        return web.FileResponse(INDEX_HTML_PATH)

    async def __websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """ Обработчик WebSocket-соединений """
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.__connected_websockets.add(ws)

        # При подключении сразу отправляем последнее актуальное состояние
        current_state = self.__state.current
        if current_state.last_updated > 0:
            await ws.send_str(current_state.to_json())

        try:
            async for _ in ws:
                pass  # Принимать сообщения от клиентов не требуется
        finally:
            self.__connected_websockets.discard(ws)
        return ws

    async def __broadcast_loop(self):
        """ Фоновая рассылка данных клиентам с фиксированным интервалом """
        while True:
            await asyncio.sleep(BROADCAST_INTERVAL_SEC)
            current_state = self.__state.current
            if self.__connected_websockets and current_state.last_updated > 0:
                payload = current_state.to_json()
                await asyncio.gather(
                    *[ws.send_str(payload) for ws in list(self.__connected_websockets)],
                    return_exceptions=True,
                )

    async def run_server(self) -> None:
        await self.__runner.setup()
        site = web.TCPSite(self.__runner, HTTP_HOST, HTTP_PORT)
        await site.start()

        print(f'[*] Веб-виджет доступен по адресу : http://{HTTP_HOST}:{HTTP_PORT}')
        print(f'[*] WebSocket эндпоинт            : ws://{HTTP_HOST}:{HTTP_PORT}/ws')
        print(f'[*] Интервал рассылки в сокет     : {BROADCAST_INTERVAL_SEC} сек')

        # Запуск фонового цикла рассылки
        asyncio.create_task(self.__broadcast_loop())

    async def stop(self) -> None:
        if self.__connected_websockets:
            await asyncio.gather(
                *[ws.close() for ws in list(self.__connected_websockets)],
                return_exceptions=True
            )
        await self.__runner.cleanup()
