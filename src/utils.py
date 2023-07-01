import os
import requests
from src.config import TELETOKEN, CHAT_ID

symbol_list = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT']
round_list = {'BTCUSDT': 2, 'ETHUSDT': 2, 'BNBUSDT': 1, 'XRPUSDT': 4}

def send_message(message: str):
    return requests.get(
        f'https://api.telegram.org/bot{TELETOKEN}/sendMessage', 
        params=dict(chat_id=CHAT_ID, text=message)
    )

def round_float(num: float) -> int:
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
