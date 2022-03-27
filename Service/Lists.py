import sys; sys.path.append('..')

from DataBase.database import database
from psycopg2._psycopg import cursor
from Country import Country

from abc import ABC, abstractmethod
from typing import Any


class Order(ABC):
    '''Класс заказа, проверяет на возможность покупки и покупает предмет'''
    buy_ability: bool
    info: dict[str, Any]

    country_id: int
    item_type: str
    item_id: int
    count: int

    @abstractmethod
    def buy(self):
        '''Покупает предмет если прошла проверка на возможность покупки'''
        pass

class SimpleOrder(Order):
    buy_ability: bool
    info: dict[str, Any]

    economy: Economy
    item_type: str
    item_id: int
    count: int

    def __init__(self, economy: Economy, item: Item, item_id: int, count: int):
        self.economy = economy
        self.item_type = item.item_name
        self.item_id = item_id
        self.count = count

        price = database().select(f'''SELECT price*{count}
                                      FROM {self.item_type}
                                      WHERE {self.item_type}_id = {item_id}''')
        money = economy.money

class Item(ABC):
    '''Класс предмета, должен выдавать информацию о предмете для вызова из БД,
    а так же проводить специальные операции при покупке'''
    item_name: str

    @abstractmethod
    def select(self, columns: tuple[str]=None, join: tuple[str]=None, where: str = '') -> dict[str, Any]:
        '''Выдает список предметов, по указанным параметрам'''
        pass

    @abstractmethod
    def insert(self, **kwargs):
        '''Создает новый предмет'''
        pass

    @abstractmethod
    def get_order(self, country: Country, item_id: int, count: int) -> Order:
        '''Выдает класс заказа с помощью которого можно купить предмет'''
        pass


class List(ABC):
    item: Item
