"""
Модуль main_request.py
Описывает взаимодействие с Hotels API (rapidapi.com).
"""

from typing import Callable, Dict, List, Tuple, Union, Any
import requests
import json
import arrow
import re
from time import time, ctime
import traceback
from src import config
from src.util.dictionary import SCError



city_url = 'https://hotels4.p.rapidapi.com/locations/search'
hotel_url = 'https://hotels4.p.rapidapi.com/properties/list'
photo_url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'




def request_to_api(url, hs, qs):
    """
    Функция для обращения к HotelsApi с проверкой кода ответа HTTP
    :return: результат запроса к API
    """
    try:
        try:
            res = requests.get(url, headers=hs, params=qs, timeout=10)
        except requests.Timeout as exception:
            with open('errors_log.txt', 'a') as file:
                file.write('\n'.join([ctime(time()), exception.__class__.__name__, traceback.format_exc(),
                                      f'status_code = {res.status_code}\n\n']))
            return False
        if res.status_code == 200:
            return res
        else:
            raise SCError
    except SCError as exception:
        with open('errors_log.txt', 'a') as file:
            file.write('\n'.join([ctime(time()), exception.__class__.__name__, traceback.format_exc(),
                                  f'status_code = {res.status_code}\n\n']))
        return False


def location_search(message) -> Dict[str, str]:
    """
    Выполнение HTTP-запроса к Hotels API (rapidapi.com) (Поиск локаций (городов)).
    :param message: сообщение пользователя
    :return: словарь, содержащий сведения локаций (городов)
    """

    querystring = {"query": message.text, "locale": "{}".format(message.text)}
    # response = requests.request("GET", city_url, headers=headers, params=querystring, timeout=10)
    response = request_to_api(city_url, config.headers, querystring)
    if response is False:
        pass
    else:
        data = json.loads(response.text)

        city_dict = {', '.join((city['name'], re.findall('(\\w+)[\n<]', city['caption']+'\n')[-1])): city['destinationId']
                     for city in data['suggestions'][0]['entities']}
        return city_dict


def hotels_search(data: Dict[str, Union[int, str, None, List[Union[int, float]], Dict[str, Union[str, List[str]]]]],
                  sorted_func: Callable) -> \
        Union[Tuple[Union[Dict[str, Dict[str, Union[str, None]]], None], Union[str, None]]]:
    """
    Выполнение HTTP-запроса к Hotels API (rapidapi.com) (поиск вариантов размещения (отелей)).
    :param data: данные пользователя
    :param sorted_func: функция, выполняющая http-запрос
    :return: кортеж, содержаший словарь со сведениями вариантов размещения (отелей) и url-ссылку
    """
    if data['sorted_func'] == 'bestdeal':
        hotels_data = sorted_func(user_city_id=data['city_id'], lang=data['lang'], cur=data['cur'],
                                  hotels_value=data['hotels_value'], hotel_url=hotel_url,
                                  headers=config.headers, price_range=data['price_range'],
                                  dist_range=data['dist_range'], today=arrow.utcnow().format("YYYY-MM-DD"))
    else:
        hotels_data = sorted_func(user_city_id=data['city_id'], lang=data['lang'], cur=data['cur'],
                                  hotels_value=data['hotels_value'], hotel_url=hotel_url,
                                  headers=config.headers, today=arrow.utcnow().format("YYYY-MM-DD"))
    return hotels_data


def photos_search(data: Dict[str, Union[int, str, None, List[Union[int, float]], Dict[str, Union[str, List[str]]]]],
                  hotel_id: int) -> List[Dict[str, Union[str, Any]]]:
    """
    Выполнение HTTP-запроса к Hotels API (rapidapi.com) (поиск фото).
    :param data: данные пользователя
    :param hotel_id: hotel id
    :return: список url-адресов фото варианта размещения (отеля)
    """

    querystring = {"id": "{}".format(hotel_id)}
    # response = requests.request("GET", photo_url, headers=headers, params=querystring, timeout=10)
    response = request_to_api(photo_url, config.headers, querystring)
    if response is False:
        pass
    else:
        photo_data = json.loads(response.text)
        photos_address = photo_data["hotelImages"][:data['photos_value']]
        return photos_address
