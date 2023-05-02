from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Меню выбора тикера
symbol_kb = InlineKeyboardMarkup(row_width=3)
symbol_btc = InlineKeyboardButton(text='BTC', callback_data='BTCUSDT')
symbol_eth = InlineKeyboardButton(text='ETH', callback_data='ETHUSDT')
symbol_bnb = InlineKeyboardButton(text='BNB', callback_data='BNBUSDT')
symbol_xrp = InlineKeyboardButton(text='XRP', callback_data='XRPUSDT')
symbol_ada = InlineKeyboardButton(text='ADA', callback_data='ADAUSDT')
symbol_dot = InlineKeyboardButton(text='DOT', callback_data='DOTUSDT')
symbol_matic = InlineKeyboardButton(text='MATIC', callback_data='MATICUSDT')
symbol_avax = InlineKeyboardButton(text='AVAX', callback_data='AVAXUSDT')
symbol_link = InlineKeyboardButton(text='LINK', callback_data='LINKUSDT')
symbol_sol = InlineKeyboardButton(text='SOL', callback_data='SOLUSDT')
symbol_near = InlineKeyboardButton(text='NEAR', callback_data='NEARUSDT')
symbol_uni = InlineKeyboardButton(text='UNI', callback_data='UNIUSDT')
symbol_kb.row(symbol_btc, symbol_eth, symbol_bnb, symbol_xrp,)\
        .row(symbol_ada, symbol_dot, symbol_matic, symbol_avax,)\
        .row(symbol_link, symbol_sol, symbol_near, symbol_uni)

# Меню выбора интервала
interval_kb = InlineKeyboardMarkup(row_width=1)
interval_low = InlineKeyboardButton(text='0.2 %', callback_data='0.002')
interval_medium = InlineKeyboardButton(text='0.5 %', callback_data='0.005')
interval_high = InlineKeyboardButton(text='1 %', callback_data='0.01')
interval_kb.row(interval_low, interval_medium, interval_high)

# Кнопка запуска алгоритма
start_kb = InlineKeyboardMarkup(row_width=1)
start_bot = InlineKeyboardButton(text='Старт', callback_data='start')
start_kb.add(start_bot)

# Кнопка остановки алгоритма: да/нет
stop_kb = InlineKeyboardMarkup(row_width=1)
stop_no = InlineKeyboardButton(text='Нет', callback_data='continue')
stop_yes = InlineKeyboardButton(text='Да', callback_data='stop')
stop_kb.row(stop_no, stop_yes)
