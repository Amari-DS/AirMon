import asyncio

from ble_scanner import BleScanner
from srv_app.settings import Settings
from state import State, AirState
from ws_server import WsServer


def loop_exception_handler(loop, context):
    exception = context.get('exception')
    if isinstance(exception, ConnectionResetError):
        print('Connection reset by peer')
        # ignoring [WinError 10054]
        return
    loop.default_exception_handler(context)


async def main():
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(loop_exception_handler)

    settings = Settings.load()
    state = State(AirState())
    server = WsServer(state, settings)
    scanner = BleScanner(state, settings)

    await server.run_server()
    await scanner.run()

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()
        await scanner.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")
