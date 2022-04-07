from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
from data import db_session
from data.geolocation import User

TOKEN = '5278858507:AAFA_jQaFD8oSFzMqyp3G5e0mjqS-hYkwT4'
WEATHER_TOKEN = ''
current_area = ''
new_name = ''


def new(update, context):
    update.message.reply_text('''Вы активировали процесс регистрации. Чтобы прервать последующий диалог,
используйте команду /stop. Пожалуйста, введите свой никнейм''')
    return 1


def registration_name(update, context):
    global new_name
    new_name = update.message.text
    update.message.reply_text('Теперь придумайте пароль')
    return 2


def registration_password(update, context):
    password = update.message.text
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()

    user = User()
    user.name = new_name
    user.password = password
    user.latest_city = ''
    user.constant_city = ''
    db_sess.add(user)
    db_sess.commit()
    update.message.reply_text('Регистрация успешно завершена')
    return ConversationHandler.END


def help(update, context):
    update.message.reply_text('Какая-то помощь')


def registration_stop(update, context):
    update.message.reply_text('Регистрация отменена')
    return ConversationHandler.END


def start(update, context):
    update.message.reply_text('Какое-то приветствие')


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    text_handler = MessageHandler(Filters.text, registration_name)
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new_user', new)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, registration_name)],
            2: [MessageHandler(Filters.text & ~Filters.command, registration_password)]
        },
        fallbacks=[CommandHandler('stop', registration_stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(text_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    db_session.global_init("db/cities.db")
    main()
