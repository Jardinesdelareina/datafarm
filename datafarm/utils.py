import os
import requests
from datafarm.config_binance import CLIENT
from telegram.config_telegram import TELETOKEN, CHAT_ID

symbol_list = ['BTCTUSD', 'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', ]
round_list = {'BTCTUSD': 2, 'BTCUSDT': 2, 'ETHUSDT': 2, 'BNBUSDT': 1, 'XRPUSDT': 4,}


def send_message(message: str):
    """ Уведомление в Telegram 
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
    if ticker == 'USDT' or ticker == 'TUSD':
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
