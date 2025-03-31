import telebot
from config import API_TOKEN
from handlers import setup_handlers

bot = telebot.TeleBot(API_TOKEN)

setup_handlers(bot)

bot.polling(none_stop=True)