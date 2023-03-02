import environs
from binance.client import Client
from sqlalchemy import create_engine

env = environs.Env()
env.read_env('.env')

# Binance API
CLIENT = Client(env('API_KEY'), env('SECRET_KEY'), {'verify': True, 'timeout': 20})
BALANCE = round(float(CLIENT.futures_account_balance()[6]['balance']), 2)
print(f'Баланс фьючерсного кошелька: {BALANCE}')

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
