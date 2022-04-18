from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
from geopy import geocoders
from data import db_session
import requests
import json
from data.geolocation import User

TOKEN = '5278858507:AAFA_jQaFD8oSFzMqyp3G5e0mjqS-hYkwT4'
WEATHER_TOKEN = 'a911cb6b-7f4b-4b40-99b4-a1a8f235ad78'
current_name = ''
user_keyboard = [['/registration', '/enter']]
functions_keyboard = [['/weather', '/conditions', '/advice'], ['/help', '/change', '/link'], ['/quit']]
user_markup = ReplyKeyboardMarkup(user_keyboard, one_time_keyboard=True)
functional_markup = ReplyKeyboardMarkup(functions_keyboard)


# Процесс регистрации
def registration(update, context):
    if context.user_data['main_flag']:
        update.message.reply_text('Вы активировали процесс регистрации. Чтобы прервать последующий диалог,'
                                  'используйте команду /stop. Пожалуйста, введите свой никнейм')
        context.userdata['main_flag'] = False
        return 1
    else:
        update.message.reply_text('Сначала завершите предыдущую задачу')


def registration_name(update, context):
    context.user_data['new_name'] = update.message.text
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    if context.user_data['new_name'] == '---':
        update.message.reply_text('Пожалуйста, придумайте другое имя')
        return 1
    for user in db_sess.query(User).all():
        if user.name == context.user_data['new_name']:
            update.message.reply_text('Пользователь с таким именем уже существет. '
                                      'Пожалуйста, придумайте другое')
            return 1
    update.message.reply_text('Теперь придумайте пароль')
    return 2


# Находим координаты введенного города
def geolocation(city: str):
    geolocator = geocoders.Nominatim(user_agent="telebot")
    latitude = str(geolocator.geocode(city).latitude)
    longitude = str(geolocator.geocode(city).longitude)
    return latitude, longitude


def registration_password(update, context):
    password = update.message.text
    context.user_data['password'] = password
    update.message.reply_text('Отлично, все почти готово. '
                              'Теперь введите Ваш город проживания')
    return 3


def registration_city(update, context):
    context.user_data['main_flag'] = True
    city = update.message.text
    db_session.global_init("db/cities.db")
    db_sess = db_session.create_session()

    user = User()
    user.name = context.user_data['new_name']
    user.password = context.user_data['password']
    user.constant_city = city
    db_sess.add(user)
    db_sess.commit()
    update.message.reply_text('Регистрация успешно пройдена!')
    return ConversationHandler.END


def help(update, context):
    if context.user_data['main_flag']:
        update.message.reply_text('Вы используете бот-метеоролог. Чтобы получить доступ ко всем функциям вам необходимо'
                                  'пройти регистрацию или выполнить вход, если вы использовали бота ранее. После '
                                  'этого вам будут доступны следующие функции: выбор города (/change_city),'
                                  'вывод краткой информации о погоде в выбранном городе (/weather),'
                                  'вывод подробной информации о погоде (/conditions),'
                                  'совет о том, что надеть в такую погоду (/advice),'
                                  'ссылка на сайт Яндекс.Погоды, где можно найти более'
                                  'подробную информацию и метеокарту (/link).'
                                  'Для отмены действия воспользуйтесь командой /stop')
    else:
        update.message.reply_text('Сначала завершите предыдущую задачу')


# Прерывание любого диалога
def stop(update, context):
    context.user_data['main_flag'] = True
    update.message.reply_text('Действие отменено')
    return ConversationHandler.END


def start(update, context):
    context.user_data['main_flag'] = True
    context.user_data['name'] = '---'
    update.message.reply_text('Добро пожаловать в бот-метеоролог! Чтобы начать '
                              'пройдите регистрацию или выполните вход', reply_markup=user_markup)


# Приветственная функция  (после входа)
def functional(update, context):
    db_session.global_init("db/cities.db")
    db_sess = db_session.create_session()
    city = ''
    for user in db_sess.query(User).all():
        if user.name == context.user_data["name"]:
            city = user.constant_city
            break
    update.message.reply_text(f'Добро пожаловать, {context.user_data["name"]}! ')
    context.user_data['current_area'] = city
    latitude, longitude = geolocation(context.user_data['current_area'])
    yandex_weather_x = yandex_weather(latitude, longitude, WEATHER_TOKEN)
    context.user_data['link'] = yandex_weather_x['link']
    print_weather(yandex_weather_x, update, context)
    update.message.reply_text(f'Вам также доступны следующие функции:\n'
                              f'/weather - узнать погоду в другом городе\n'
                              f'/conditions - узнать подробную информацию о погоде в другом городе\n'
                              f'/advice - получить совет, что следует надеть сегодня\n'
                              f'/help - справка о работе бота\n'
                              f'/change - сменить город проживания\n'
                              f'/link - получить ссылку на более подробную информацию\n'
                              f'/quit - выйти'
                              , reply_markup=functional_markup)


# Начало диалога с изменением города
def change(update, context):
    if context.user_data['name'] != '---':
        update.message.reply_text('Хотите поменять город проживания?'
                                  'Хорошо, введите новое место:')
        context.userdata['main_flag'] = False
        return 1
    else:
        update.message.reply_text('Сначала войдите в систему')
        return ConversationHandler.END


def change_city_handling(update, context):
    context.user_data['main_flag'] = True
    new_city = update.message.text
    db_session.global_init("db/cities.db")
    db_sess = db_session.create_session()
    context.user_data['current_area'] = new_city
    for user in db_sess.query(User).all():
        if user.name == context.user_data["name"]:
            user.constant_city = new_city
            db_sess.commit()
    update.message.reply_text('Город проживания успешно изменен')
    return ConversationHandler.END


# Процесс входа
def enter(update, context):
    if context.user_data['main_flag']:
        update.message.reply_text('Вы активировали процесс входа. Чтобы прервать последующий диалог, '
                                  'используйте команду /stop. Пожалуйста, введите свой никнейм')
        context.user_data['main_flag'] = False
        return 1
    else:
        update.message.reply_text('Сначала завершите предыдущую задачу')


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
    context.user_data['main_flag'] = True
    global current_name
    password = update.message.text
    f = False

    db_session.global_init("db/cities.db")
    db_sess = db_session.create_session()
    for user in db_sess.query(User).all():
        if user.name == current_name and user.password == password:
            f = True
    if f:
        context.user_data['name'] = current_name
        functional(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text('Вы ввели неверный пароль. Пожалуйста, войдите в систему заново',
                                  reply_markup=user_markup)
        return ConversationHandler.END


# Берем информацию о погоде с сайта Яндекс.Погоды
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
                'se': 'юго-восточное', 's': 'южное', 'sw': 'юго-западное', 'w': 'западное', 'c': 'штиль'}

    yandex_json = json.loads(yandex_req.text)
    yandex_json['fact']['condition'] = conditions[yandex_json['fact']['condition']]
    yandex_json['fact']['wind_dir'] = wind_dir[yandex_json['fact']['wind_dir']]
    for parts in yandex_json['forecast']['parts']:
        parts['condition'] = conditions[parts['condition']]
        parts['wind_dir'] = wind_dir[parts['wind_dir']]

    weather = dict()
    fact_params = ['temp', 'feels_like', 'condition', 'wind_dir',
                   'wind_speed', 'wind_gust', 'pressure_mm', 'humidity']
    forecast_params = ['sunrise', 'sunset']
    parts_params = ['temp_avg', 'feels_like',
                    'condition', 'wind_speed', 'wind_gust', 'wind_dir',
                    'pressure_mm', 'humidity', 'prec_prob']

    for parts in yandex_json['forecast']['parts']:
        weather[parts['part_name']] = dict()
        for param in parts_params:
            weather[parts['part_name']][param] = parts[param]

    weather['fact'] = dict()
    for param in fact_params:
        weather['fact'][param] = yandex_json['fact'][param]

    weather['forecast'] = dict()
    for param in forecast_params:
        weather['forecast'][param] = yandex_json['forecast'][param]

    weather['link'] = yandex_json['info']['url']
    return weather


# Ссылка на Яндекс.Погоду
def link(update, context):
    if context.user_data['main_flag']:
        if context.user_data['name'] != '---':
            update.message.reply_text('Вот ссылка на подробности:'
                                      f'{context.user_data["link"]}')
        else:
            update.message.reply_text('Сначала войдите в систему')
    else:
        update.message.reply_text('Сначала завершите предыдущую задачу')


# Вывод краткой информации о погоде
def print_weather(dict_weather_yandex, update, context):
    update.message.reply_text(f'Погода в городе {context.user_data["current_area"]} на данный момент:\n'
                              f'Температура воздуха: {dict_weather_yandex["fact"]["temp"]}℃\n'
                              f'Направление ветра {dict_weather_yandex["fact"]["wind_dir"]}\n'
                              f'Влажность воздуха: {dict_weather_yandex["fact"]["humidity"]}%\n'
                              f'{dict_weather_yandex["fact"]["condition"]}')


def main_weather(update, context):
    context.user_data['main_flag'] = True
    global WEATHER_TOKEN
    context.user_data['current_area'] = update.message.text
    latitude, longitude = geolocation(context.user_data['current_area'])
    yandex_weather_x = yandex_weather(latitude, longitude, WEATHER_TOKEN)
    context.user_data['link'] = yandex_weather_x['link']
    print_weather(yandex_weather_x, update, context)
    return ConversationHandler.END


# Начало диалога с запросом краткой информации о погоде
def weather(update, context):
    if context.user_data['main_flag']:
        if context.user_data['name'] != '---':
            context.user_data['main_flag'] = False
            update.message.reply_text('Хотите узнать погоду? Введите название интересующего города:')
            return 1
        else:
            update.message.reply_text('Сначала войдите в систему')
            return ConversationHandler.END
    else:
        update.message.reply_text('Сначала завершите предыдущую задачу')


# Начало диалога с запросом подробной информации о погоде
def conditions(update, context):
    if context.user_data['main_flag']:
        context.user_data['main_flag'] = False
        if context.user_data['name'] != '---':
            update.message.reply_text('Введите название города, для которого хотите '
                                      'узнать подробную информацию о погоде')
            return 1
        else:
            update.message.reply_text('Сначала войдите в систему')
            return ConversationHandler.END
    else:
        update.message.reply_text('Сначала завершите предыдущую задачу')


def detailed_weather(update, context):
    global WEATHER_TOKEN
    context.user_data['current_area'] = update.message.text
    latitude, longitude = geolocation(context.user_data['current_area'])
    yandex_weather_x = yandex_weather(latitude, longitude, WEATHER_TOKEN)
    context.user_data['link'] = yandex_weather_x['link']
    print_detailed_weather(yandex_weather_x, update, context)
    return 2


# Вывод подробной информации о погоде
def print_detailed_weather(dict_weather, update, context):
    update.message.reply_text(f'Погода в городе {context.user_data["current_area"]} на данный момент:\n'
                              f'Температура воздуха: {dict_weather["fact"]["temp"]}℃'
                              f'(ощущается как {dict_weather["fact"]["feels_like"]}℃)\n'
                              f'Направление ветра {dict_weather["fact"]["wind_dir"]}\n'
                              f'Скорость ветра {dict_weather["fact"]["wind_speed"]} м/с\n'
                              f'Скорость порывов ветра {dict_weather["fact"]["wind_gust"]} м/с\n'
                              f'Влажность воздуха: {dict_weather["fact"]["humidity"]}%\n'
                              f'Давление {dict_weather["fact"]["pressure_mm"]} мм рт. ст.\n'
                              f'{dict_weather["fact"]["condition"].capitalize()}\n'
                              f'Время рассвета:{dict_weather["forecast"]["sunrise"]}\n'
                              f'Время заката:{dict_weather["forecast"]["sunset"]}\n'
                              'Для того чтобы узнать прогноз на утро/день/вечер/ночь, '
                              'напишите боту morning/day/evening/night соответственно. '
                              'Если Вам это не нужно, воспользуйтесь командой /stop'
                              )


# Вывод прогноза погоды на конкретное время суток
def daytime_weather(update, context):
    context.user_data['main_flag'] = True
    day = {'night': 'ночью', 'morning': 'утром', 'day': 'днем', 'evening': 'вечером'}
    global WEATHER_TOKEN
    latitude, longitude = geolocation(context.user_data['current_area'])
    yandex_weather_x = yandex_weather(latitude, longitude, WEATHER_TOKEN)
    daytime = update.message.text
    if daytime not in yandex_weather_x.keys():
        update.message.reply_text('Увы, введенное Вами время дня уже прошло (или вы ввели его некорректно)')
        return ConversationHandler.END
    else:
        for key in yandex_weather_x:
            if key == daytime:
                update.message.reply_text(f'Погода в городе {context.user_data["current_area"]} {day[daytime]}:\n'
                                          f'Средняя температура {yandex_weather_x[daytime]["temp_avg"]}℃\n'
                                          f'Ощущается как {yandex_weather_x[daytime]["feels_like"]}℃\n'
                                          f'Скорость ветра {yandex_weather_x[daytime]["wind_speed"]} м/с\n'
                                          f'Скорость порывов ветра {yandex_weather_x[daytime]["wind_gust"]} м/с\n'
                                          f'Направление ветра {yandex_weather_x[daytime]["wind_dir"]}\n'
                                          f'Давление {yandex_weather_x[daytime]["pressure_mm"]} мм рт. ст.\n'
                                          f'Влажность воздуха {yandex_weather_x[daytime]["humidity"]} %\n'
                                          f'Вероятность осадков {yandex_weather_x[daytime]["prec_prob"]} %\n'
                                          f'{yandex_weather_x[daytime]["condition"]}')
                break
        return ConversationHandler.END


# Выход из системы
def quit(update, context):
    context.user_data['name'] = '---'
    update.message.reply_text('Вы вышли из системы. Чтобы продолжить работу, пожалуйста, войдите заново.',
                              reply_markup=user_markup)


# Служит для начала диалога с запросом совета о том, что надеть
def advice(update, context):
    if context.user_data['main_flag']:
        db_session.global_init("db/cities.db")
        db_sess = db_session.create_session()
        city = ''
        for user in db_sess.query(User).all():
            if user.name == context.user_data["name"]:
                city = user.constant_city
                break
        context.user_data['current_area'] = city
        latitude, longitude = geolocation(context.user_data['current_area'])
        yandex_weather_x = yandex_weather(latitude, longitude, WEATHER_TOKEN)
        context.user_data['link'] = yandex_weather_x['link']
        print_advice(yandex_weather_x, update, context)
    else:
        update.message.reply_text('Сначала завершите предыдущую задачу')


# Вывод совета о том, что надеть
def print_advice(dict_weather, update, context):
    cond_adv = ''
    weather = dict_weather["fact"]
    if weather["wind_speed"] >= 25:
        wind_adv = 'На улице ураган. Покидать помещение опасно для жизни. '
    elif weather["wind_speed"] >= 10:
        wind_adv = 'На улице сильный ветер. По возможности оставайтесь в помещении, в противном случае наденьте шарф ' \
                   'и теплую одежду. '
    elif weather["wind_speed"] >= 5:
        wind_adv = 'На улице ветренно. Рекомендуем надеть шарф или платок, а также ветровку. '
    else:
        wind_adv = 'На улице безветренно. '
    if 'снег' in weather["condition"]:
        cond_adv = 'Идет снег. Необходимо надеть перчатки. '
    elif 'дождь' in weather["condition"]:
        cond_adv = 'Идет дождь. Рекомендуем взять с собой зонт или же надеть дождевик. '
    elif 'град' in weather["condition"]:
        cond_adv = 'Идет град. Оставайтесь в помещении, в противном случае, защитите голову от ударов. '
    elif 'гроза' in weather["condition"]:
        cond_adv = 'Идет гроза. Будьте бдительны, не выходите на открытую местность, избегайте купания, не находитесь' \
                   'вблизи высоких объектов. По возможности оставайтесь в помещении. '
    elif 'ясно' in weather["condition"]:
        cond_adv = 'Солнечно - '
        if weather["temp"] >= 20:
            cond_adv += 'Необходимо надеть головной убор и взять с собой солнечные очки. '
        else:
            cond_adv += 'Стоит взять с собой солнечные очки. '
    if weather["temp"] >= 30:
        temp_adv = 'Погода экстремально жаркая. Следует по возможности оставаться в помещении, а в' \
                   'случае выхода на улицу надеть легкую одежду и взять с собой холодную воду. '
    elif weather["temp"] >= 20:
        temp_adv = 'Погода жаркая, поэтому рекомендуем надеть легкую одежду, а также ' \
                   'взять с собой прохладную воду. '
    elif weather["temp"] >= 10:
        temp_adv = 'Погода комфортная, однако следует надеть куртку или теплую кофту. '
    elif weather["temp"] >= 0:
        temp_adv = 'Погода прохладная, следует надеть куртку, шапку и шарф. '
    elif weather["temp"] >= -10:
        temp_adv = 'Погода очень холодная, следует надеть теплую куртку, шапку и шарф, а также свитер или теплую ' \
                   'кофту. '
    else:
        temp_adv = 'Погода экстремально холодная, следует по возможности оставаться в помещении, а в случае выхода ' \
                   'на улицу надеть как можно больше теплой одежды. В качестве верхней одежды использовать зимние ' \
                   'куртку и штаны, надеть теплую обувь. Защищайте конечности и лицо от обморожения. '
    update.message.reply_text(f'{wind_adv + cond_adv + temp_adv}')


# Главная функция, в которой определяются все остальные
def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start, pass_user_data=True))
    dp.add_handler(CommandHandler('help', help, pass_user_data=True))
    dp.add_handler(CommandHandler('link', link, pass_user_data=True))
    dp.add_handler(CommandHandler('quit', quit, pass_user_data=True))
    dp.add_handler(CommandHandler('advice', advice, pass_user_data=True))

    conv_handler1 = ConversationHandler(
        entry_points=[CommandHandler('registration', registration, pass_user_data=True)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, registration_name, pass_user_data=True)],
            2: [MessageHandler(Filters.text & ~Filters.command, registration_password, pass_user_data=True)],
            3: [MessageHandler(Filters.text & ~Filters.command, registration_city, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler('enter', enter, pass_user_data=True)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, enter_name, pass_user_data=True)],
            2: [MessageHandler(Filters.text & ~Filters.command, enter_password, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)])

    conv_handler3 = ConversationHandler(
        entry_points=[CommandHandler('weather', weather, pass_user_data=True)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, main_weather, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)])

    conv_handler4 = ConversationHandler(
        entry_points=[CommandHandler('change', change, pass_user_data=True)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, change_city_handling, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)])

    conv_handler5 = ConversationHandler(
        entry_points=[CommandHandler('conditions', conditions, pass_user_data=True)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, detailed_weather, pass_user_data=True)],
            2: [MessageHandler(Filters.text & ~Filters.command, daytime_weather, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)])

    dp.add_handler(conv_handler1)
    dp.add_handler(conv_handler2)
    dp.add_handler(conv_handler3)
    dp.add_handler(conv_handler4)
    dp.add_handler(conv_handler5)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    db_session.global_init("db/cities.db")
    main()
