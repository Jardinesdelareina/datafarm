import asyncio, requests
import pandas as pd
from binance import BinanceSocketManager
from config import CLIENT, ENGINE, TELETOKEN, CHAT_ID
from sqlalchemy import text

SYMBOL = 'XRPUSDT'


def send_message(message) -> str:
    """ Уведомления в Telegram 
    """
    return requests.get(
        f'https://api.telegram.org/bot{TELETOKEN}/sendMessage', 
        params=dict(chat_id=CHAT_ID, text=message)
    )    


def round_float(num: float) -> int:
    """ Расчет количества знаков после запятой у числа типа float 
    """
    num_str = str(num)
    counter = 0
    for i in num_str[::-1]:
        if i == '.':
            break
        else:
            counter += 1
    return counter


def get_data(stream):
    """ Получение данных с биржи
    """
    df = pd.DataFrame([stream])
    df = df.loc[:,['s', 'E', 'p']]
    df.columns = ['symbol', 'time', 'price']
    df.time = pd.to_datetime(df.time, unit='ms', utc=True, infer_datetime_format=True)
    df.price = df.price.astype(float)
    db_ticker = df.symbol.iloc[0]
    df.to_sql(name=f'{db_ticker.lower()}', con=ENGINE, if_exists='append', index=False)
    with ENGINE.connect() as conn:
        # Последняя цена тикера
        last_price = conn.execute(text(
            f"SELECT price FROM {db_ticker.lower()} ORDER BY time DESC LIMIT 1"
        ))
        last_price = pd.DataFrame(last_price.fetchall())
        last_price = float(last_price.iloc[-1].values)

        # Минимальная цена тикера за последний час
        min_price_last_hour = conn.execute(text(
            f"SELECT MIN(price) FROM {db_ticker.lower()} WHERE time > NOW() - INTERVAL '1 HOUR'"
        ))
        min_price_last_hour = pd.DataFrame(min_price_last_hour.fetchall()) 
        min_price_last_hour = float(min_price_last_hour.iloc[-1].values)

        # Максимальная цена тикера за последний час
        max_price_last_hour = conn.execute(text(
            f"SELECT MAX(price) FROM {db_ticker.lower()} WHERE time > NOW() - INTERVAL '1 HOUR'"
        ))
        max_price_last_hour = pd.DataFrame(max_price_last_hour.fetchall()) 
        max_price_last_hour = float(max_price_last_hour.iloc[-1].values)

    signal_bull = round((min_price_last_hour + (min_price_last_hour / 100)), round_float(num=last_price))
    signal_bear = round((max_price_last_hour - (max_price_last_hour / 100)), round_float(num=last_price))
    
    if last_price == signal_bull:
        message = f'{db_ticker}: {last_price} Buy'
        send_message(message)
        print(message)
    elif last_price == signal_bear:
        message = f'{db_ticker}: {last_price} Sell'
        send_message(message)
        print(message)
    else:
        print(
            f'''
                {db_ticker}: {last_price}
                BUY: {signal_bull}
                SELL: {signal_bear}
            '''
        )


async def main(symbol):
    """ Подключение к сокетам
    """
    bm = BinanceSocketManager(client=CLIENT)
    ts = bm.trade_socket(symbol)
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            if res:
                get_data(res)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    asyncio.run(main(SYMBOL))
except KeyboardInterrupt:
    pass
