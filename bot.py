import os
import random
import googlemaps
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# [Opcional] Recomendable poner un log con los errores que apareceran por pantalla.
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
def error_callback(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

try:
    from settings import BOT_TOKEN, MAPS_TOKEN
except:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    MAPS_TOKEN = os.environ['MAPS_TOKEN']

gmaps = googlemaps.Client(key=MAPS_TOKEN)


def save_activity(command, update):
    with open('activity.log', 'a') as f:
        f.write(f'{datetime.now()} - {command} - {update.message.from_user.first_name} - {update.message.from_user.id} - {update.message.chat.id}\n')
        f.close()


def start(update, context):
    save_activity('/start', update)
    update.message.reply_text('Bienvenido, soy el bot que te ayudara a encontrar un lugar para comer.')


def help(update, context):
    save_activity('/help', update)
    msg = '''
    <b>Comandos disponibles:</b>
    /restaurant - <i>Busca un restaurante</i>
    /restaurant_zone palermo - <i>Busca un restaurante en una zona</i>
    /bar - <i>Busca un bar</i>
    /bar_zone palermo - <i>Busca un bar en una zona</i>
    /help - <i>Muestra este mensaje</i>
    '''
    update.message.reply_html(msg)


def get_location_by_zone(zone):
    random_lat = round(random.uniform(-34.6500000, -34.5500000), 6)
    random_lng = round(random.uniform(-58.3640000, -58.5000000), 6)
    if zone:
        zones = gmaps.geocode(address=zone, region='ar', language='es')
        if zones:
            zones[0].get('geometry').get('location')
    return {'lat': random_lat, 'lng': random_lng}


def get_location_by_place(place):
    return {'latitude': place.get('result').get('geometry').get('location').get('lat'),
            'longitude': place.get('result').get('geometry').get('location').get('lng')}


def get_ramdom_place_id(type='restaurant', zone=None, keyword=None):
    place_args = {
        'location': get_location_by_zone(zone),
        'radius': 1000,
        'type': type,
        'language': 'es',
        'open_now': True,
        'min_price': 1,
        'max_price': 4,
        'keyword': keyword,
    }
    if not gmaps.places_nearby(**place_args).get('status') == 'OK':
        return get_ramdom_place_id()
    else:
        return gmaps.places_nearby(**place_args).get('results').pop().get('place_id')


def get_caption(place):
    name = place.get('result').get('name')
    url = place.get('result').get('url')
    address = place.get('result').get('formatted_address')
    price_level = place.get('result').get('price_level') * '💰'
    rating = round(place.get('result').get('rating')) * '⭐️'
    return f'<b>🍽 <a href="{url}">{name}</a> 🍽</b>&#10;&#13;&#10;&#13;&#8226; {rating} &#8226; {price_level} &#8226;&#10;&#13;&#10;&#13;🗺 <code>{address}</code> 🗺'


def get_photo_file(photo):
    photo_reference = photo.get('photo_reference')
    raw_image_data = gmaps.places_photo(photo_reference,'400','400')
    f = open('image.jpg', 'wb')
    for chunk in raw_image_data:
        if chunk:
            f.write(chunk)
    f.close()
    return open('image.jpg', 'rb')


def get_ramdom_place(update, context, **kargs):
    place = gmaps.place(place_id=get_ramdom_place_id(type=kargs.get('type'), zone=kargs.get('zone'), keyword=kargs.get('keyword')))
    caption = get_caption(place)
    update.message.reply_html(caption)
    location = get_location_by_place(place)
    update.message.reply_location(**location)


def restaurant(update, context):
    save_activity('/restaurant', update)
    keyword = ' '.join(context.args) if context.args else None
    return get_ramdom_place(update, context, type='restaurant',keyword=keyword)


def bar(update, context):
    save_activity('/bar', update)
    keyword = ' '.join(context.args) if context.args else None
    return get_ramdom_place(update, context, type='bar', keyword=keyword)


def restaurant_zone(update, context):
    save_activity('/restaurant_zone', update)
    zone = ' '.join(context.args) if context.args else None
    if not zone:
        return update.message.reply_text('Debe ingresar el comando con una zona')
    return get_ramdom_place(update, context, type='restaurant', zone=zone)


def bar_zone(update, context):
    save_activity('/bar_zone', update)
    zone = ' '.join(context.args) if context.args else None
    if not zone:
        return update.message.reply_text('Debe ingresar el comando con una zona')
    return get_ramdom_place(update, context, type='bar', zone=zone)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def add_all_handlers(updater):
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("restaurant", restaurant))
    dp.add_handler(CommandHandler("bar", bar))
    dp.add_handler(CommandHandler("restaurant_zone", restaurant_zone))
    dp.add_handler(CommandHandler("bar_zone", bar_zone))
    # dp.add_handler(CommandHandler("random_delivery", ramdom_delivery))
    dp.add_error_handler(error)


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    add_all_handlers(updater)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    print(('[Donde comemos hoy] Start...'))
    main()