from sqlalchemy import create_engine
from config import USER, PASSWORD, HOST, PORT, DB_NAME

ENGINE = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}')
