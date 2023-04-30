import json
import pandas as pd
from datafarm.config_binance import CLIENT

def top_coin():
    """ Получение тикера с максимальным показателем priceChangePercent за 24 часа
    """
    all_tickers = pd.DataFrame(CLIENT.get_ticker())
    usdt = all_tickers[all_tickers.symbol.str.contains('USDT')]
    work = usdt[~((usdt.symbol.str.contains('UP')) | (usdt.symbol.str.contains('DOWN')))]
    top_coin = work[work.priceChangePercent == work.priceChangePercent.max()]
    top_coin = top_coin.symbol.values[0]
    return top_coin

#print(top_coin())

def balance_ticker_list() -> list:
    """ Создание списка тикеров для баланса
    """
    all_tickers = pd.DataFrame(CLIENT.get_all_tickers())
    return all_tickers[all_tickers.symbol.str.endswith('USDT')].symbol.tolist()

#print(balance_ticker_list())

def balance():
    get_balance = CLIENT.get_account()
    balances = [{'asset': item['asset'], 'free': float(item['free'])} for item in get_balance['balances']]
    balances = sorted(filter(lambda item: item['free'] > 0, balances), key=lambda item: -item['free'])
    print(balances)


balance()