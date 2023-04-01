import asyncio, requests
import pandas as pd
from binance import BinanceSocketManager
from config import CLIENT, ENGINE, TELETOKEN, CHAT_ID
from sqlalchemy import text


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


def top_coin():
    """ Фильтр тикеров по максимальному процентному изменению
    """
    all_tickers = pd.DataFrame(CLIENT.get_ticker())
    usdt = all_tickers[all_tickers.symbol.str.contains('USDT')]
    work = usdt[~((usdt.symbol.str.contains('UP')) | (usdt.symbol.str.contains('DOWN')))]
    top_coin = work[work.priceChangePercent == work.priceChangePercent.max()]
    top_coin = top_coin.symbol.values[0]
    return top_coin


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

    # Цена выше минимума за последний час на 1%
    signal_buy = round((min_price_last_hour + (min_price_last_hour / 1000)), round_float(num=last_price))

    # Цена ниже максимума за последний час на 0.5%
    signal_sell = round((max_price_last_hour - (max_price_last_hour / 500)), round_float(num=last_price))
    
    open_position = False
    last_signal = None
    last_print = None
    if not open_position:
        if last_price > signal_buy:
            message = f'{db_ticker.upper()}: {last_price} Buy'
            if message != last_signal:
                send_message(message)
                print(message)
                last_signal = message
            open_position = True
        else:
            last_log = f'{db_ticker.upper()}: {last_price} BUY: {signal_buy}'
            if last_log != last_print:
                print(last_log)
                last_log = last_print
    if open_position:
        if last_price < signal_sell:
            message = f'{db_ticker.upper()}: {last_price} Sell'
            if message != last_signal:
                send_message(message)
                print(message)
                last_signal = message
            open_position = False
        else:
            last_log = f'{db_ticker.upper()}: {last_price} SELL: {signal_buy}'
            if last_log != last_print:
                print(last_log)
                last_log = last_print

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
    asyncio.run(main(top_coin()))
except KeyboardInterrupt:
    print('Stop')
