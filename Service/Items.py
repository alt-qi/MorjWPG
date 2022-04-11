if __name__ == '__main__':
    import sys; sys.path.append('..')
from abc import ABC, abstractmethod
from typing import Any

from psycopg2._psycopg import cursor

from Database.Database import database
from Service.Country import Country
from Service.exceptions import CantTransact, NoImportantParameter, \
                               NoItem, OperationOnlyForOneCountry


class Item(ABC):
    """
    Интерфейс предметов, они должны выдавать имя своей таблицы, 
    имя в аргументах, параметры предмета и выдавать класс заказа 
    для возможности покупки
    
    """

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

    def update(self, item_id: int, parameters: dict[str, Any]):
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
            database().insert(f'TRUNCATE TABLE {self.table_name} RESTART IDENTITY CASCADE')
        else:
            database().insert(f'DELETE FROM {self.table_name} '
                              f'WHERE {self.arguments_name}_id = %s', item_id)


    def get_id(self, name: str) -> dict[str, int]:
        name_id = {}
        for i in database().select(f'SELECT name, {self.arguments_name}_id '
                                   f'FROM get_{self.table_name}_by_name(%s)',
                                   name):
            name_id[i['name']] = i[f'{self.arguments_name}_id']

        return name_id

    @abstractmethod
    def buy(self, country: Country, item_id: int, count: int):
        pass

    @abstractmethod
    def sell(self, country_seller: Country, country_customer: Country,
                   item_id: int, count: int, price: int):
        pass

class Order(ABC):
    """Класс заказа по которому строятся другие заказы"""

    transact_ability: bool
    needed_for_transact: dict[str, Any]

    def __init__(self, *args):
        self.transact_ability = True
        self.needed_for_transact = {}

        conn = database().get_conn()
        try:
            conn.set_isolation_level('READ COMMITTED')
            with conn:
                with conn.cursor() as cur:
                    self.check_transact_ability(cur, *args)

                    if self.transact_ability:
                        self.transact(cur, *args)
                    else:
                        raise CantTransact(self.needed_for_transact)
        finally:
            database().put_conn(conn)

    @abstractmethod
    def check_transact_ability(self, *args):
        pass

    @abstractmethod
    def transact(self, *args):
        pass

class BuyOrder(Order):
    transact_ability: bool
    needed_for_transact: dict[str, Any]

    def check_transact_ability(self, cur: cursor, country: Country, item: Item, 
                               item_id: int, count: int):
        if country.len_ != 1:
            raise OperationOnlyForOneCountry

        cur.execute(f'SELECT get_needed_price_for_{item.arguments_name}'
                     '(%s, %s, %s) AS money',
                     (country.id_[0], item_id, count))

        self.money = cur.fetchone()[0]
        if self.money < 0:
            self.transact_ability = False
            self.needed_for_transact['money'] = self.money

        cur.execute(f'SELECT needed_build_name, count '
                    f'FROM get_needed_builds_for_{item.arguments_name}(%s, %s)',
                     (country.id_[0], item_id))

        needed_builds = cur.fetchall()
        if len(needed_builds) > 0:
            self.transact_ability = False
            self.needed_for_transact['builds'] = {}

            for i in needed_builds:
                self.needed_for_transact['builds'][i[0]] = i[1]

    def transact(self, cur: cursor, country: Country, item: Item, 
                 item_id: int, count: int):
        item_inventory = f'{item.table_name}_inventory'
        id_ = f'{item.arguments_name}_id'

        cur.execute(f'INSERT INTO {item_inventory}'
                    f'(country_id, {id_}, count) '
                     'VALUES(%s, %s, %s) ' 
                    f'ON CONFLICT (country_id, {id_}) DO UPDATE '
                    f'SET count = {item_inventory}.count + %s',
                     (country.id_[0], item_id, count, count))

        cur.execute('UPDATE countries '
                    'SET money = %s '
                    'WHERE country_id = %s;',
                    (self.money, country.id_[0]))

class SellOrder(Order):
    transact_ability: bool
    needed_for_transact: dict[str, Any]

    def check_transact_ability(
            self, cur: cursor, country_seller: Country, country_customer: Country,
            item: Item, item_id: int, count: int, price: int
            ):
        if country_seller.len_ != 1 or country_customer.len_ != 1:
            raise OperationOnlyForOneCountry
        
        cur.execute('SELECT saleability '
                   f'FROM {item.table_name} '
                   f'WHERE {item.arguments_name}_id = %s',
                    (item_id, ))
        if not cur.fetchone()[0]:
            self.transact_ability = False
            self.needed_for_transact['saleability'] = False
            return

        cur.execute(f'SELECT get_needed_count_{item.arguments_name}(%s, %s, %s)',
                     (country_seller.id_[0], item_id, count))

        self.new_seller_count = cur.fetchone()[0]
        if self.new_seller_count < 0:
            self.transact_ability = False
            self.needed_for_transact['item'] = self.new_seller_count

        cur.execute(f'SELECT get_needed_money(%s, %s)', 
                    (country_customer.id_[0], price))

        self.new_customer_money = cur.fetchone()[0]
        if self.new_customer_money < 0:
            self.transact_ability = False
            self.needed_for_transact['money'] = self.new_customer_money

    def transact(
            self, cur: cursor, country_seller: Country, country_customer: Country,
            item: Item, item_id: int, count: int, price: int
            ):
        item_inventory = f'{item.table_name}_inventory'
        id_ = f'{item.arguments_name}_id'
        
        if self.new_seller_count > 0:
            cur.execute(f'UPDATE {item_inventory} '
                        f'SET count = %s '
                        f'WHERE country_id = %s AND {id_} = %s',
                         (self.new_seller_count, country_seller.id_[0], item_id))
        else:
            cur.execute(f'DELETE FROM {item_inventory} '
                        f'WHERE country_id = %s AND {id_} = %s',
                         (country_seller.id_[0], item_id))

        cur.execute('UPDATE countries '
                    'SET money = %s '
                    'WHERE country_id = %s',
                    (self.new_customer_money, country_customer.id_[0]))

        cur.execute(f'INSERT INTO {item_inventory}'
                    f'(country_id, {id_}, count) '
                     'VALUES(%s, %s, %s) ' 
                    f'ON CONFLICT (country_id, {id_}) DO UPDATE '
                    f'SET count = {item_inventory}.count + %s',
                     (country_customer.id_[0], item_id, count, count))

        cur.execute('UPDATE countries '
                    'SET money = countries.money + %s '
                    'WHERE country_id = %s',
                    (price, country_seller.id_[0]))
        

class Build(Item):
    table_name: str = 'builds'
    arguments_name: str = 'build'

    def buy(self, country: Country, item_id: int, count: int):
        BuyOrder(country, self, item_id, count)
    
    def sell(self, country_seller: Country, country_customer: Country,
                   item_id: int, count: int, price: int|float):
        SellOrder(country_seller, country_customer, self, item_id, count, price)

class Unit(Item):
    table_name: str = 'units'
    arguments_name: str = 'unit'

    def buy(self, country: Country, item_id: int, count: int):
        BuyOrder(country, self, item_id, count)

    def sell(self, country_seller: Country, country_customer: Country,
                   item_id: int, count: int, price: int|float):
        SellOrder(country_seller, country_customer, self, item_id, count, price)


class ItemFabric:
    def get_item(self, item: str) -> Item:
        if item in ('bu', 'build', 'builds'):
            return Build()
        elif item in ('un', 'unit', 'units'):
            return Unit()
        else:
            raise NoItem
