from datafarm.config_binance import CLIENT

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
