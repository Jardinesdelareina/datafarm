from aiogram import executor
from telegram.config_telegram import dp
from telegram.handlers import welcome

async def on_startup(_):
    print('Online')

welcome.register_handlers_welcome(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
