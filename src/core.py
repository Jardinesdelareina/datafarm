import os
import time
import asyncio
import pandas as pd
import plotly.graph_objects as go
import plotly.graph_objs as gos
from binance import BinanceSocketManager
from binance.exceptions import BinanceAPIException as bae
from binance.helpers import round_step_size
from src.config import CLIENT, DEBUG
from src.utils import send_message, remove_file, round_float, round_list

online = True


def bot_off():
    """ Остановка алгоритма
    """
    global online
    online = False


def start_single_bot(symbol, qnty=50):
    """ Запуск алгоритма
    """
    global online
    online = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(Datafarm(symbol, qnty).socket_stream())


class Datafarm:

    # Наличие открытой позиции в рынке
    OPEN_POSITION = False

    # Рабочий временной диапазон
    TIME_RANGE = 1

    # Дистанция от экстремума
    MIN_INTERVAL = 0.002

    def __init__(self, symbol, qnty):
        """ Конструктор класса Datafarm

            symbol (str): Тикер криптовалютной пары

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


    def calculate_quantity(self) -> float:
        """ Расчет объема ордера 
        """
        symbol_info = CLIENT.get_symbol_info(self.symbol)
        step_size = symbol_info.get('filters')[1]['stepSize']
        order_volume = self.qnty / self.last_price
        return round_step_size(order_volume, step_size)


    def place_order(self, order_side: str):
        """ Размещение ордеров
            
            order_side (str): Направление ордера, передаваемое при вызове функции в алгоритме
        """

        if order_side == 'BUY':
            order = None if DEBUG else CLIENT.create_order(
                symbol=self.symbol, 
                side='BUY', 
                type='MARKET', 
                quantity=self.calculate_quantity(),
            )
            remove_file(self.data_file)
            self.__class__.OPEN_POSITION = True
            self.buy_price = round(
                float(order.get('fills')[0]['price']), 
                round_float(num=self.last_price)
            )
            message = f'{self.symbol} \n Buy \n {self.buy_price}'
            send_message(message)
            print(message)

        if order_side == 'SELL':
            order = None if DEBUG else CLIENT.create_order(
                symbol=self.symbol, 
                side='SELL', 
                type='MARKET', 
                quantity=self.calculate_quantity(),
            )
            remove_file(self.data_file)
            self.__class__.OPEN_POSITION = False
            self.sell_price = round(
                float(order.get('fills')[0]['price']), 
                round_float(num=self.last_price)
            )
            result = round(((self.sell_price - self.buy_price) * self.calculate_quantity()), 2)
            message = f'{self.symbol} \n Sell \n {self.sell_price} \n Результат: {result} USDT'
            send_message(message)
            print(message)


    def create_frame(self, stream):
        """ Получение данных, сохранение их в виде таблицы в файл формата .csv,
            чтение файла с данными и построение стратегии на основе полученных данных

            Структура таблицы файла .csv:
            
            Symbol (str): Название тикера
            Time (datetime): Время поступления данных
            Bid (float): Цена Bid
            Ask (float):Цена Ask
            stream (dict): Данные, поступающие через вебсокеты
        """

        # Запись
        df = pd.DataFrame([stream])
        df = df.loc[:,['s', 'E', 'b', 'a']]
        df.columns = ['Symbol', 'Time', 'Bid', 'Ask']
        df.Time = pd.Series(pd.to_datetime(df.Time, unit='ms', utc=True)).dt.strftime('%Y-%m-%d %H:%M:%S')
        for column in ['Bid', 'Ask']:
            df[column] = round(df[column].astype(float), round_list[f'{self.symbol}'])
        with open(self.data_file, 'a') as f:
            if os.stat(self.data_file).st_size == 0:
                df.to_csv(f, mode='a', header=True, index=False)
            else:
                df.to_csv(f, mode='a', header=False, index=False)
        
        # Чтение
        df_csv = pd.read_csv(self.data_file)
        df_csv.Time = pd.to_datetime(df_csv.Time)

        # Фильтр и сохраниение данных за определенный период
        time_period = df_csv[df_csv.Time > (df_csv.Time.iloc[-1] - pd.Timedelta(hours=self.TIME_RANGE))]
        time_period_df = time_period.to_csv(self.data_file, mode='w', header=True, index=False)
        
        self.last_price = round(
            ((time_period_df.Bid.iloc[-1] + time_period_df.Ask.iloc[-1]) / 2), 
            round_list[f'{self.symbol}']
        )


        def get_interval():
            """ Расчитывает интервал для сигнала: 
                либо четверть от диапазона, 
                либо MIN_INTERVAL, если он больше
            """
            quarter_time_range = ((time_period_df.Bid.max() - time_period_df.Ask.min()) / 4) / self.last_price
            quarter_time_range = round(quarter_time_range, 3)
            return quarter_time_range if quarter_time_range > self.MIN_INTERVAL else self.MIN_INTERVAL


        signal_buy = round(
            (time_period_df.Ask.min() + (time_period_df.Ask.min() * get_interval())),
            round_float(num=self.last_price)
        )
        signal_sell = round(
            (time_period_df.Bid.max() - (time_period_df.Bid.max() * get_interval())),
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
            signal = signal_buy if not self.__class__.OPEN_POSITION else signal_sell
            message = f'''
            {self.symbol}: {self.last_price}
            {order_side}: {signal}
            INTERVAL: {get_interval() * 100}
            '''
            if message != self.__last_log:
                print(message)
                self.__last_log = message


        if not self.__class__.OPEN_POSITION:
            if self.last_price > signal_buy:
                self.place_order('BUY')
                report_signal('BUY')
            else:
                report_log('BUY')

        if self.__class__.OPEN_POSITION:
            if self.last_price < signal_sell:
                self.place_order('SELL')
                report_signal('SELL')
            else:
                report_log('SELL')


    def report_graph(self):
        """ Визуализация определенных данных и сигналов на вход в рынок
        """
        df_gph = pd.read_csv(self.data_file)
        df_gph.Time = pd.to_datetime(df_gph.Time)
        df_gph = df_gph[df_gph.Time > (df_gph.Time.iloc[-1] - pd.Timedelta(hours=self.TIME_RANGE))]
        gph_last_price = round(((df_gph.Bid.iloc[-1] + df_gph.Ask.iloc[-1]) / 2), round_list[f'{self.symbol}'])
        

        def get_interval():
            """ Расчитывает интервал для сигнала: либо четверть от диапазона, 
                либо MIN_INTERVAL, если он больше
            """
            quarter_time_range = ((df_gph.Bid.max() - df_gph.Ask.min()) / 4) / gph_last_price
            quarter_time_range = round(quarter_time_range, 3)
            return quarter_time_range if quarter_time_range > self.MIN_INTERVAL else self.MIN_INTERVAL
        

        signal_buy_report = round(
            (df_gph.Ask.min() + (df_gph.Ask.min() * get_interval())),
            round_float(num=gph_last_price)
        )
        signal_sell_report = round(
            (df_gph.Bid.max() - (df_gph.Bid.max() * get_interval())),
            round_float(num=gph_last_price)
        )
        signal_line = signal_buy_report if not self.__class__.OPEN_POSITION else signal_sell_report
        chart = go.Scatter(
            x=df_gph.Time, 
            y=df_gph.Bid,
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
        ts = bm.symbol_ticker_socket(self.symbol)
        async with ts as tscm:
            while online:
                res = await tscm.recv()
                if res:
                    try:
                        self.create_frame(res)
                    except bae:
                        print('Binance API Exception')
                        time.sleep(5)
                        self.create_frame(res)
                    except KeyboardInterrupt:
                        online = False
                await asyncio.sleep(0)
            if not online:
                remove_file(self.data_file)
