import websocket, json, threading
import pandas as pd
from sqlalchemy import create_engine

# Тикеры фьючерсов Binance
SYMBOL = [
    'btcusdt', 'ethusdt', 'bnbusdt', 'xrpusdt', 'dotusdt', 'linkusdt', 'xtzusdt', 
    'adausdt', 'solusdt', 'maticusdt', 'avaxusdt', 'uniusdt', 'trxusdt', 'xlmusdt',
    'vetusdt', 'axsusdt', 'zilusdt', 'dogeusdt', 'nearusdt', 'aaveusdt', 'ltcusdt',
]

# Перебор тикеров для подписки на поток
SOCKETS = [f'wss://stream.binance.com:9443/ws/{symbol}@trade' for symbol in SYMBOL]

# Подключение к Sqlite3
ENGINE = create_engine(f'sqlite:///sqlite.db')

# Открытие соединения
def on_open(ws):
    for ticker in SYMBOL:
        ticker = ticker.upper()
        print(f'{ticker} Online')

# Закрытие соединения
def on_close(ws):
    print('Offline')

# Обработка потока Binance
def on_message(ws, df):
    df = pd.DataFrame([json.loads(df)])
    df = df.loc[:, ['s', 'E', 'p']]
    df.columns = ['Symbol', 'Time', 'Price']
    df.Time = pd.to_datetime(df.Time, unit='ms', utc=True, infer_datetime_format=True)
    df.Price = df.Price.astype(float)
    db_ticker = df.Symbol.iloc[0].upper()
    df.to_sql(name=f'{db_ticker}', con=ENGINE, if_exists='append', index=False)
    print(df.Symbol, df.Price)

# Точка подключения websocket для потока
def main(socket):
    ws = websocket.WebSocketApp(
        socket, 
        on_open=on_open, 
        on_close=on_close, 
        on_message=on_message)
    ws.run_forever()

# Разделение потоков: один тикер - один поток
threads = []
for socket in SOCKETS:
    thread_socket = threading.Thread(target=main, args=(socket,))
    threads.append(thread_socket)
    thread_socket.start()
