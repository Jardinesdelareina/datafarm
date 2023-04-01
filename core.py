import asyncio, requests
import pandas as pd
from binance import BinanceSocketManager
from config import CLIENT, ENGINE, TELETOKEN, CHAT_ID
from sqlalchemy import text

SYMBOL = 'XRPUSDT'
open_position = False


def send_message(message: str) -> str:
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
    db_ticker = df.symbol.iloc[0].lower()
    df.to_sql(name=f'{db_ticker.lower()}', con=ENGINE, if_exists='append', index=False)

    def execute_query(query: str):
        """ Оборачивание запросов к базе данных

            query (str): SQL запрос
            return (Pandas DataFrame): Результат выполнения запроса 
        """
        with ENGINE.connect() as conn:
            result = conn.execute(text(query))
            df_result = pd.DataFrame(result.fetchall())
            value = float(df_result.iloc[-1].values)
            return value

    # Последняя цена тикера  
    last_price = execute_query(
        f"SELECT price FROM {db_ticker} ORDER BY time DESC LIMIT 1"
    )

    # Минимальная цена тикера за последний час
    min_price_last_hour = execute_query(
        f"SELECT MIN(price) FROM {db_ticker} WHERE time > NOW() - INTERVAL '1 HOUR'"
    )

    # Максимальная цена тикера за последний час
    max_price_last_hour = execute_query(
        f"SELECT MAX(price) FROM {db_ticker} WHERE time > NOW() - INTERVAL '1 HOUR'")

    signal_buy = round((min_price_last_hour + (min_price_last_hour / 100)), round_float(num=last_price))
    signal_sell = round((max_price_last_hour - (max_price_last_hour / 100)), round_float(num=last_price))
    
    if not open_position:
        if last_price == signal_buy:
            message = f'{db_ticker.upper()}: {last_price} Buy'
            send_message(message)
            print(message)
            open_position == True
        else:
            print(f'''
                {db_ticker.upper()}: {last_price}
                BUY: {signal_buy}
                ''')
    if open_position:
        if last_price == signal_sell:
            message = f'{db_ticker.upper()}: {last_price} Sell'
            send_message(message)
            print(message)
            open_position == False
        else:
            print(f'''
                {db_ticker.upper()}: {last_price} 
                SELL: {signal_sell}
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
