import asyncio

from ble_scanner import BleScanner
from state import State, AirState
from ws_server import WsServer


def loop_exception_handler(loop, context):
    """ Глушит специфичный для Windows шум при жестком разрыве сокетов """
    exception = context.get('exception')
    if isinstance(exception, ConnectionResetError):
        print('Connection reset by peer')
        # Игнорируем ошибку [WinError 10054]
        return
    # Все остальные непредвиденные ошибки выводим как обычно
    loop.default_exception_handler(context)


async def main():
    # Назначаем фильтр для текущего Event Loop
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(loop_exception_handler)

    state = State(AirState())
    server = WsServer(state)
    scanner = BleScanner(state)

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
