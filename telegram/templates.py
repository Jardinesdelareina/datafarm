from datafarm.core import symbol_list, Datafarm

START = '''
<b>Главное меню</b>
Здесь вы можете ознакомиться с описанием проекта <b>Datafarm</b>, изучить инструкцию по работе с проектом, 
посмотреть баланс вашего спотового кошелька на бирже Binance или приступить к настройке алгоритма.
'''

DESCRIPTION = '''
Здравствуйте!
<em><b>Datafarm</b></em> - это инновационный проект, созданный для расширения возможностей трейдеров в мире криптовалют.
В нашем алгоритме нет привычных для многих технических индикаторов. Мы доверяем анализу другим способом, 
и теперь <em><b>Datafarm</b></em> успешно подвергается тестированию на спот-рынке биржи Binance. 
Мы создали интерфейс внутри телеграм-бота, позволяющий наблюдать за балансом вашего криптовалютного портфеля и 
находиться в курсе всех изменений в реальном времени. 
<em><b>Datafarm</b></em> предлагает выход за рамки обычных стратегий торговли на криптовалютном рынке.
Удачной охоты!
'''

HELP = '''
В данном разделе будет описан порядок работы с торговым алгоритмом <b>Datafarm</b>.
Для начала работы необходимо:
1. Перейти в раздел <em><b>Алгоритм</b></em> главного меню,
2. Выбрать криптовалютную пару (в меню представлены тикеры без валюты-знаменателя, она по-умолчанию USDT),
3. Ввести объем (в USDT), именно на эту сумму алгоритм будет работать (минимальный объем 15 USDT)

Если в процессе настройки вы хотите изменить свое решение о выборе тикера для торговли, вы можете вернуться
в начало настройки, набрав команду <em><b>'Отмена'</b></em>.

Если все данные введены верно, останется только активировать алгоритм, нажав кнопку <em><b>Старт</b></em>.

Если вы хотите остановить работу алгоритма, необходимо ввести текстовую команду <em><b>Стоп</b></em>. 

Остановка алгоритма означает окончание вашей торговой сессии. Следующая сессия начнется после перехода по ссылке 
<em><b>Алгоритм</b></em> и заполнения необходимых полей.
'''

balance_usdt = round(Datafarm.get_balance('USDT'), 1)
BALANCE = f'''
Здесь вы можете отслеживать состояние вашего криптовалютного портфеля:

USDT: <b>{balance_usdt}</b>\n
'''
for ticker in symbol_list:
    ticker_name = ticker.replace('USDT', '')
    balance = Datafarm.get_balance(ticker_name)
    if balance > 0:
        BALANCE += f'{ticker_name}: <b>{balance}</b>\n'

STATE_START = '''
Давайте приступим. 
Выберите криптовалютную пару, которую вы бы хотели подключить к алгоритму. 
Вы можете выбрать одну или все вместе.
'''
STATE_QNTY = f'''
<em>
Баланс USDT: <b>{balance_usdt}</b>
Введите объем в USDT:
</em>
'''
STATE_QNTY_TYPE_ERROR = '''
<em>
Некорректные данные. Пожалуйста, введите числовое значение:
</em>
'''
STATE_QNTY_MAX_VALUE_ERROR = f'''
<em>
Объем превышает размер депозита. Пожалуйста, введите сумму меньше <b>{balance_usdt}</b> USDT
</em>
'''
STATE_QNTY_MIN_VALUE_ERROR = f'''
<em>
Объем не должен быть меньше 15 USDT
</em>
'''
STATE_VALID_ERROR = '''
<em>
Данные заполнены неверно, попробуйте еще раз, пожалуйста.
</em>
'''
ORDER_EXCEPTION = '''
<em>
Торговля недоступна по техническим причинам. Приносим извинения за доставленные неудобства.
</em>
'''