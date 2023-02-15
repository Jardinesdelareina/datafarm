import websocket, json, os
import pandas as pd

SYMBOL = 'xrpusdt'
SOCKET = f'wss://stream.binance.com:9443/ws/{SYMBOL}@trade'

# Открытие соединения
def on_open(ws):
    print('Online')

# Закрытие соединения
def on_close(ws):
    print('Offline')

# Обработка потока Binance
def on_message(ws, message):
    df = pd.DataFrame([json.loads(message)])
    df = df.loc[:, ['s', 'E', 'p']]
    df.columns = ['Symbol', 'Time', 'Price']
    df.Time = pd.to_datetime(df.Time, unit='ms', utc=True, infer_datetime_format=True)
    df.Price = df.Price.astype(float)
    with open('data.csv', 'a') as f:
        if os.stat('data.csv').st_size == 0:
            df.to_csv(f, mode='a', header=True, index=False)
        else:
            df.to_csv(f, mode='a', header=False, index=False)
    df = pd.read_csv('data.csv')
    df.Time = pd.to_datetime(df.Time)
    max_price = df[df.Time > (df.Time.iloc[-1] - pd.Timedelta(hours=1))].Price.max()
    price_now = df.Price.iloc[-1]
    max_price = max_price - (max_price / 100)
    max_price = round((max_price), 4)

    if price_now == (max_price - (max_price / 100)):
        print(f'Цена {SYMBOL} упала на 1% от максимальной цены за последний час') 
    else:
        print(f'Текущая цена: {price_now} -- 1% ниже high за последний час: {max_price}')

ws = websocket.WebSocketApp(
    SOCKET, 
    on_open=on_open, 
    on_close=on_close, 
    on_message=on_message)

ws.run_forever()
