import re
from src.util.data_manager import *
from src.util.dictionary import dictionary
import traceback
from time import time, ctime, sleep
from typing import Callable
import functools
from src.config import bot
from src.util.ask_parametrs import ask_date


def exc_handler(method: Callable) -> Callable:
    """ Декоратор. Логирует исключение вызванной функции, уведомляет пользователя об ошибке. """
    @functools.wraps(method)
    def wrapped(message: Union[types.Message, types.CallbackQuery]) -> None:
        try:
            method(message)
        except (ValueError, IndexError) as exception:
            if isinstance(message, types.CallbackQuery):
                message = message.message
            if exception.__class__.__name__ == 'JSONDecodeError':
                reset_data(message.chat.id)
                exc_handler(method(message))
            else:
                if str(exception) == 'Range Error':
                    bot.send_message(chat_id=message.chat.id,
                                     text=dictionary['rng_err'])
                else:
                    bot.send_message(chat_id=message.chat.id,
                                     text=dictionary['val_err'])
                bot.register_next_step_handler(message=message, callback=exc_handler(method))
        except Exception as exception:
            bot.send_message(chat_id=message.chat.id, text=dictionary['crt_err'])
            with open('errors_log.txt', 'a') as file:
                file.write('\n'.join([ctime(time()), exception.__class__.__name__, traceback.format_exc(), '\n\n']))
            sleep(1)
    return wrapped


@bot.message_handler(regexp=r'.*[Пп]ривет.*')
@bot.message_handler(commands=['start', 'hello_world', 'help'])
def start_message(message: types.Message) -> None:
    """Стартовое сообщение"""
    bot.send_message(chat_id=message.chat.id, text=dictionary['started_message'])


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
@exc_handler
def set_func(message: types.Message) -> None:
    """Установка сортирующей функции, определение следующего шага обработчика"""
    set_sorted_func(chat_id=message.chat.id, func=re.search(r'\w+', message.text).group())
    ask_date(message)


bot.polling(non_stop=True)
