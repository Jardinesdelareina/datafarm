import threading, os
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import StatesGroup, State
from datafarm.core import start_single_bot, bot_off, bot_closed, Datafarm
from datafarm.utils import symbol_list, get_balance_ticker, remove_file
from telegram.config_telegram import bot, CHAT_ID
from telegram.templates import *
from telegram.keyboards.kb_trading import *
from telegram.keyboards.kb_welcome import main_kb


class TradeStateGroup(StatesGroup):
    """ Состояние параметров: криптовалютные пары, объем ордеров, старт/остановка алгоритма
    """
    symbol = State()
    qnty = State()
    start = State()
    stop = State()


async def get_trading(message: types.Message):
    """ Пункт 'Алгоритм' главного меню, предлагает начать настройку параметров
        с выбора криптовалютных пар, начинает цикл стейта 
    """
    await TradeStateGroup.symbol.set()
    await bot.send_message(
        chat_id=CHAT_ID, 
        text=STATE_START, 
        parse_mode="HTML", 
        reply_markup=symbol_kb
    )
    await message.delete()


async def cancel_handler(message: types.Message, state: FSMContext):
    """ Отменяет действия, сбрасывает стейт 
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await bot.send_message(chat_id=CHAT_ID, text='\U0001F519 Отменено')


async def symbol_callback(callback: types.CallbackQuery, state: FSMContext):
    """ Сохраняет тикер в стейт, предлагает список интервалов 
    """
    async with state.proxy() as data:
        if callback.data in symbol_list:
            data['symbol'] = callback.data
            await TradeStateGroup.next()
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_QNTY, 
                parse_mode="HTML", 
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await state.finish()
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_VALID_ERROR,
                parse_mode="HTML",
                reply_markup=main_kb
            )            


async def qnty_message(message: types.Message, state: FSMContext):
    """ Введенный объем проходит валидацию (числовое ли значение и меньше ли баланса),
        сохраняется в стейт, выводит всю информацию из стейта и предлагает кнопку старта алгоритма
    """
    async with state.proxy() as data:
        quantity = message.text
        try:
            quantity_float = float(quantity)
        except:
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_QNTY_TYPE_ERROR, 
                parse_mode="HTML"
            )
            quantity_float = float(quantity)

        if quantity_float < 15:
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_QNTY_MIN_VALUE_ERROR, 
                parse_mode="HTML"
            )
            await TradeStateGroup.previous()
        elif get_balance_ticker('USDT') - quantity_float > 0:
            data['qnty'] = quantity_float
        else:
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_QNTY_MAX_VALUE_ERROR, 
                parse_mode="HTML"
            )
            await TradeStateGroup.previous()
        
        await TradeStateGroup.next()
        symbol = data['symbol']
        qnty = data['qnty']
        STATE_RESULT = f'\U00002705 Сверим данные \n Тикер: {symbol} \n Объем USDT: {qnty}'
        await bot.send_message(
            chat_id=CHAT_ID, 
            text=STATE_RESULT,
            reply_markup=start_kb
        )


async def start_callback(callback: types.CallbackQuery, state: FSMContext):
    """ Сохраняет в стейт коллбэк 'start' и запускает алгоритм - в зависимости от параметров
        вызывается экземпляр определенного алгоритма с параметрами из стейта 
    """
    async with state.proxy() as data:
        try:
            data['start'] = callback.data
            if data['start'] == 'start':
                def work():
                    start_single_bot(data['symbol'], data['qnty'])
                thread_work = threading.Thread(target=work)
                thread_work.start()

                await TradeStateGroup.next()
                STATE_START = '\U0001F3C1 Datafarm начал свою работу'
                await callback.answer(STATE_START)
                await bot.send_message(
                    chat_id=CHAT_ID, 
                    text=STATE_START,
                )
        except:
            await state.finish()
            print('Ошибка старта')
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=ORDER_EXCEPTION,
                parse_mode="HTML",
                reply_markup=main_kb
            )


async def manage_message(message: types.Message, state: FSMContext):
    """ Остановка алгоритма при вводе команды 'Стоп',
        продажа по рынку при вводе команды 'Продать',
        вывод графического отчета о положении цены при вводе команды 'Отчет'
    """
    async with state.proxy() as data:
        if message.text == 'Стоп':
            STATE_STOP_MESSAGE = f'\U0001F6D1 Вы действительно хотите остановить Datafarm?'
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_STOP_MESSAGE, 
                reply_markup=stop_kb
            )
            await message.delete()
        elif message.text == 'Продать':
            trade_symbol = data['symbol']
            try:
                bot_closed()
                print('Closed')
                await TradeStateGroup.last()
                STATE_CLOSED = f'Совершена ручная продажа по {trade_symbol}'
                await bot.send_message(
                    chat_id=CHAT_ID, 
                    text=STATE_CLOSED
                )
                await message.delete()
            except:
                await bot.send_message(
                    chat_id=CHAT_ID, 
                    text=CLOSE_EXCEPTION,
                    parse_mode="HTML"
                )
                await message.delete()
        if message.text == 'Отчет':
            report = Datafarm(data['symbol'], data['qnty'])
            report.report_graph()
            print('Отчет')
            with open('report.png', 'rb') as photo:
                await bot.send_photo(
                    CHAT_ID, 
                    photo=types.InputFile(photo), 
                    caption='\U0001F4C3 Последний отчет'
                )
            await message.delete()


async def stop_callback(callback: types.CallbackQuery, state: FSMContext):
    """ Коллбэк, обрабатывающий кнопки контрольного вопроса: 
        либо отключает алгоритм, либо продолжает его работу 
    """
    async with state.proxy() as data:
        data['stop'] = callback.data
        if data['stop'] == 'continue':
            STATE_CONTINUE = '\U0001F503 Datafarm продолжает работу' 
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_CONTINUE,
            )
        elif data['stop'] == 'stop':
            bot_off()
            STATE_STOP = '\U0001F3C1 Datafarm закончил свою работу'
            print('Datafarm Stop')
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=STATE_STOP, 
                reply_markup=main_kb
            )
            remove_file('report.png')
            await state.finish()


def register_handlers_trading(dp: Dispatcher):
    dp.register_message_handler(get_trading, text='Алгоритм', state=None)
    dp.register_message_handler(cancel_handler, state="*", text='Отмена')
    dp.register_message_handler(cancel_handler, Text(equals='Отмена', ignore_case=True), state="*")
    dp.register_callback_query_handler(symbol_callback, state=TradeStateGroup.symbol)
    dp.register_message_handler(qnty_message, state=TradeStateGroup.qnty)
    dp.register_callback_query_handler(start_callback, state=TradeStateGroup.start)
    dp.register_message_handler(manage_message, state="*")
    dp.register_callback_query_handler(stop_callback, state=TradeStateGroup.stop)
