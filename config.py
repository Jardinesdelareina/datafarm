import environs

env = environs.Env()
env.read_env('.env')

USER = env('USER')
PASSWORD = env('PASSWORD')
HOST = env('HOST')
PORT = env('PORT')
DB_NAME = env('DB_NAME')
