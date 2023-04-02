import asyncio, requests
import pandas as pd
from binance import BinanceSocketManager
from config import CLIENT, ENGINE, TELETOKEN, CHAT_ID
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor

symbol_list = [
    'BTCUSDT', 'ETHUSDT'
]


class Datafarm:

    def __init__(self, symbol):
        self.symbol = symbol
        self.open_position = False
        self.last_signal = None
        self.last_log = None


    def send_message(self, message: str) -> str:
        """ Уведомления в Telegram 
        """
        return requests.get(
            f'https://api.telegram.org/bot{TELETOKEN}/sendMessage', 
            params=dict(chat_id=CHAT_ID, text=message)
        )    


    def round_float(self, num: float) -> int:
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

    
    def get_data(self, stream):
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
            f"SELECT MAX(price) FROM {db_ticker} WHERE time > NOW() - INTERVAL '1 HOUR'"
        )

        # Цена выше минимума за последний час на 1%
        signal_buy = round((min_price_last_hour + (min_price_last_hour * 0.01)), self.round_float(num=last_price))

        # Цена ниже максимума за последний час на 0.5%
        signal_sell = round((max_price_last_hour - (max_price_last_hour * 0.01)), self.round_float(num=last_price))

        if not self.open_position:
            if last_price > signal_buy:
                message = f'{db_ticker.upper()}: {last_price} Buy'
                if message != self.last_signal:
                    self.send_message(message)
                    print(message)
                    self.last_signal = message
                self.open_position = True
            else:
                message = f'{db_ticker.upper()}: {last_price} BUY: {signal_buy}'
                if message != self.last_log:
                    print(self.last_log)
                    self.last_log = message
        if self.open_position:
            if last_price < signal_sell:
                message = f'{db_ticker.upper()}: {last_price} Sell'
                if message != self.last_signal:
                    self.send_message(message)
                    print(message)
                    self.last_signal = message
                self.open_position = False
            else:
                message = f'{db_ticker.upper()}: {last_price} SELL: {signal_buy}'
                if message != self.last_log:
                    print(self.last_log)
                    self.last_log = message


    async def main(self):
        """ Подключение к сокетам
        """
        bm = BinanceSocketManager(client=CLIENT)
        ts = bm.trade_socket(self.symbol)
        async with ts as tscm:
            while True:
                res = await tscm.recv()
                if res:
                    self.get_data(res)


# Создание объектов класса, где атрибут - элемент списка, и запуск созданных объектов многопоточно
bots = [Datafarm(symbol) for symbol in symbol_list]
try:
    with ThreadPoolExecutor() as executor:
        results = executor.map(asyncio.run, [bot.main() for bot in bots])
except KeyboardInterrupt:
    print('Stop')
