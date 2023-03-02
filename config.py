import environs, json
from binance.um_futures import UMFutures
from sqlalchemy import create_engine

env = environs.Env()
env.read_env('.env')

# Binance API
CLIENT = UMFutures(env('API_KEY'), env('SECRET_KEY'))

GENERAL_BALANCE = round(float(CLIENT.balance()[6]['balance']), 2)
AVAILABLE_BALANCE = round(float(CLIENT.balance()[6]['availableBalance']), 2)
print(f'Общий баланс: {GENERAL_BALANCE}')
print(f'Свободные средства: {AVAILABLE_BALANCE}')

TRADES = CLIENT.get_account_trades(symbol='XRPUSDT')
#print(json.dumps(TRADES, indent=4, sort_keys=True))

INFO = CLIENT.exchange_info()
#print(json.dumps(INFO, indent=4, sort_keys=True))

# Database
USER = env('USER')
PASSWORD = env('PASSWORD')
HOST = env('HOST')
PORT = env('PORT')
DB_NAME = env('DB_NAME')
ENGINE = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}')

# Telegram API
TELETOKEN = env('TELETOKEN')
CHAT_ID = env('CHAT_ID')
