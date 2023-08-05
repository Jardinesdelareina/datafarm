import asyncio
from core import Datafarm


def start_single_bot(symbol, qnty=50):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(Datafarm(symbol, qnty).socket_stream())


start_single_bot('XRPUSDT')
