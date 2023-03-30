import websocket, json, threading, requests
import pandas as pd
from sqlalchemy import text
from config import ENGINE, TELETOKEN, CHAT_ID
from helpers import symbol_list, round_float

# Перебор тикеров для подписки на поток
SOCKETS = [f'wss://stream.binance.com:9443/ws/{symbol}@trade' for symbol in symbol_list]


def send_message(message) -> str:
    """ Уведомления в Telegram """
    return requests.get(
        f'https://api.telegram.org/bot{TELETOKEN}/sendMessage', 
        params=dict(chat_id=CHAT_ID, text=message)
    )    


def on_open(ws):
    """ Открытие соединения """
    for symbol in symbol_list:
        symbol = symbol.upper()
        print(f'{symbol} Online')


def on_message(ws, df):
    """ Обработка потока Binance """
    df = pd.DataFrame([json.loads(df)])
    df = df.loc[:, ['s', 'E', 'p']]
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

        # Максимальная цена тикера за последний час
        max_price_last_hour = conn.execute(text(
            f"SELECT MAX(price) FROM {db_ticker.lower()} WHERE time > NOW() - INTERVAL '1 HOUR'"
        ))
        max_price_last_hour = pd.DataFrame(max_price_last_hour.fetchall()) 
        max_price_last_hour = float(max_price_last_hour.iloc[-1].values)

        # Минимальная цена тикера за последний час
        min_price_last_hour = conn.execute(text(
            f"SELECT MIN(price) FROM {db_ticker.lower()} WHERE time > NOW() - INTERVAL '1 HOUR'"
        ))
        min_price_last_hour = pd.DataFrame(min_price_last_hour.fetchall()) 
        min_price_last_hour = float(min_price_last_hour.iloc[-1].values)

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
        print(f'{db_ticker}: {last_price}')


def main(socket):
    """ Точка подключения websocket для потока """
    ws = websocket.WebSocketApp(
        socket, 
        on_open=on_open, 
        on_message=on_message
    )
    ws.run_forever()


# Разделение потоков: один тикер - один поток
threads = []
for socket in SOCKETS:
    thread_socket = threading.Thread(target=main, args=(socket,))
    threads.append(thread_socket)
    thread_socket.start()
