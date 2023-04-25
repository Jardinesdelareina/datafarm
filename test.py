import asyncio, os
from datafarm.core import Datafarm

SYMBOL = 'XRPUSDT'
QNTY = 20
data_file = f'{SYMBOL}.csv'

""" loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    asyncio.run(Datafarm(SYMBOL,QNTY).socket_stream())
except KeyboardInterrupt:
    if os.path.exists(data_file):
        os.remove(data_file)
        print('Файл с данными торгов удален')
    else:
        print('Файл с данными торгов не был найден') """
