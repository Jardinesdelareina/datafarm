import websocket, json, threading, requests
import pandas as pd
from sqlalchemy import text
from config import *
from helpers import round_step_size

# Объем ордера
QNTY = 10

# Тикеры фьючерсов Binance
SYMBOL = [
    #'btcusdt', 'ethusdt', 'bnbusdt', 'xrpusdt', 'dotusdt', 'linkusdt', 'xtzusdt', 
    #'adausdt', 'solusdt', 'maticusdt', 'avaxusdt', 'uniusdt', 'trxusdt', 'xlmusdt',
    'vetusdt', #'axsusdt', 'zilusdt', 'dogeusdt', 'nearusdt', 'aaveusdt', 'ltcusdt',
]

# Перебор тикеров для подписки на поток
SOCKETS = [f'wss://stream.binance.com:9443/ws/{symbol}@trade' for symbol in SYMBOL]

# Алерт в Telegram
def send_message(message) -> str:
    return requests.get(
        'https://api.telegram.org/bot{}/sendMessage'.format(TELETOKEN), 
        params=dict(chat_id=CHAT_ID, text=message)
    )

# Открытие соединения
def on_open(ws):
    for ticker in SYMBOL:
        ticker = ticker.upper()
        print(f'{ticker} Online')

# Обработка потока Binance
def on_message(ws, df):
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

    signal_bear = max_price_last_hour - (max_price_last_hour / 100)
    signal_bull = min_price_last_hour + (max_price_last_hour / 100)

    # Расчет объема ордера в зависимости от размера шага тикера
    def calculate_quantity():
        INFO = CLIENT.exchange_info()
        for symbol in INFO['symbols']:
            if symbol['symbol'] == db_ticker:
                step_size = symbol['filters'][2]['stepSize']
                order_volume = QNTY / last_price
                order_volume = round_step_size(order_volume, step_size)
                print(order_volume)
                return order_volume

    if last_price == signal_bull:
        CLIENT.new_order(symbol=db_ticker, side='BUY', type='MARKET', quantity=calculate_quantity())
        send_message(f'{db_ticker} SELL')
        print(f'{db_ticker} Sell')
    elif last_price == signal_bear:
        CLIENT.new_order(symbol=db_ticker, side='SELL', type='MARKET', quantity=calculate_quantity())
        send_message(f'{db_ticker} BUY')
        print(f'{db_ticker} Buy')
    else:
        print(f'Price {db_ticker}: {last_price} \n Buy: {signal_bull} \n Sell: {signal_bear} \n')

# Точка подключения websocket для потока
def main(socket):
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
