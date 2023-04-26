import asyncio, requests, os
import pandas as pd
import plotly.graph_objects as go
import plotly.graph_objs as gos
from binance import BinanceSocketManager
from binance.helpers import round_step_size
from datafarm.config_binance import CLIENT
from datafarm.utils import round_list, remove_file
from telegram.config_telegram import TELETOKEN, CHAT_ID

online = True
closed = False


def bot_off() -> bool:
    """ Остановка алгоритма
    """
    global online
    online = False
    

def bot_closed() -> bool:
    """ Продажа по рынку
    """
    global closed
    closed = True


def start_single_bot(symbol, qnty):
    """ Запуск алгоритма извне по одному выбранному тикеру
    """
    global online
    online = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(Datafarm(symbol, qnty).socket_stream())


class Datafarm:
    """ Базовый класс, содержащий инфраструктуру обработки данных, торговую стратегию, 
        построенную на основе полученных данных и логику взаимодействия с API Binance.
    """

    PERCENT_ORDER = 0.01
    TIME_RANGE = 1


    def __init__(self, symbol, qnty=15):
        """ Конструктор класса Datafarm

            symbol (str): Тикер криптовалютной пары

            qnty (float): Объем ордера, по-умолчанию 15

            __open_position (bool): Состояние, в котором находится алгоритм. 
                                    Если нет открытой позиции, значение атрибута - False,
                                    если произошло событие signal_buy - True.

            __last_signal (str): Текстовое сообщение о торговом сигнале, передаваемое как 
                                уведомление в Telegram и в терминал.

            __last_log (str): Текстовое уведомление, логирующее работу алгоритма в состоянии
                            ожидания торгового сигнала.

            ** __last_signal и __last_log служат для предотвращения дублирования уведомлений
            при поступающих через вебсокеты идентичных данных.
        """
        self.symbol = symbol.upper()
        self.qnty = qnty
        self.data_file = f'{self.symbol}.csv'
        self.__open_position = False
        self.__last_signal = None
        self.__last_log = None


    def send_message(self, message: str):
        """ Уведомления в Telegram 
        """
        return requests.get(
            f'https://api.telegram.org/bot{TELETOKEN}/sendMessage', 
            params=dict(chat_id=CHAT_ID, text=message)
        )


    def calculate_quantity(self) -> float:
        """ Расчет объема ордера 
        """
        symbol_info = CLIENT.get_symbol_info(self.symbol)
        step_size = symbol_info.get('filters')[1]['stepSize']
        order_volume = self.qnty / self.last_price
        order_volume = round_step_size(order_volume, step_size)
        return order_volume
    

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
            result = round(((self.sell_price - self.buy_price) * self.calculate_quantity()), 2)
            message = f'{self.symbol} \n Sell \n {self.sell_price} \n Результат: {result} USDT'
            self.send_message(message)
            print(message)


    def create_frame(self, stream):
        """ Получение данных, сохранение их в виде таблицы в файл формата .csv
            чтение файла с данными и построение стратегии на основе полученных данных

            Структура таблицы файла .csv:
            
            Symbol (str): Название тикера
            Time (datetime): Время поступления данных
            Price (float): Значение цены тикера
            stream (dict): Данные, поступающие через вебсокеты
        """
        global closed

        df = pd.DataFrame(stream['data'], index=[0])
        df = df.loc[:,['s', 'E', 'p']]
        df.columns = ['Symbol', 'Time', 'Price']
        df.Time = pd.Series(pd.to_datetime(df.Time, unit='ms', utc=True)).dt.strftime('%Y-%m-%d %H:%M:%S')
        df.Price = round(df.Price.astype(float), round_list[f'{self.symbol}'])
        with open(self.data_file, 'a') as f:
            if os.stat(self.data_file).st_size == 0:
                df.to_csv(f, mode='a', header=True, index=False)
            else:
                df.to_csv(f, mode='a', header=False, index=False)
        df_csv = pd.read_csv(f'{self.symbol}.csv')
        df_csv.Time = pd.to_datetime(df_csv.Time)
        self.last_price = df_csv.Price.iloc[-1]
        time_period = df_csv[df_csv.Time > (df_csv.Time.iloc[-1] - pd.Timedelta(hours=self.TIME_RANGE))]
        
        signal_buy = round(
            (time_period.Price.min() + (time_period.Price.min() * self.PERCENT_ORDER)),
            self.round_float(num=self.last_price)
        )
        signal_sell = round(
            (time_period.Price.max() - (time_period.Price.max() * self.PERCENT_ORDER)),
            self.round_float(num=self.last_price)
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
            message = f'{self.symbol}: {self.last_price} {order_side}: {signal_buy}'
            if message != self.__last_log:
                print(self.__last_log)
                self.__last_log = message


        if not self.__open_position:
            if (self.last_price > signal_buy) \
                and (self.last_price < (signal_buy + (signal_buy * 0.001))):
                self.place_order('BUY')
                report_signal('BUY')
            else:
                report_log('BUY')

        if self.__open_position:
            if (self.last_price < signal_sell) \
                and (self.last_price > ((signal_sell - (signal_sell * 0.001)))) \
                or (self.last_price < time_period.Price.min()) \
                or closed:
                self.place_order('SELL')
                report_signal('SELL')
            else:
                report_log('SELL')


    def report_graph(self):
        df_gph = pd.read_csv(self.data_file)
        df_gph.Time = pd.to_datetime(df_gph.Time)
        df_gph = df_gph[df_gph.Time > (df_gph.Time.iloc[-1] - pd.Timedelta(hours=self.TIME_RANGE))]
        signal_buy_report = round(
            (df_gph.Price.min() + (df_gph.Price.min() * self.PERCENT_ORDER)),
            self.round_float(num=df_gph.Price.iloc[-1])
        )
        signal_sell_report = round(
            (df_gph.Price.max() - (df_gph.Price.max() * self.PERCENT_ORDER)),
            self.round_float(num=df_gph.Price.iloc[-1])
        )
        
        chart = go.Scatter(
            x=df_gph.Time, 
            y=df_gph.Price, 
            mode='lines', 
            line=dict(width=1), 
            marker=dict(color='blue')
        )
        layout = go.Layout(
            title=self.symbol,
            yaxis=dict(title='Цена', side='right', showgrid=False, zeroline=False),
            xaxis=dict(title='Время', showgrid=False, zeroline=False),
            shapes=[
                dict(
                    type='line',
                    yref='y',
                    y0=signal_buy_report if not self.__open_position else signal_sell_report,
                    y1=signal_buy_report if not self.__open_position else signal_sell_report,
                    xref='paper',
                    x0=0,
                    x1=1,
                    line=dict(color='green' if not self.__open_position else 'red'),
                )
            ],
            margin=gos.layout.Margin(l=40, r=0, t=40,b=30)
        )
        data = [chart]
        fig = go.Figure(data=data, layout=layout)
        fig.write_image(f"report.png")


    async def socket_stream(self):
        """ Подключение к потоку Binance через вебсокеты
        """
        global online
        bm = BinanceSocketManager(client=CLIENT)
        ts = bm.symbol_mark_price_socket(self.symbol, fast=False)
        async with ts as tscm:
            while online:
                res = await tscm.recv()
                if res:
                    self.create_frame(res)
                await asyncio.sleep(0)
            if not online:
                remove_file(self.data_file)
