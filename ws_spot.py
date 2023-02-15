from binance import BinanceSocketManager
import asyncio
import pandas as pd

SYMBOL = 'XRPUSDT'

# Получение данных с биржи
def get_data(stream):
    df = pd.DataFrame([stream])
    df = df.loc[:,['s', 'E', 'p']]
    df.columns = ['Symbol', 'Time', 'Price']
    df.Time = pd.to_datetime(df.Time, unit='ms')
    df.Price = df.Price.astype(float)
    return df

# Подключение к сокетам
async def main(symbol):
    bm = BinanceSocketManager(client=CLIENT)
    ts = bm.trade_socket(symbol)
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            if res:
                df = get_data(res)
                print(df)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(main(SYMBOL))
    except KeyboardInterrupt:
        pass
