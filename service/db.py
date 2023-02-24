from sqlalchemy import create_engine
from config_binance import USER, PASSWORD, HOST, PORT, DB_NAME

# Подключение к PostgreSQL 
ENGINE = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}')

def create_db():
    try:
        ENGINE.execute("CREATE DATABASE datafarm")
        print('База данных успешно создана')
    except Exception as e:
        print('Ошибка при создании базы данных')
        raise e
    
def drop_db():
    try:
        ENGINE.execute("DROP DATABASE datafarm")
        print('База данных успешно удалена')
    except Exception as e:
        print('Ошибка при удалении базы данных')
        raise e
