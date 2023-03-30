import pandas as pd
from config import CLIENT, INFO
    

def get_top_coin():
    """ 
    Выбор из всех фьючерсов Binance тикера с максимальным изменением цены за 24 часа. 
    
    Удаление из выборки тикеров валют-знаменателей, отличных от USDT,
    сохранение в список тикеров, у которых в json-словаре есть ключ 'priceChangePercent'
    и вывод тикера с его максимальным значением.  
    """
    symbol_list = list(symbol['symbol'] for symbol in INFO['symbols'])
    df = pd.DataFrame(symbol_list, columns=['symbol'])
    df = df[~(df.symbol.str.contains('BULL|BEAR'))]
    df = df[~(df.symbol.str.contains('BUSD|USDC'))]
    df = df[df.symbol.str.contains('USDT')]
    all_tickers = df['symbol'].to_list()
    tickers_with_price_change_percent = []
    for ticker in all_tickers:
        ticker_data = CLIENT.ticker_24hr_price_change(ticker)
        if 'priceChangePercent' in ticker_data:
            tickers_with_price_change_percent.append(ticker)
        elif not tickers_with_price_change_percent:
            return None
    top_coin = max(
        tickers_with_price_change_percent, 
        key=lambda ticker: CLIENT.ticker_24hr_price_change(ticker)['priceChangePercent']
    )
    return top_coin       
    