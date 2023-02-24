from binance.um_futures import UMFutures
import environs

env = environs.Env()
env.read_env('.env')

# Database
USER = env('USER')
PASSWORD = env('PASSWORD')
HOST = env('HOST')
PORT = env('PORT')
DB_NAME = env('DB_NAME')

# Binance API
CLIENT = UMFutures(env('API_KEY'), env('SECRET_KEY'))
GENERAL_BALANCE = round(float(CLIENT.balance()[6]['balance']), 2)
AVAILABLE_BALANCE = round(float(CLIENT.balance()[6]['availableBalance']), 2)
