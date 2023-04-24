from datafarm.config_binance import CLIENT

symbol_list = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT',
    'ADAUSDT', 'SOLUSDT', 'MATICUSDT', 'UNIUSDT', 'NEARUSDT', 'AVAX'
]


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
    balance_free = round(float(asset_balance.get('free')), round_balance)
    return balance_free
