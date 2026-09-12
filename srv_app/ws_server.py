import asyncio

from aiohttp import web

from srv_app.misc import get_base_dir
from srv_app.settings import Settings
from state import State


HTTP_HOST = '127.0.0.1'
INDEX_HTML_PATH = get_base_dir() / 'index.html'


class WsServer:

    def __init__(self, state: State, settings: Settings):
        self.__state = state
        self.__http_port = settings.http_port
        self.__broadcast_interval = settings.broadcast_interval
        self.__connected_websockets: set[web.WebSocketResponse] = set()
        self.__runner: web.AppRunner = self.__setup()

    def __setup(self) -> web.AppRunner:
        app = web.Application()
        app.router.add_get('/', self.__index_handler)
        app.router.add_get('/ws', self.__websocket_handler)

        return web.AppRunner(app)

    @staticmethod
    async def __index_handler(_: web.Request) -> web.FileResponse | web.Response:
        if not INDEX_HTML_PATH.exists():
            return web.Response(text='index.html not foud', status=404)
        return web.FileResponse(INDEX_HTML_PATH)

    async def __websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.__connected_websockets.add(ws)

        # send current state immediately
        current_state = self.__state.current
        if current_state.last_updated > 0:
            await ws.send_str(current_state.to_json())

        try:
            async for _ in ws:
                pass  # no response handling
        finally:
            self.__connected_websockets.discard(ws)
        return ws

    async def __broadcast_loop(self):
        while True:
            await asyncio.sleep(self.__broadcast_interval)
            current_state = self.__state.current
            if self.__connected_websockets and current_state.last_updated > 0:
                payload = current_state.to_json()
                await asyncio.gather(
                    *[ws.send_str(payload) for ws in list(self.__connected_websockets)],
                    return_exceptions=True,
                )

    async def run_server(self) -> None:
        await self.__runner.setup()
        site = web.TCPSite(self.__runner, HTTP_HOST, self.__http_port)
        await site.start()

        print(f'[*] Web widget available at : http://{HTTP_HOST}:{self.__http_port}')
        print(f'[*] WebSocket endpoint      : ws://{HTTP_HOST}:{self.__http_port}/ws')
        print(f'[*] Broadcast interval      : {self.__broadcast_interval} sec')

        # Запуск фонового цикла рассылки
        asyncio.create_task(self.__broadcast_loop())

    async def stop(self) -> None:
        if self.__connected_websockets:
            await asyncio.gather(
                *[ws.close() for ws in list(self.__connected_websockets)],
                return_exceptions=True
            )
        await self.__runner.cleanup()
