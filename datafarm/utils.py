import os
import requests
from datafarm.config_binance import CLIENT
from telegram.config_telegram import TELETOKEN, CHAT_ID

symbol_list = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 
    'DOTUSDT', 'LINKUSDT', 'ADAUSDT', 'SOLUSDT', 
    'MATICUSDT', 'UNIUSDT', 'NEARUSDT', 'AVAXUSDT',
]

round_list = {
    'BTCUSDT': 2, 'ETHUSDT': 2, 'BNBUSDT': 1, 'XRPUSDT': 4,
    'DOTUSDT': 3, 'LINKUSDT': 3, 'ADAUSDT': 4, 'SOLUSDT': 2,
    'MATICUSDT': 4, 'UNIUSDT': 3, 'NEARUSDT': 3, 'AVAXUSDT': 2,
}

interval_list = ['0.002', '0.005', '0.01']


def send_message(message: str):
    """ Уведомления в Telegram 
    """
    return requests.get(
        f'https://api.telegram.org/bot{TELETOKEN}/sendMessage', 
        params=dict(chat_id=CHAT_ID, text=message)
    )


def get_balance_ticker(ticker: str) -> float:
    """ Баланс определенной криптовалюты на спотовом кошельке Binance

        ticker (str): Тикер криптовалюты (базовой, без котируемой, в формате 'BTC', 'ETH' и т.д.)
        return (float): Количество заданной криптовалюты
    """
    asset_balance = CLIENT.get_asset_balance(ticker)
    if ticker == 'USDT':
        round_balance = 1
    else:
        round_balance = 4
    return round(float(asset_balance.get('free')), round_balance)


def round_float(num: float) -> int:
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


def remove_file(target_file):
    """ Удаление файла
    """
    if os.path.exists(target_file):
        os.remove(target_file)
        print(f'Файл {target_file} удален')
    else:
        print(f'Файл {target_file} не был найден')
