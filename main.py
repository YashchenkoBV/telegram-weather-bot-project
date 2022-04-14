from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
from geopy import geocoders
from data import db_session
import requests
import json
from data.geolocation import User

TOKEN = '5278858507:AAFA_jQaFD8oSFzMqyp3G5e0mjqS-hYkwT4'
WEATHER_TOKEN = 'a911cb6b-7f4b-4b40-99b4-a1a8f235ad78'
current_area = ''
new_name = ''
current_name = ''
user_keyboard = [['/registration', '/enter']]
functions_keyboard = [['/advice', '/weather_conditions', '/weather', '/link'], ['change_city']]
user_markup = ReplyKeyboardMarkup(user_keyboard, one_time_keyboard=True)
functional_markup = ReplyKeyboardMarkup(functions_keyboard)


def registration(update, context):
    update.message.reply_text('''Вы активировали процесс регистрации. Чтобы прервать последующий диалог,
используйте команду /stop. Пожалуйста, введите свой никнейм''')
    return 1


def registration_name(update, context):
    global new_name
    new_name = update.message.text
    update.message.reply_text('Теперь придумайте пароль')
    return 2


def geolocation(city: str):
    geolocator = geocoders.Nominatim(user_agent="telebot")
    latitude = str(geolocator.geocode(city).latitude)
    longitude = str(geolocator.geocode(city).longitude)
    return latitude, longitude


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
    update.message.reply_text('Вы используете бот-метеоролог. Чтобы получить доступ ко всем функциям вам необходимо'
                              'пройти регистрацию или выполнить вход, если вы использовали бота ранее. После '
                              'этого вам будут доступны следующие функции: выбор города (/change_city),'
                              'вывод краткой информации о погоде в выбранном городе (/weather),'
                              'вывод подробной информации о погоде (/weather_conditions),'
                              'совет о том, что надеть в такую погоду (/advice),'
                              'ссылка на сайт Яндекс.Погоды, где можно найти более'
                              'подробную информацию и метеокарту (/link)')


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
    global current_name
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
    else:
        update.message.reply_text('Вы ввели неверный пароль. Пожалуйста, войдите в систему заново',
                                  reply_markup=user_markup)
        return ConversationHandler.END


def yandex_weather(latitude, longitude, token):
    url_yandex = f'https://api.weather.yandex.ru/v2/informers?lat={latitude}&lon={longitude}&[lang=ru_RU]'
    yandex_req = requests.get(url_yandex, headers={'X-Yandex-API-Key': token}, verify=True)

    conditions = {'clear': 'ясно', 'partly-cloudy': 'малооблачно', 'cloudy': 'облачно с прояснениями',
                  'overcast': 'пасмурно', 'drizzle': 'морось', 'light-rain': 'небольшой дождь',
                  'rain': 'дождь', 'moderate-rain': 'умеренно сильный', 'heavy-rain': 'сильный дождь',
                  'continuous-heavy-rain': 'длительный сильный дождь', 'showers': 'ливень',
                  'wet-snow': 'дождь со снегом', 'light-snow': 'небольшой снег', 'snow': 'снег',
                  'snow-showers': 'снегопад', 'hail': 'град', 'thunderstorm': 'гроза',
                  'thunderstorm-with-rain': 'дождь с грозой', 'thunderstorm-with-hail': 'гроза с градом'
                  }

    wind_dir = {'nw': 'северо-западное', 'n': 'северное', 'ne': 'северо-восточное', 'e': 'восточное',
                'se': 'юго-восточное', 's': 'южное', 'sw': 'юго-западное', 'w': 'западное', 'с': 'штиль'}

    season = {'summer': 'лето', 'autumn': 'осень', 'winter': 'зима', 'spring': 'весна'}
    yandex_json = json.loads(yandex_req.text)
    yandex_json['fact']['condition'] = conditions[yandex_json['fact']['condition']]
    yandex_json['fact']['wind_dir'] = wind_dir[yandex_json['fact']['wind_dir']]
    for parts in yandex_json['forecast']['parts']:
        parts['condition'] = conditions[parts['condition']]
        parts['wind_dir'] = wind_dir[parts['wind_dir']]

    weather = dict()
    params = ['condition', 'wind_dir', 'pressure_mm', 'humidity']
    for parts in yandex_json['forecast']['parts']:
        weather[parts['part_name']] = dict()
        weather[parts['part_name']]['temp'] = parts['temp_avg']
        for param in params:
            weather[parts['part_name']][param] = parts[param]

    weather['fact'] = dict()
    weather['fact']['temp'] = yandex_json['fact']['temp']
    for param in params:
        weather['fact'][param] = yandex_json['fact'][param]

    weather['link'] = yandex_json['info']['url']
    print(weather)
    return weather


def print_weather(dict_weather_yandex, update, context):
    global current_area

    day = {'night': 'ночью', 'morning': 'утром', 'day': 'днем', 'evening': 'вечером', 'fact': 'сейчас'}
    update.message.reply_text(f'Погода в городе {current_area} на данный момент:\n'
                              f'Температура: {dict_weather_yandex["fact"]["temp"]}\n'
                              f'Направление ветра {dict_weather_yandex["fact"]["wind_dir"]}\n'
                              f'Влажность воздуха: {dict_weather_yandex["fact"]["humidity"]}%')


def main_weather(update, context):
    global current_area
    global WEATHER_TOKEN

    print('работает 1')
    current_area = update.message.text
    latitude, longitude = geolocation(current_area)
    print(latitude, longitude)
    yandex_weather_x = yandex_weather(latitude, longitude, WEATHER_TOKEN)
    print_weather(yandex_weather_x, update, context)


def weather(update, context):
    update.message.reply_text('Хотите узнать погоду? Введите название интересующего города:')
    return 1


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
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
    conv_handler3 = ConversationHandler(
        entry_points=[CommandHandler('weather', weather)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, main_weather)]
        },
        fallbacks=[CommandHandler('stop', stop)])
    dp.add_handler(conv_handler1)
    dp.add_handler(conv_handler2)
    dp.add_handler(conv_handler3)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    db_session.global_init("db/cities.db")
    main()
