from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Меню выбора тикера
symbol_kb = InlineKeyboardMarkup(row_width=2)
symbol_btc = InlineKeyboardButton(text='BTC', callback_data='BTCUSDT')
symbol_eth = InlineKeyboardButton(text='ETH', callback_data='ETHUSDT')
symbol_bnb = InlineKeyboardButton(text='BNB', callback_data='BNBUSDT')
symbol_xrp = InlineKeyboardButton(text='XRP', callback_data='XRPUSDT')
symbol_kb.row(symbol_btc, symbol_eth).row(symbol_bnb, symbol_xrp)

# Кнопка запуска алгоритма
start_kb = InlineKeyboardMarkup(row_width=1)
start_bot = InlineKeyboardButton(text='Старт', callback_data='start')
start_kb.add(start_bot)

# Кнопка остановки алгоритма: да/нет
stop_kb = InlineKeyboardMarkup(row_width=1)
stop_no = InlineKeyboardButton(text='Нет', callback_data='continue')
stop_yes = InlineKeyboardButton(text='Да', callback_data='stop')
stop_kb.row(stop_no, stop_yes)
