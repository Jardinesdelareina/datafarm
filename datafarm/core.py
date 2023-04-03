import asyncio, requests, json
import pandas as pd
from binance import BinanceSocketManager
from binance.helpers import round_step_size
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
from .config_binance import CLIENT, ENGINE
from telegram.config_telegram import TELETOKEN, CHAT_ID

symbol_list = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT',
    'ADAUSDT', 'SOLUSDT', 'MATICUSDT', 'UNIUSDT', 'AVAXUSDT', 'NEARUSDT'
]


class Datafarm:
    """ Базовый класс, содержащий инфраструктуру обработки данных, торговую стратегию, 
        построенную на основе полученных данных и логику взаимодействия с API Binance.
    """

    def __init__(self, symbol, qnty=15):
        """ Конструктор класса Datafarm

            symbol (str): Тикер криптовалютной пары

            qnty (float): Объем ордера, по-умолчанию 15

            __open_position (bool): Состояние, в котором находится алгоритм. 
                                    Если нет открытой позиции, значение атрибута - False,
                                    если произошло событие signal_buy - True

            __last_signal (str): Текстовое сообщение о торговом сигнале, передаваемое как 
                                уведомление в Telegram и в терминал.

            __last_log (str): Текстовое уведомление, логирующее работу алгоритма в состоянии
                            ожидания торгового сигнала.

            ** __last_signal и __last_log служат для предотвращения дублирования уведомлений
            при поступающих через вебсокеты идентичных данных.

            running (bool): Состояние цикла while в методе main. 
                            Если True - данные через API Binance непрерывно поступают,
                            если False - поступление данных прекращается, работа алгоритма останавливается
        """
        self.symbol = symbol
        self.qnty = qnty
        self.__open_position = False
        self.__last_signal = None
        self.__last_log = None
        self.running = True


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


    @staticmethod
    def get_balance(ticker: str) -> float:
        """ Баланс определенной криптовалюты на спотовом кошельке Binance

            ticker (str): Тикер криптовалюты (базовой, без котируемой, в формате 'BTC', 'ETH' и т.д.)
            return (float): Количество заданной криптовалюты
        """
        asset_balance = CLIENT.get_asset_balance(asset=ticker)
        balance_free = float(asset_balance.get('free'))
        return balance_free


    def calculate_quantity(self) -> float:
        """ Расчет объема ордера 
        """
        symbol_info = CLIENT.get_symbol_info(self.symbol)
        step_size = symbol_info.get('filters')[1]['stepSize']
        order_volume = self.qnty / self.last_price
        order_volume = round_step_size(order_volume, step_size)
        return order_volume


    def place_order(self, order_side: str):
        """ Размещение ордеров
            
            order_side (str): Направление ордера, передаваемое при вызове функции в алгоритме.
        """

        if order_side == 'BUY':
            order = CLIENT.create_order(
                symbol=self.symbol, 
                side='BUY', 
                type='MARKET', 
                quantity=self.calculate_quantity(),
            )
            self.__open_position = True
            self.buy_price = round(
                float(order.get('fills')[0]['price']), 
                self.round_float(num=self.last_price)
            )
            message = f'{self.symbol} \n Buy \n {self.buy_price}'
            self.send_message(message)
            print(message)
            print(json.dumps(order, indent=4, sort_keys=True))

        elif order_side == 'SELL':
            order = CLIENT.create_order(
                symbol=self.symbol, 
                side='SELL', 
                type='MARKET', 
                quantity=self.calculate_quantity(),
            )
            self.__open_position = False
            self.sell_price = round(
                float(order.get('fills')[0]['price']), 
                self.round_float(num=self.last_price)
            )
            result = round((self.sell_price - self.buy_price * self.calculate_quantity()), 2)
            message = f'{self.symbol} \n Sell \n {self.sell_price} \n Результат: {result} USDT'
            self.send_message(message)
            print(message)
            print(json.dumps(order, indent=4, sort_keys=True))


    def execute_query(query: str):
        """ Обработка запросов к базе данных

            query (str): SQL запрос
            return (Pandas DataFrame): Результат выполнения запроса 
        """
        with ENGINE.connect() as conn:
            result = conn.execute(text(query))
            df_result = pd.DataFrame(result.fetchall())
            value = float(df_result.iloc[-1].values)
            return value


    def get_data(self, stream):
        """ Получение данных с биржи, сохранение в базу данных, чтение, обработка данных
            и преобразование их в торговые сигналы

            Структура таблицы базы данных:
            symbol (str): Название тикера
            time (datetime): Время поступления данных
            price (float): Значение цены тикера
        """
        df = pd.DataFrame([stream])
        df = df.loc[:,['s', 'E', 'p']]
        df.columns = ['symbol', 'time', 'price']
        df.time = pd.to_datetime(df.time, unit='ms', utc=True, infer_datetime_format=True)
        df.price = df.price.astype(float)
        db_ticker = df.symbol.iloc[0].lower()
        df.to_sql(name=f'{db_ticker}', con=ENGINE, if_exists='append', index=False)

        # Последняя цена тикера  
        self.last_price = self.execute_query(
            f"SELECT price FROM {db_ticker} ORDER BY time DESC LIMIT 1"
        )

        # Минимальная цена тикера за последний час
        min_price_last_hour = self.execute_query(
            f"SELECT MIN(price) FROM {db_ticker} WHERE time > NOW() - INTERVAL '1 HOUR'"
        )

        # Максимальная цена тикера за последний час
        max_price_last_hour = self.execute_query(
            f"SELECT MAX(price) FROM {db_ticker} WHERE time > NOW() - INTERVAL '1 HOUR'"
        )

        # Цена выше минимума за последний час на 1%
        signal_buy = round(
            (min_price_last_hour + (min_price_last_hour * 0.01)), 
            self.round_float(num=self.last_price)
        )

        # Цена ниже максимума за последний час на 1%
        signal_sell = round(
            (max_price_last_hour - (max_price_last_hour * 0.01)), 
            self.round_float(num=self.last_price)
        )

        if not self.__open_position:
            if self.last_price > signal_buy:
                try:
                    self.place_order('BUY')
                except:
                    print('Покупка невозможна')
                message = f'{self.symbol}: {self.last_price} Buy'
                if message != self.__last_signal:
                    print(message)
                    self.__last_signal = message
            else:
                message = f'{self.symbol}: {self.last_price} BUY: {signal_buy}'
                if message != self.__last_log:
                    print(self.__last_log)
                    self.__last_log = message

        if self.__open_position:
            if self.last_price < signal_sell:
                try:
                    self.place_order('SELL')
                except:
                    print('Продажа невозможна')
                message = f'{self.symbol}: {self.last_price} Sell'
                if message != self.__last_signal:
                    print(message)
                    self.__last_signal = message
            else:
                message = f'{self.symbol}: {self.last_price} SELL: {signal_buy}'
                if message != self.__last_log:
                    print(self.__last_log)
                    self.__last_log = message


    def stop(self):
        """ Остановка выполнения программы
        """
        self.running = False


    async def main(self):
        """ Подключение к потоку Binance через вебсокеты

            Поток: 'wss://stream.binance.com:9443/ws/{self.symbol}@trade'
        """
        bm = BinanceSocketManager(client=CLIENT)
        ts = bm.trade_socket(self.symbol)
        async with ts as tscm:
            while self.running:
                res = await tscm.recv()
                if res:
                    self.get_data(res)
                await asyncio.sleep(0)


""" 
# Создание объектов класса, где атрибут - элемент списка, и запуск созданных объектов многопоточно
bots = [Datafarm(symbol, qnty=15) for symbol in symbol_list]
with ThreadPoolExecutor() as executor:
    results = executor.map(asyncio.run, [bot.main() for bot in bots]) 
"""
