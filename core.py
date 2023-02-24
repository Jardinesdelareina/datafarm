import websocket, json, threading
import pandas as pd
import environs
from sqlalchemy import create_engine, text

env = environs.Env()
env.read_env('.env')

USER = env('USER')
PASSWORD = env('PASSWORD')
HOST = env('HOST')
PORT = env('PORT')
DB_NAME = env('DB_NAME')

# Тикеры фьючерсов Binance
SYMBOL = [
    'btcusdt', 'ethusdt', 'bnbusdt', 'xrpusdt', 'dotusdt', 'linkusdt', 'xtzusdt', 
    'adausdt', 'solusdt', 'maticusdt', 'avaxusdt', 'uniusdt', 'trxusdt', 'xlmusdt',
    'vetusdt', 'axsusdt', 'zilusdt', 'dogeusdt', 'nearusdt', 'aaveusdt', 'ltcusdt',
]

# Перебор тикеров для подписки на поток
SOCKETS = [f'wss://stream.binance.com:9443/ws/{symbol}@trade' for symbol in SYMBOL]

# Подключение к PostgreSQL 
ENGINE = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}')

# Открытие соединения, создание базы данных
def on_open(ws):
    try:
        ENGINE.execute("CREATE DATABASE datafarm")
        print('База данных успешно создана')
    except Exception as e:
        print('Ошибка при создании базы данных')
        raise e
    for ticker in SYMBOL:
        ticker = ticker.upper()
        print(f'{ticker} Online')

# Закрытие соединения, удаление базы данных
def on_close(ws):
    try:
        ENGINE.execute("DROP DATABASE datafarm")
        print('База данных успешно удалена')
    except Exception as e:
        print('Ошибка при удалении базы данных')
        raise e
    print('Offline')

# Обработка потока Binance
def on_message(ws, df):
    df = pd.DataFrame([json.loads(df)])
    df = df.loc[:, ['s', 'E', 'p']]
    df.columns = ['symbol', 'time', 'price']
    df.time = pd.to_datetime(df.time, unit='ms', utc=True, infer_datetime_format=True)
    df.price = df.price.astype(float)
    db_ticker = df.symbol.iloc[0].lower()
    df.to_sql(name=f'{db_ticker}', con=ENGINE, if_exists='append', index=False)

    with ENGINE.connect() as conn:

        # Максимальная цена тикера за последний час
        max_price_last_hour = conn.execute(text(
            f"SELECT MAX(price) FROM {db_ticker} WHERE time > NOW() - INTERVAL '1 HOUR'"
        ))
        max_price_last_hour = pd.DataFrame(max_price_last_hour.fetchall()) 
        max_price_last_hour = max_price_last_hour.iloc[-1].values

        # Минимальная цена тикера за последний час
        min_price_last_hour = conn.execute(text(
            f"SELECT MIN(price) FROM {db_ticker} WHERE time > NOW() - INTERVAL '1 HOUR'"
        ))
        min_price_last_hour = pd.DataFrame(min_price_last_hour.fetchall()) 
        min_price_last_hour = min_price_last_hour.iloc[-1].values

        # Последняя цена тикера
        last_price = conn.execute(text(
            f"SELECT price FROM {db_ticker} ORDER BY time DESC LIMIT 1"
        ))
        last_price = pd.DataFrame(last_price.fetchall())
        last_price = last_price.iloc[-1].values

    one_percent_bear = max_price_last_hour - (max_price_last_hour / 100)
    one_percent_bull = min_price_last_hour + (max_price_last_hour / 100)

    if last_price == one_percent_bear:
        print('Sell')
    elif last_price == one_percent_bull:
        print('Buy')
    else:
        print(f'Price {db_ticker.upper()}: {last_price} \n Buy: {one_percent_bull} \n Sell: {one_percent_bear} \n')

# Точка подключения websocket для потока
def main(socket):
    ws = websocket.WebSocketApp(
        socket, 
        on_open=on_open, 
        on_close=on_close, 
        on_message=on_message
    )
    ws.run_forever()

# Разделение потоков: один тикер - один поток
threads = []
for socket in SOCKETS:
    thread_socket = threading.Thread(target=main, args=(socket,))
    threads.append(thread_socket)
    thread_socket.start()
