import websocket, json, threading, os
import pandas as pd

SYMBOL = ['btcusdt', 'adausdt', 'xrpusdt', 'ethusdt', 'linkusdt']
SOCKETS = [f'wss://stream.binance.com:9443/ws/{symbol}@trade' for symbol in SYMBOL]

def on_open(ws):
    print('Online')

def on_close(ws):
    print('Offline')

def on_message(ws, df):
    df = pd.DataFrame([json.loads(df)])
    df = df.loc[:, ['s', 'E', 'p']]
    df.columns = ['Symbol', 'Time', 'Price']
    df.Time = pd.to_datetime(df.Time, unit='ms', utc=True, infer_datetime_format=True)
    df.Price = df.Price.astype(float)
    with open(f'data/{df.Symbol[0]}.csv', 'a') as f:
        if os.stat(f'data/{df.Symbol[0]}.csv').st_size == 0:
            df.to_csv(f, mode='a', header=True, index=False)
        else:
            df.to_csv(f, mode='a', header=False, index=False)
    print(df.Symbol, df.Price)
    return df

def main(socket):
    ws = websocket.WebSocketApp(
        socket, 
        on_open=on_open, 
        on_close=on_close, 
        on_message=on_message)
    ws.run_forever()

threads = []
for socket in SOCKETS:
    thread_socket = threading.Thread(target=main, args=(socket,))
    threads.append(thread_socket)
    thread_socket.start()
