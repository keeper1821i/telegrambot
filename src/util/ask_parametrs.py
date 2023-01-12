from src.util.data_manager import *
from src.util.dictionary import dictionary
import re
import datetime
from src.config import bot
from src.util.output import result


def ask_date(message: types.Message) -> None:
    """Запрос даты заезда"""
    bot.send_message(chat_id=message.chat.id, text=dictionary['move_in'])
    bot.register_next_step_handler(message, first_date)


def first_date(message: types.Message) -> None:
    """Запрос даты отъезда
       Запись даты заезда
    """
    bot.send_message(chat_id=message.chat.id, text=dictionary['move_out'])
    set_first_date(message.chat.id, message.text)
    bot.register_next_step_handler(message, second_date)


def second_date(message: types.Message) -> None:
    """Запись даты отъезда,
       Стартовое соощение
    """

    set_second_date(message.chat.id, message.text)
    count_day(message)


def count_day(message):
    move_in = get_first(message.chat.id)
    move_out = get_second(message.chat.id)
    move_in = move_in.split('.')
    move_out = move_out.split('.')
    try:
        a = datetime.date(int(move_in[0]), int(move_in[1]), int(move_in[2]))
        b = datetime.date(int(move_out[0]), int(move_out[1]), int(move_out[2]))
        c = b - a
        set_day(message.chat.id, c.days)
        bot.send_message(chat_id=message.chat.id, text=dictionary['ask_for_city'])
        bot.register_next_step_handler(message, search_city)
    except (IndexError, ValueError):
        bot.send_message(chat_id=message.chat.id, text=dictionary['bad_date'])
        ask_date(message)


@bot.callback_query_handler(func=lambda call: any(key in call.message.text
                                                  for key in ['lowprice', 'highprice', 'bestdeal']))
def operation_for_history(call: types.CallbackQuery) -> None:
    """Обработка сообщений истории поиска (скрыть, очистить)"""
    if call.data in [value[0] for value in dictionary['operations_for_history'].values()]:
        clear_history(call.message.chat.id)
    for i_message_id in get_message_list(chat_id=call.message.chat.id, message_id=call.message.id):
        bot.delete_message(chat_id=call.message.chat.id, message_id=int(i_message_id))


@bot.callback_query_handler(func=lambda call: dictionary['city_results'] in call.message.text)
def city_handler(call: types.CallbackQuery) -> None:
    """Обработка данных искомого города (id, name), определение следующего шага обработчика"""
    set_city(call.message.chat.id, call.data)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    if flag_advanced_question(call.message.chat.id):
        ask_for_price_range(call.message)
    else:
        ask_for_hotels_value(call.message)


def search_city(message: types.Message) -> None:
    """Проверка параметров настроек, обработка запроса пользователя по поиску города,
    вывод Inline клавиатуры с результатами"""
    temp = bot.send_message(chat_id=message.chat.id,
                            text=dictionary['search'], parse_mode='HTML')
    city_list = get_city_list(message)
    keyboard = types.InlineKeyboardMarkup()
    if not city_list:
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id, text=dictionary['no_options'],
                              parse_mode='HTML')
    else:
        for city_name, city_id in city_list.items():
            keyboard.add(types.InlineKeyboardButton(text=city_name, callback_data=city_id))
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id, text=dictionary['city_results'],
                              reply_markup=keyboard)


def ask_for_price_range(message: types.Message) -> None:
    """Запрос ценового диапазона у пользователя, определение следующего шага обработчика"""
    bot.send_message(chat_id=message.chat.id, text=dictionary['ask_price'].format(cur='RUB'))
    bot.register_next_step_handler(message, ask_for_dist_range)


def ask_for_dist_range(message: types.Message) -> None:
    """Обработка значений ценового диапазона пользователя, запрос диапазона дистанции,
    определение следующего шага обработчика"""
    price_range = list(set(map(int, map(lambda string: string.replace(',', '.'),
                                        re.findall(r'\d+[.,\d+]?\d?', message.text)))))
    if len(price_range) != 2:
        raise ValueError('Range Error')
    else:
        set_price_range(chat_id=message.chat.id, value=price_range)
        bot.send_message(chat_id=message.chat.id, text=dictionary['ask_dist'])
        bot.register_next_step_handler(message, ask_for_hotels_value)


def ask_for_hotels_value(message: types.Message) -> None:
    """Обработка значений диапазона дистанции пользователя, запрос количества отелей,
    определение следующего шага обработчика"""
    if flag_advanced_question(message.chat.id):
        dist_range = list(set(map(float, map(lambda string: string.replace(',', '.'),
                                             re.findall(r'\d+[.,\d+]?\d?', message.text)))))
        if len(dist_range) != 2:
            raise ValueError('Range Error')
        else:
            set_dist_range(chat_id=message.chat.id, value=dist_range)

    bot.send_message(chat_id=message.chat.id, text=dictionary['hotels_value'])
    bot.register_next_step_handler(message, photo_needed)


def photo_needed(message: types.Message) -> None:
    """Обработка значения кол-ва отелей пользователя, запрос необходимости вывода фото в виде Inline клавитуары"""
    set_hotels_value(chat_id=message.chat.id, value=abs(int(message.text)))
    keyboard = types.InlineKeyboardMarkup()
    [keyboard.add(types.InlineKeyboardButton(x, callback_data=x)) for x in
     [dictionary['pos'], dictionary['neg']]]
    bot.send_message(message.chat.id, text=dictionary['photo_needed'],
                     reply_markup=keyboard)


@bot.callback_query_handler(
    func=lambda call: dictionary['photo_needed'] in call.message.text)
def set_photo_needed(call: types.CallbackQuery) -> None:
    """Обработка ответа пользователя о необходимости вывода фото, определение хода действий."""
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    if call.data in dictionary['pos']:
        set_needed_photo(chat_id=call.message.chat.id, value=True)
        number_of_photo(call.message)
    else:
        set_needed_photo(chat_id=call.message.chat.id, value=False)
        result(call.message)


def number_of_photo(message: types.Message) -> None:
    """Запрос кол-ва фото у пользователя, определение следующего шага обработчика"""
    bot.send_message(chat_id=message.chat.id,
                     text=dictionary['photos_value'])
    bot.register_next_step_handler(message, result)
