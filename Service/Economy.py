import sys; sys.path.append('..')

from DataBase.database import database
from psycopg2._psycopg import cursor
from Country import Country

from typing import Any


class Economy:
    country_info: dict[str, Any]
    where: str
    money: int

    def __init__(self, country: Country):
        self.country_info = country.get_access()
        self.where = where = f'WHERE {self.country_info[\'where\']}' if self.country_info['where'] else ''

    def edit_money(self, money: int):
        database().insert(f'''UPDATE {self.country_info['from']}
                              SET money = money+{money}
                              {self.where}''')
    def delete(self):
        database().insert(f'''UPDATE {self.country_info['from']}
                              SET money = 0
                              {self.where}''')

class Order(ABC):
    '''Класс заказа, проверяет на возможность покупки и покупает предмет'''

    buy_ability: bool
    info: dict[str, Any]

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

    buy_info: dict[str, Any]

    def __init__(self, economy: Economy, item: Item, item_id: int, count: int):
        self.economy = economy
        self.item_type = item.item_name
        self.item_id = item_id
        self.count = count

        price = database().select(f'''SELECT price*{count}
                                      FROM {self.item_type}
                                      WHERE {self.item_type}_id = {item_id}''')
        self.buy_info = {'price': price}

        if economy.money >= price:
            self.buy_ability = True
        else:
            self.buy_ability = False
            self.info = {'price': price-economy.money}

    def buy(self):
        if self.buy_ability:
            self.economy.edit_money(-self.buy_info['price'])
            database().insert(f'''INSERT INTO {self.item_type}_inventory(country_id, {self.item_type}_id, count)
                                  ''')
