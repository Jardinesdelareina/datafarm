import asyncio
import pandas as pd
from binance import BinanceSocketManager
from datafarm.config_binance import CLIENT
from datafarm.core import start_single_bot


async def socket_stream():
    """ Подключение к потоку Binance через вебсокеты
    """
    bm = BinanceSocketManager(client=CLIENT)
    ts = bm.symbol_ticker_socket('BTCTUSD')
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            if res:
                df = pd.DataFrame([res])
                df = df.loc[:,['s', 'E', 'b']]
                df.columns = ['Symbol', 'Time', 'Price']
                df.Time = pd.Series(pd.to_datetime(df.Time, unit='ms', utc=True)).dt.strftime('%Y-%m-%d %H:%M:%S')
                df.Price = df.Price.astype(float)
                print(df.Price)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
asyncio.run(socket_stream())
