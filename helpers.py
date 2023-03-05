from decimal import Decimal
from typing import Union

# Тикеры фьючерсов Binance
symbol_list = [
    #'btcusdt', 'ethusdt', 'bnbusdt', 'xrpusdt', 'dotusdt', 'linkusdt', 'xtzusdt', 
    #'adausdt', 'solusdt', 'maticusdt', 'avaxusdt', 'uniusdt', 'trxusdt', 'xlmusdt',
    'vetusdt'#, 'axsusdt', 'zilusdt', 'dogeusdt', 'nearusdt', 'aaveusdt', 'ltcusdt',
]

# Округление qnty до определенного размера шага
def round_step_size(quantity: Union[float, Decimal], step_size: Union[float, Decimal]) -> float:
    quantity = Decimal(str(quantity))
    return float(quantity - quantity % Decimal(str(step_size)))

# Расчет количества знаков после запятой у числа типа float
def round_float(num: float) -> int:
    num_str = str(num)
    counter = 0
    for i in num_str[::-1]:
        if i == '.':
            break
        else:
            counter += 1
    return counter
