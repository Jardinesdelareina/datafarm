import time
import asyncio
import pandas as pd
import plotly.graph_objects as go
import plotly.graph_objs as gos
from binance import BinanceSocketManager
from binance.exceptions import BinanceAPIException as bae
from binance.helpers import round_step_size
from config import CLIENT, DEBUG, ENGINE
from utils import log_alert, round_float, round_list, execute_query
from queries import *


class Datafarm:

    OPEN_POSITION = False           # Наличие открытой позиции в рынке
    MIN_INTERVAL = 0.002            # Дистанция от экстремума (в процентах)

    def __init__(self, symbol, qnty):
        """ symbol (str): Тикер криптовалютной пары

            qnty (float): Объем ордера, по-умолчанию 50

            __last_signal (str): Текстовое сообщение о торговом сигнале, передаваемое как 
                                уведомление в Telegram и в терминал

            __last_log (str): Текстовое уведомление, логирующее работу алгоритма в состоянии
                            ожидания торгового сигнала

            ** __last_signal и __last_log служат для предотвращения дублирования уведомлений
            при поступающих через вебсокеты идентичных данных
        """
        self.symbol = symbol.upper()
        self.qnty = qnty
        self.data_file = f'{self.symbol}.csv'
        self.__last_signal = None
        self.__last_log = None


    def calculate_quantity(self):
        """ Расчет объема ордера 
        """
        symbol_info = CLIENT.get_symbol_info(self.symbol)
        step_size = symbol_info.get('filters')[1]['stepSize']
        order_volume = self.qnty / self.last_price
        return round_step_size(order_volume, step_size)


    def place_order(self, order_side: str):
        """ Размещение ордеров
            
            order_side (str): Направление ордера (BUY или SELL)
        """

        if order_side == 'BUY':
            order = None if DEBUG else CLIENT.create_order(
                symbol=self.symbol, 
                side='BUY', 
                type='MARKET', 
                quantity=self.calculate_quantity(),
            )
            execute_query(drop_data)
            self.__class__.OPEN_POSITION = True
            self.buy_price = round(
                float(order.get('fills')[0]['price']), 
                round_float(num=self.last_price)
            )
            message = f'{self.symbol} \n Buy \n {self.buy_price}'
            log_alert(message)

        if order_side == 'SELL':
            order = None if DEBUG else CLIENT.create_order(
                symbol=self.symbol, 
                side='SELL', 
                type='MARKET', 
                quantity=self.calculate_quantity(),
            )
            execute_query(drop_data)
            self.__class__.OPEN_POSITION = False
            self.sell_price = round(
                float(order.get('fills')[0]['price']), 
                round_float(num=self.last_price)
            )
            result = round(((self.sell_price - self.buy_price) * self.calculate_quantity()), 2)
            message = f'{self.symbol} \n Sell \n {self.sell_price} \n Результат: {result} USDT'
            log_alert(message)


    def get_interval(self):
        """ Расчитывает интервал для сигнала: 
            либо четверть от диапазона, 
            либо MIN_INTERVAL, если он больше
        """
        quarter_time_range = (abs
            (execute_query(max_price_range) - execute_query(min_price_range)) / 4
        ) / self.last_price

        print(self.last_price)
        print(quarter_time_range)
        return quarter_time_range if quarter_time_range > self.MIN_INTERVAL else self.MIN_INTERVAL


    def create_frame(self, stream):
        """ Получение данных, сохранение в базу данных,
            чтение и построение стратегии на основе полученных данных
        """
        try:
            df = pd.DataFrame([stream])
            df = df.loc[:,['s', 'E', 'p']]
            df.columns = ['symbol', 'time', 'price']
            df.time = pd.Series(pd.to_datetime(df.time, unit='ms', utc=True))
            df.price = round(df.price.astype(float), round_list[f'{self.symbol}'])
            df.to_sql(name='market_stream', con=ENGINE, if_exists='append', index=False)
        except KeyError:
            pass
        
        self.last_price = execute_query(last_price)

        self.signal_buy = round(
            ((execute_query(min_price_range)) + (execute_query(min_price_range)) * self.get_interval()),
            round_float(num=self.last_price)
        )
        self.signal_sell = round(
            ((execute_query(max_price_range)) - (execute_query(max_price_range)) * self.get_interval()),
            round_float(num=self.last_price)
        )


        def report_signal(order_side):
            """ Логирование сигнала
            """
            message = f'{self.symbol} {order_side}'
            if message != self.__last_signal:
                print(message)
                self.__last_signal = message


        def report_log(order_side):
            """ Логирование ожидания сигнала
            """
            signal = self.signal_buy if not self.__class__.OPEN_POSITION else self.signal_sell
            message = f'''
            {self.symbol}: {self.last_price}
            {order_side}: {signal}
            INTERVAL: {self.get_interval() * 100}
            '''
            if message != self.__last_log:
                print(message)
                self.__last_log = message


        if not self.__class__.OPEN_POSITION:
            if self.last_price > self.signal_buy:
                self.place_order('BUY')
                report_signal('BUY')
            else:
                report_log('BUY')

        if self.__class__.OPEN_POSITION:
            if self.last_price < self.signal_sell:
                self.place_order('SELL')
                report_signal('SELL')
            else:
                report_log('SELL')


    def report_graph(self):
        """ Визуализация данных и сигналов на вход в рынок
        """
        signal_line = self.signal_buy if not self.__class__.OPEN_POSITION else self.signal_sell
        chart = go.Scatter(
            x=execute_query(column_time), 
            y=execute_query(column_price),
            mode='lines', 
            line=dict(width=2), 
            marker=dict(color='blue')
        )
        layout = go.Layout(
            title=self.symbol,
            yaxis=dict(side='right', showgrid=False, zeroline=False),
            xaxis=dict(showgrid=False, zeroline=False),
            shapes=[
                dict(
                    type='line',
                    yref='y',
                    y0=signal_line,
                    y1=signal_line,
                    xref='paper',
                    x0=0,
                    x1=1,
                    line=dict(color='green' if not self.__class__.OPEN_POSITION else 'red'),
                )
            ],
            margin=gos.layout.Margin(l=40, r=0, t=40, b=30)
        )
        data = [chart]
        fig = go.Figure(data=data, layout=layout)
        fig.write_image('report.png')


    async def socket_stream(self):
        """ Подключение к потоку Binance через вебсокеты
        """
        global online
        bm = BinanceSocketManager(client=CLIENT)
        ts = bm.trade_socket(self.symbol)
        async with ts as tscm:
            while True:
                res = await tscm.recv()
                if res:
                    try:
                        self.create_frame(res)
                    except bae:
                        print('Binance API Exception')
                        time.sleep(5)
                        self.create_frame(res)
                await asyncio.sleep(0)
