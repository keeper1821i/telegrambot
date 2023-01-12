from src.util.data_manager import *
from src.util.dictionary import dictionary
import telebot
from src.config import bot


@bot.message_handler(commands=['history'])
def history(message: types.Message) -> None:
    """Вывод истории поиска"""
    i_history = get_history(message.chat.id)
    if i_history:
        message_list = list()
        for i_query, i_hotels in i_history.items():
            temp = bot.send_message(chat_id=message.chat.id, text='{func}\n\n{hotels}'.format(
                func=i_query, hotels='\n'.join(i_hotels)), parse_mode='HTML', disable_web_page_preview=True)
            message_list.append(str(temp.id))
        else:
            set_message_list(chat_id=message.chat.id, i_key=message_list[-1], i_value=message_list)
            keyword = types.InlineKeyboardMarkup(row_width=2)
            buttons = [types.InlineKeyboardButton(text=text, callback_data=text)
                       for text in dictionary['operations_for_history']]
            keyword.add(*buttons)
            bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=int(message_list[-1]),
                                          reply_markup=keyword)
    else:
        bot.send_message(chat_id=message.chat.id, text=dictionary['clr_history'])


def result(message: types.Message) -> None:
    """Обработка значения кол-ва фото, выполнение поиска вариантов, представление результатов"""
    if get_needed_photo(chat_id=message.chat.id):
        set_photos_value(chat_id=message.chat.id, value=abs(int(message.text)))
    temp = bot.send_message(chat_id=message.chat.id, text=dictionary['search'])
    hotels_dict, search_link = get_hotels(user_id=message.chat.id)

    if hotels_dict:
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id,
                              text=dictionary['ready_to_result'])
        for index, i_data in enumerate(hotels_dict.values()):
            if index + 1 > get_hotels_value(chat_id=message.chat.id):
                break
            text = dictionary['main_results'].format(
                name=i_data['name'], address=get_address(i_data), distance=get_landmarks(i_data),
                price=i_data['price'],
                day=get_day(message.chat.id),
                total_price='$' + str(int(i_data['price'][1:]) * get_day(message.chat.id)),
                link='https://hotels.com/ho' + str(i_data['id']),
                address_link='https://www.google.ru/maps/place/' + i_data['coordinate'])

            if get_needed_photo(chat_id=message.chat.id):
                photo_list = get_photos(user_id=message.chat.id, hotel_id=int(i_data['id']), text=text)
                for i_size in ['z', 'y', 'd', 'n', '_']:
                    try:
                        bot.send_media_group(chat_id=message.chat.id, media=photo_list)
                        break
                    except telebot.apihelper.ApiTelegramException:
                        photo_list = [types.InputMediaPhoto(caption=obj.caption, media=obj.media[:-5] + f'{i_size}.jpg',
                                                            parse_mode=obj.parse_mode) for obj in photo_list]
            else:
                bot.send_message(message.chat.id, text, parse_mode='HTML', disable_web_page_preview=True)

        bot.send_message(chat_id=message.chat.id, text=dictionary['additionally'].format(
            link=search_link), parse_mode='MarkdownV2', disable_web_page_preview=True)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=temp.id,
                              text=dictionary['no_options'])
