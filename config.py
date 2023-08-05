import environs
from sqlalchemy import create_engine
from binance.client import Client

env = environs.Env()
env.read_env('.env')

DEBUG = bool(int(env('DEBUG')))

# Binance API
CLIENT = Client(env('API_KEY'), env('SECRET_KEY'), {'verify': True, 'timeout': 20})

# Telegram API
TELETOKEN = env('TELETOKEN')
CHAT_ID = env('CHAT_ID')

# Database
DB_USER = env('DB_USER')
DB_PASS = env('DB_PASS')
DB_HOST = env('DB_HOST')
DB_PORT = env('DB_PORT')
DB_NAME = env('DB_NAME')
ENGINE = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
