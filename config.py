import environs
from sqlalchemy import create_engine
from binance.client import Client

env = environs.Env()
env.read_env('.env')

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

# Binance API
CLIENT = Client(env('API_KEY'), env('SECRET_KEY'), {'verify': True, 'timeout': 20})
ASSET_BALANCE = CLIENT.get_asset_balance(asset='USDT')
BALANCE_FREE = round(float(ASSET_BALANCE.get('free')), 1)
