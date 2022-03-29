if __name__ == '__main__':
    import sys; sys.path.append('..')
from abc import ABC, abstractmethod
from typing import Any

from DataBase.database import database
from Country import Country
from exceptions import NoImportantParameter, OperationOnlyForOneCountry


class Item(ABC):
    """Интерфейс предметов, они должны выдавать имя своей таблицы, 
    имя в аргументах, параметры предмета и выдавать класс заказа 
    для возможности покупки"""

    table_name: str
    arguments_name: str
    
    def insert(self, parameters: dict[str, Any]):
        if not 'name' in parameters: 
            raise NoImportantParameter('name')
        
        needed_for_purchase = {}
        if 'needed_for_purchase' in parameters: 
            needed_for_purchase = parameters.pop('needed_for_purchase')

        needed_for_purchase_item = f'{self.table_name}_needed_for_purchase'
        id_ = f'{self.arguments_name}_id'

        columns = ', '.join(parameters.keys())
        values = ', '.join(('%s', )*len(list(parameters.values())))

        item_id = database().select_one(
                f'INSERT INTO {self.table_name}({columns}) '
                f'VALUES({values}) RETURNING {id_}', 
                *list(parameters.values()))[f'{id_}']

        if needed_for_purchase:
            values = []
            for i in needed_for_purchase:
                values.append(f'({item_id}, {i}, {needed_for_purchase[i]})')

            values = ',\n'.join(values)
            database().insert(f'INSERT INTO {needed_for_purchase_item}({id_}, ' 
                               'needed_build_id, count) ' 
                              f'VALUES{values}')

    def update(self, item_id: int, *, parameters: dict[str, Any]):
        needed_for_purchase_item = f'{self.table_name}_needed_for_purchase'
        id_ = f'{self.arguments_name}_id'

        if 'needed_for_purchase' in parameters.keys():
            database().insert(f'DELETE FROM {needed_for_purchase_item} '
                              f'WHERE {id_} = %s', item_id)

            needed_for_purchase = []
            for i in parameters['needed_for_purchase']:
                needed_for_purchase.append(
                    f'({item_id}, {i},'
                    f"{parameters['needed_for_purchase'][i]})"
                    )

            needed_for_purchase = ',\n'.join(needed_for_purchase)
            if needed_for_purchase:
                database().insert(f'INSERT INTO {needed_for_purchase_item}'
                                  f'({id_}, needed_build_id, count) '
                                  f'VALUES{needed_for_purchase}')
            parameters.pop('needed_for_purchase')

        columns = []
        for i in parameters.keys():
            columns.append(f'{i} = %s')

        columns = ', '.join(columns)
        database().insert(f'UPDATE {self.table_name} '
                          f'SET {columns} '
                          f'WHERE {id_} = %s', 
                          *parameters.values(), item_id)

    def delete(self, item_id: int=-1):
        if item_id == -1:
            database().insert(f'TRUNCATE TABLE {self.table_name} RESTART IDENTITY')
        else:
            database().insert(f'DELETE FROM {self.table_name} '
                              f'WHERE {self.arguments_name}_id = %s', item_id)

    @abstractmethod
    def order(self, country: Country, item_name: str, count: int):
        pass

class Order(ABC):
    """Класс заказа, по которому покупают предмет"""

    buy_ability: bool
    needed_for_buy: dict[str, Any]

    def __init__(self, country: Country, item: Item, 
                 item_id: int, count: int):
        self.buy_ability = True
        self.needed_for_buy = {}

        self.check_buy_ability(country, item, item_id, count)

        if self.buy_ability:
            self.buy()

    @abstractmethod
    def check_buy_ability(self, country: Country, item: Item, 
                          item_id: int, count: int):
        pass

    @abstractmethod
    def buy(self):
        pass

class List(ABC):
    '''Класс списков, которые использует предметы'''
    item: Item

class SimpleOrder(Order):
    buy_ability: bool
    needed_for_buy: dict[str, Any]

    def check_buy_ability(self, country: Country, item: Item, 
                          item_id: int, count: int):
        self.country = country
            
        self.item = item
        self.item_id = item_id
        self.count = count

        if country.len_ != 1:
            raise OperationOnlyForOneCountry

        self.needed_for_buy = {}
        self.buy_ability = True

        self.money = database().select_one(
            f'SELECT get_needed_price_for_{item.arguments_name}'
             '(%s, %s, %s) AS money',
            country.id_[0], item_id, count
            )['money']
        if self.money < 0:
            self.buy_ability = False
            self.needed_for_buy['money'] = abs(self.money)

        needed_builds = database().select(
            f'SELECT needed_build_name, count '
            f'FROM get_needed_builds_for_{item.arguments_name}(%s, %s)',
            country.id_[0], item_id
            )
        if len(needed_builds) > 0:
            self.buy_ability = False
            self.needed_for_buy['builds'] = {}

            for i in needed_builds:
                self.needed_for_buy['builds'][i['needed_build_name']] = abs(i['count'])

    def buy(self):
        item_inventory = f'{self.item.table_name}_inventory'
        item_id = f'{self.item.arguments_name}_id'

        database().insert(
        f'INSERT INTO {item_inventory}'
        f'(country_id, {item_id}, count) '
         'VALUES(%s, %s, %s) ' 
        f'ON CONFLICT (country_id, {item_id}) DO UPDATE '
        f'SET count = {item_inventory}.count + %s; '

        'UPDATE countries '
        'SET money = %s '
        'WHERE country_id = %s;',
        self.country.id_[0], self.item_id, self.count, 
        self.count, self.country.id_[0], self.item_id, 
        self.money, self.country.id_[0]
        )

class Build(Item):
    table_name: str = 'builds'
    arguments_name: str = 'build'

    def order(self, country: Country, item_id: int, count: int) -> Order:
        return SimpleOrder(country, self, item_id, count)

class Unit(Item):
    table_name: str = 'units'
    arguments_name: str = 'unit'

    def order(self, country: Country, item_id: int, count: int) -> Order:
        return SimpleOrder(country, self, item_id, count)


class Shop(List):
    item: Item

    def __init__(self, item: Item):
        self.item = item

    def get_shop(self) -> dict[str, dict[str, Any]]:
        shop = {}
        item_name = f'{self.item.arguments_name}_name'

        for i in database().select('SELECT * '
                                  f'FROM get_{self.item.table_name}_shop()'):
            if i[item_name] in shop:
                shop[i[item_name]]['needed_for_purchase'][i['needed_build_name']] = i['count']
                continue

            needed_build_name = i.pop('needed_build_name')
            count = i.pop('count')
            if needed_build_name:
                i['needed_for_purchase'] = {needed_build_name: count}
            shop[i.pop(item_name)] = i
            
        return shop

class Inventory(List):
    item: Item
    country: Country

    def __init__(self, item: Item, country: Country):
        self.item = item
        self.country = country

    def get_inventory(self) -> dict[str, dict[str, Any]]:
        if self.country.len_ != 1:
            raise OperationOnlyForOneCountry

        inventory = {}

        for i in database().select(
                'SELECT * '
               f'FROM get_{self.item.table_name}_inventory(%s)',
                self.country.id_[0]
               ):
            inventory[i.pop('name')] = i

        return inventory

    def edit_inventory(self, item_id: int, count: int):
        if self.country.len_ == -1:
            countries = database().select('SELECT country_id '
                                          'FROM countries')
            values = []
            for i in countries:
                values.append(f"({i['country_id']}, {item_id}, {count})")
        
        else:
            values = []
            for i in self.country.id_:
                values.append(f"({i}, {item_id}, {count})")

        values = ',\n'.join(values)
        
        item_inventory = f'{self.item.table_name}_inventory'
        id_ = f'{self.item.arguments_name}_id'

        database().insert(f'INSERT INTO {item_inventory}'
                          f'(country_id, {id_}, count) '
                          f'VALUES{values} '
                          f'ON CONFLICT(country_id, {id_}) DO UPDATE '
                          f'SET count = {item_inventory}.count+%s', count)
    
    def delete_inventory_item(self, item_id: int):
        if self.country.where:
            where = (f'{self.country.where} AND {self.item.arguments_name}_id = '
                     f'{item_id}')
        else:
            where = f'WHERE {self.item.arguments_name}_id = {item_id}'

        database().insert(f'DELETE FROM {self.item.table_name}_inventory '
                          + where)

    def delete_inventory(self):
        item_inventory = f'{self.item.table_name}_inventory'

        if self.country.len_ == -1:
            database().insert(f'TRUNCATE TABLE {item_inventory}')
        else:
            database().insert(f'DELETE FROM {item_inventory}'
                              + self.country.where)
