# Тикеры фьючерсов Binance
symbol_list = [
    #'btcusdt', 'ethusdt', 'bnbusdt', 'xrpusdt', 'dotusdt', 'linkusdt', 'xtzusdt', 
    #'adausdt', 'solusdt', 'maticusdt', 'avaxusdt', 'uniusdt', 'trxusdt', 'xlmusdt',
    'vetusdt'#, 'axsusdt', 'zilusdt', 'dogeusdt', 'nearusdt', 'aaveusdt', 'ltcusdt',
]

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
