import websocket, threading
from core import SYMBOL, SOCKETS, get_data

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
    get_data(df)

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
