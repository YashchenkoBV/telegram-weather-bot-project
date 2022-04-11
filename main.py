from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
from data import db_session
from data.geolocation import User

TOKEN = '5278858507:AAFA_jQaFD8oSFzMqyp3G5e0mjqS-hYkwT4'
WEATHER_TOKEN = ''
current_area = ''
new_name = ''
current_name = ''
user_markup = ReplyKeyboardMarkup([['/registration', '/enter']], one_time_keyboard=False)
functional_markup = ReplyKeyboardMarkup([['/temperature', '/weather_conditions', '/weather', '/map'], ['change_city']])


def registration(update, context):
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
    functional(update, context)
    return ConversationHandler.END


def help(update, context):
    update.message.reply_text('Вы используете бот-метеоролог. Чтобы получить доступ ко всем функциям вам необходимо'
                              'пройти регистрацию или выполнить вход, если вы использовали бота ранее. После '
                              'этого вам будут доступны следующие функции: выбор города проживания (/change_city),'
                              'вывод температуры в городе проживания (/temperature), вывод погодных условий, а'
                              'именно влажности, скорости и направления ветра, атмосферного давления '
                              '(/weather_conditions), вывод всей информации о погоде (/weather), вывод метеокарты'
                              '(/map)')


def stop(update, context):
    update.message.reply_text('Действие отменено')
    return ConversationHandler.END


def start(update, context):
    update.message.reply_text('Добро пожаловать в бот-метеоролог! Чтобы начать '
                              'пройдите регистрацию или выполните вход', reply_markup=user_markup)

def functional(update, context):
    update.message.reply_text('Добро пожаловать!'
                              'Вам доступны следующие функции:', reply_markup=functional_markup)

def enter(update, context):
    update.message.reply_text('''Вы активировали процесс входа. Чтобы прервать последующий диалог,
    используйте команду /stop. Пожалуйста, введите свой никнейм''')
    return 1


def enter_name(update, context):
    global current_name
    current_name = update.message.text
    f = False

    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    for user in db_sess.query(User).all():
        if user.name == current_name:
            f = True
    if f:
        update.message.reply_text('Введите ваш пароль')
        return 2
    else:
        update.message.reply_text('Пользователь с таким именем не найден')
        current_name = ''
        return ConversationHandler.END


def enter_password(update, context):
    password = update.message.text
    f = False
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    for user in db_sess.query(User).all():
        if user.name == current_name and user.password == password:
            f = True
    if f:
        functional(update, context)
        return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    text_handler = MessageHandler(Filters.text, registration_name)
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    conv_handler1 = ConversationHandler(
        entry_points=[CommandHandler('registration', registration)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, registration_name)],
            2: [MessageHandler(Filters.text & ~Filters.command, registration_password)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler('enter', enter)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, enter_name)],
            2: [MessageHandler(Filters.text & ~Filters.command, enter_password)]
        },
        fallbacks=[CommandHandler('stop', stop)])

    dp.add_handler(conv_handler1)
    dp.add_handler(conv_handler2)
    dp.add_handler(text_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    db_session.global_init("db/cities.db")
    main()
