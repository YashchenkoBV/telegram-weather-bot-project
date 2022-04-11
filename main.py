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


def registration(update, context):
    update.message.reply_text('''Вы активировали процесс регистрации. Чтобы прервать последующий диалог,
используйте команду /stop. Пожалуйста, введите свой никнейм''')
    return 'A'


'''def registration_name(update, context):
    global new_name
    new_name = update.message.text
    update.message.reply_text('Теперь придумайте пароль')
    return 'B'''


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
    update.message.reply_text('Какая-то помощь')


def stop(update, context):
    update.message.reply_text('Действие отменено')
    return ConversationHandler.END


def start(update, context):
    update.message.reply_text('Какое-то приветствие')


def enter(update, context):
    update.message.reply_text('''Вы активировали процесс входа. Чтобы прервать последующий диалог,
    используйте команду /stop. Пожалуйста, введите свой никнейм''')
    return 3


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
        return 4
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
        update.message.reply_text('Добро пожаловать!')
        return ConversationHandler.END
    else:
        update.message.reply_text('Пользователь с таким именем не найден')
        current_name = ''
        return ConversationHandler.END


def yandex_weather(latitude, longitude, WEATHER_TOKEN):
    url_yandex = f'https://api.weather.yandex.ru/v2/informers/?lat={latitude}&lon={longitude}&[lang=ru_RU]'
    yandex_req = requests.get(url_yandex, headers={'X-Yandex-API-Key': WEATHER_TOKEN}, verify=False)

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
    print('работает 2')
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
    return weather


def print_yandex_weather(dict_weather_yandex, update, context):
    day = {'night': 'ночью', 'morning': 'утром', 'day': 'днем', 'evening': 'вечером', 'fact': 'сейчас'}
    update.message.reply_text(f'А яндекс говорит:')
    for i in dict_weather_yandex.keys():
        if i != 'link':
            time_day = day[i]
            update.message.reply_text(f'Температура {time_day} {dict_weather_yandex[i]["temp"]}'
                                      f', на небе {dict_weather_yandex[i]["condition"]}')

    update.message.reply_text(f'Подробности смотрите тут: '
                              f'{dict_weather_yandex["link"]}')


def main_weather(update, context):
    print('работает 1')
    city = update.message.text
    latitude, longitude = geolocation(city)
    yandex_weather_x = yandex_weather(latitude, longitude, WEATHER_TOKEN)
    print_yandex_weather(yandex_weather_x, update, context)


def weather(update, context):
    update.message.reply_text('Хотите узнать погоду? Введите название интересующего города:')
    return 1


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    '''conv_handler1 = ConversationHandler(
        entry_points=[CommandHandler('registration', registration)],
        states={
            'A': [MessageHandler(Filters.text & ~Filters.command, registration_name)],
            'B': [MessageHandler(Filters.text & ~Filters.command, registration_password)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )'''
    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler('enter', enter)],
        states={
            3: [MessageHandler(Filters.text & ~Filters.command, enter_name)],
            4: [MessageHandler(Filters.text & ~Filters.command, enter_password)]
        },
        fallbacks=[CommandHandler('stop', stop)])
    conv_handler3 = ConversationHandler(
        entry_points=[CommandHandler('weather', weather)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, main_weather)]
        },
        fallbacks=[CommandHandler('stop', stop)])
    # dp.add_handler(conv_handler1)
    dp.add_handler(conv_handler2)
    dp.add_handler(conv_handler3)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    db_session.global_init("db/cities.db")
    main()
