import sys; sys.path.append('.')

from DataBase.database import database
from psycopg2._psycopg import cursor
from Service.Service import Country

from abc import ABC, abstractmethod
from typing import Any


class Item(ABC):
    '''Класс предмета, должен выдавать информацию о предмете для вызова из БД,
    а так же проводить специальные операции при покупке'''
    @abstractmethod
    def get_type(self) -> str:
        pass

    def get_parameters(self) -> dict[str: Any]:
        '''Возвращает параметры предмета: 
        параметры для всех предметов+специальные параметры предметов'''
        parameters = {'Name': '',
                      'Price': 0,
                      'Description': '',
                      'NeededForPurchase': [{''}],
                      'Saleabillity': False}
        
        special_parameters = self.get_item_parameters()
        for i in special_parameters:
            parameters[i] = special_parameters[i]

        return parameters

    @abstractmethod
    def get_item_parameters() -> dict[str: Any]:
        pass
        
    @abstractmethod
    def item_check_buy_ability(self, cur: cursor, country: Country,
                               item_id: int, item_count: int) -> bool:
        pass
    

    @abstractmethod
    def action_after_buy(self, cur: cursor, country: Country,
                         item_id: int, item_count: int):
        pass


class List(ABC):
    def check_buy_ability(self, cur: cursor, country: Country, inventory: dict[int: int],
                          item_id: int, item_count: int):
        item = self.get_type()
        where = country.get_access()['where']

        cur.execute(f'SELECT balance FROM Balance WHERE country_{where}')
        balance = cur.fetchone()

        cur.execute(f'SELECT price FROM {item} WHERE id = {item_id}')
        price = cur.fetchone()*item_count
        
        if not (balance >= price):
            return False

        cur.execute(f'SELECT needed_build_id, count FROM {item}NeededForPurchase WHERE build_id = {item_id}')
        for i in cur.fetchall():
            try:
                if inventory[i[0]] >= i[1]:
                    continue
                else:
                    return False
            except KeyError:
                return False
            
        return self.item_check_buy_ability(cur, country, inventory, item_id, item_count)