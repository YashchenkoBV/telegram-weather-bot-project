from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup
from data import db_session
from data.geolocation import User

TOKEN = '5278858507:AAFA_jQaFD8oSFzMqyp3G5e0mjqS-hYkwT4'
WEATHER_TOKEN = ''
current_area = ''


def new(update, context):
    pass


def registration(update, context):
    pass


def help(update, context):
    update.message.reply_text('Какая-то помощь')


def start(update, context):
    update.message.reply_text('Какое-то приветствие')


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    text_handler = MessageHandler(Filters.text, registration)
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('new_user', new))
    dp.add_handler(text_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    db_session.global_init("db/cities.db")
    main()