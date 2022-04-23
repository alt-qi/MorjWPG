if __name__ == '__main__':
    import sys; sys.path.append('..')
from abc import ABC, abstractmethod
from typing import Any

from psycopg2._psycopg import cursor

from Service.default import _ALL
from Database.Database import database
from Service.Country import Country
from Service.exceptions import CantTransact, NoItem


_ALL_ITEMS = _ALL

class Item(ABC):
    """
    Интерфейс предметов, они должны выдавать имя своей таблицы, 
    имя в аргументах, параметры предмета и выдавать класс заказа 
    для возможности покупки
    
    """

    table_name: str
    arguments_name: str
    
    def insert(self, parameters: dict[str, Any]):
        """
        Создание одного предмета
        Во входящее значение должен входить словарь типа `имя_столбца: значение`

        """

        needed_for_purchase = None
        if 'needed_for_purchase' in parameters:
            needed_for_purchase = parameters.pop('needed_for_purchase')

        columns = self._get_insert_columns(list(parameters.keys()))
        values = self._get_insert_values(list(parameters.values()))

        item_id = database().select_one(
            f'INSERT INTO {self.table_name}{columns} '
            f'VALUES({values}) '
            f'RETURNING {self.arguments_name}_id AS id', 
            *list(parameters.values())
        )['id']

        self._insert_needed_for_purchase_item(item_id, needed_for_purchase)
                    

    def update(self, item_id: int, parameters: dict[str, Any]):
        """
        Обновление одного предмета
        Во входящее значение должен входить словарь типа `параметр: значение`

        """

        needed_for_purchase = None
        if 'needed_for_purchase' in parameters:
            needed_for_purchase = parameters.pop('needed_for_purchase')

            database().insert(
                f'DELETE FROM {self.table_name}_needed_for_purchase '
                f'WHERE {self.arguments_name}_id = %s; '
                f'DELETE FROM {self.table_name}_groups_needed_for_purchase '
                f'WHERE {self.arguments_name}_id = %s',
                item_id, item_id
            )

            if needed_for_purchase:
                self._insert_needed_for_purchase_item(item_id, needed_for_purchase)

        columns = self._get_update_values(list(parameters.keys()))
        if columns:
            database().insert(
                f'UPDATE {self.table_name} '
                f'SET {columns} '
                f'WHERE {self.arguments_name}_id = %s', 
                *parameters.values(), item_id
            )

    def _insert_needed_for_purchase_item(
            self, item_id: int, needed_for_purchase: dict[str, Any]
    ):
        """
        Записывает необходимое для покупки предмету
        Входное значение needed_for_purchase должно иметь 
        parameters, needed_for_purchase, groups

        """

        if needed_for_purchase:
            needed_for_purchase_parameters = needed_for_purchase['parameters']
            group_needed_for_purchases = needed_for_purchase['needed_for_purchase']
            needed_for_purchase_groups = needed_for_purchase['groups']

            self._add_needed_for_purchase_group(
                    None, item_id, needed_for_purchase_parameters,
                    group_needed_for_purchases, needed_for_purchase_groups
            )

    def _add_needed_for_purchase_group(
            self, group_parent_id: int, item_id: int, parameters: dict[str, Any], 
            needed_for_purchase: list[dict[str, Any]],
            needed_for_purchase_groups: list[dict[str, Any]]
    ):
        """
        Добавляет группу необходимых для покупки зданий предмету

        """
        group_columns = list(parameters.keys())
        group_columns.append(f'{self.arguments_name}_id')
        group_columns = self._get_insert_columns(group_columns)

        group_values = list(parameters.values())
        group_values.append(f'{self.arguments_name}_id')
        group_values = self._get_insert_values(group_values)

        group_id = database().select_one(
            f'INSERT INTO {self.table_name}_groups_needed_for_purchase{group_columns} '
            f'VALUES({group_values}) '
            f'RETURNING {self.arguments_name}_group_id AS id',
             *parameters.values(), item_id
        )['id']

        if group_parent_id:
            database().insert(
                f'INSERT INTO {self.table_name}_groups_groups '
                 'VALUES(%s, %s)',
                 group_parent_id, group_id
            )

        self._insert_needed_for_purchase(group_id, item_id, needed_for_purchase)
        if needed_for_purchase_groups:
            for group in needed_for_purchase_groups:
                new_group_parameters = group['parameters']
                new_group_needed_for_purchase = group['needed_for_purchase'] \
                        if 'needed_for_purchase' in group else None
                new_group_needed_for_purchase_groups = group['needed_for_purchase_groups'] \
                        if 'needed_for_purchase_groups' in group else None

                self._add_needed_for_purchase_group(
                        group_id, item_id, new_group_parameters, 
                        new_group_needed_for_purchase,
                        new_group_needed_for_purchase_groups
                )

    def _insert_needed_for_purchase(
            self, group_id: int, item_id: int,
            needed_for_purchases: list[dict[str, Any]]
    ):
        """
        Записывает необходимые для покупки здания в группу

        """
        if needed_for_purchases:
            for needed_for_purchase in needed_for_purchases:
                needed_for_purchase_columns = list(needed_for_purchase.keys())
                needed_for_purchase_columns.append(f'{self.arguments_name}_id')
                needed_for_purchase_columns = self._get_insert_columns(needed_for_purchase_columns)

                needed_for_purchase_values = list(needed_for_purchase.values())
                needed_for_purchase_values.append(f'{self.arguments_name}_id')
                needed_for_purchase_values = self._get_insert_values(needed_for_purchase_values)

                needed_for_purchase_id = database().select_one(
                    f'INSERT INTO {self.table_name}_needed_for_purchase'
                    f'{needed_for_purchase_columns} '
                    f'VALUES({needed_for_purchase_values}) '
                    f'RETURNING {self.arguments_name}_needed_for_purchase_id AS id',
                    *needed_for_purchase.values(), item_id
                )['id']

                database().insert(
                    f'INSERT INTO {self.table_name}_needed_for_purchase_groups '
                     'VALUES(%s, %s) ',
                     group_id, needed_for_purchase_id
                )
                    
    def delete(self, item_id: int=_ALL_ITEMS):
        """
        Удалить предмет по его id

        """

        if item_id == _ALL_ITEMS:
            database().insert(
                f'TRUNCATE TABLE {self.table_name} RESTART IDENTITY CASCADE'
            )
        else:
            database().insert(
                f'DELETE FROM {self.table_name} '
                f'WHERE {self.arguments_name}_id = %s', item_id
            )

    def get_id_by_name(self, name: str) -> dict[str, int]:
        items = {}
        for item in database().select(
             'SELECT name, id '
            f'FROM get_{self.arguments_name}_id_by_name(%s)',
             name
        ):
            items[item['name']] = item['id']

        return items

    def get_all_items(self) -> dict[str, int]:
        items = {}
        for item in database().select(
            f'SELECT name, {self.arguments_name}_id AS id '
            f'FROM {self.table_name} '
        ):
            items[item['name']] = item['id']

        return items

    def get_buyable_items(self) -> dict[str, int]:
        """
        Возвращает список предметов, которые можно купить

        """

        buyable_items = {}
        for item in database().select(
            f'SELECT name, {self.arguments_name}_id AS id '
            f'FROM {self.table_name} '
             'WHERE buyability = True'
        ):
            buyable_items[item['name']] = item['id']

        return buyable_items

    def get_saleable_items(self) -> dict[str, int]:
        """
        Возвращает список предметов, которые можно продать

        """

        saleable_items = {}
        for item in database().select(
            f'SELECT name, {self.arguments_name}_id AS id '
            f'FROM {self.table_name} '
             'WHERE buyability = True'
        ):
            saleable_items[item['name']] = item['id']

        return saleable_items

    @abstractmethod
    def buy(self, country: Country, item_id: int, count: int):
        pass

    @abstractmethod
    def sell(self, country_seller: Country, country_customer: Country,
                   item_id: int, count: int, price: int):
        pass


    def _get_insert_columns(self, columns: list[str]) -> str:
        columns_output = '('+', '.join(columns)+')'

        return columns_output

    def _get_insert_values(self, values: list[Any]) -> str:
        """
        Создает строку `(%s, %s, ...)` для записи в БД

        """

        values_output = ', '.join(('%s', )*len(values))

        return values_output


    def _get_update_values(self, columns: list[str]) -> str:
        """
        Создает строку `column = %s, column = %s, ...` для обновления записи в БД

        """

        columns_output = []
        for column in columns:
            columns_output.append(f'{column} = %s')

        return ', '.join(columns_output)


class Component(ABC):
    item: Item
    item_id: int
    should_not_be: bool

    cant_transact_reason: str

    @abstractmethod
    def check_buy(self, country: Country, count: int) -> bool:
        pass

    def add_component(self, component):
        pass

    def remove_component(self, component):
        pass

class GroupBehavior(ABC):
    cant_transact_reason: str

    @abstractmethod
    def check_buy(
            self, country: Country, count: int, 
            components: list[Component], should_not_be: bool
    ) -> bool:
        pass
    
    def get_can_transacts(
            self, country: Country, count: int, 
            components: list[Component], should_not_be: bool
    ):
        
        for component in components:
            can_transact = component.check_buy(country, count)
            can_transact = not can_transact if should_not_be else can_transact

            yield can_transact, component


class NeededForPurchase(Component):
    item: Item
    needed_build_id: int
    count: int
    should_not_be: bool
    proportionally_items: bool

    cant_transact_reason: str

    def __init__(self, item: Item, needed_for_purchase_id: int):
        needed_for_purchase_info = database().select_one(
           f'SELECT {item.arguments_name}_id, needed_build_id, count, should_not_be, proportionally_items '
           f'FROM {item.table_name}_needed_for_purchase '
           f'WHERE {item.arguments_name}_needed_for_purchase_id = %s',
            needed_for_purchase_id
        )
        self.item = item
        self.build_id = needed_for_purchase_info[f'{item.arguments_name}_id']
        self.needed_build_id = needed_for_purchase_info['needed_build_id']
        self.count = needed_for_purchase_info['count']
        self.should_not_be = needed_for_purchase_info['should_not_be']
        self.proportionally_items = needed_for_purchase_info[f'proportionally_items']

    def check_buy(self, country: Country, count: int):
        needed_build_count = self._get_needed_build_count(country, count)
        needed_build_count = database().select_one(
            'SELECT get_needed_count_build(%s, %s, %s) AS needed_build_count',
            country.id_[0], self.needed_build_id, needed_build_count
        )['needed_build_count']
        needed_build_count = needed_build_count*-1 if self.should_not_be else needed_build_count
        
        self.cant_transact_reason = ''
        build_name = database().select_one(
            'SELECT name '
            'FROM builds '
            'WHERE build_id = %s',
            self.needed_build_id
        )['name']
        self.cant_transact_reason+=\
                f'{build_name}: {needed_build_count if self.should_not_be else needed_build_count*-1}, '

        if (needed_build_count>0 if self.should_not_be else needed_build_count>=0):
            return True
        

    def _get_needed_build_count(self, country: Country, count: int):
        if self.proportionally_items:
            country_item_count = database().select_one(
                'WITH item_count AS ( '
                    'SELECT country_id, count '
                   f'FROM {self.item.table_name}_inventory '
                   f'WHERE country_id = %s AND {self.item.arguments_name}_id = %s) '
                'SELECT COALESCE(count, 0) AS count '
                'FROM countries '
                'LEFT JOIN item_count USING(country_id)',
                country.id_[0], self.build_id
            )['count']
            return (count+country_item_count)*self.count
        else:
            return self.count


class AllGroupBehavior(GroupBehavior):
    cant_transact_reason: str
    can_transact: bool

    def check_buy(
            self, country: Country, count: int, 
            components: list[Component], should_not_be: bool
    ):  
        self.cant_transact_reason = ''
        self.can_transact = True
        for can_transact, component in self.get_can_transacts(
                country, count, components, should_not_be
            ):
            if not can_transact:
                self.can_transact = False
                self.cant_transact_reason+=component.cant_transact_reason

        if not self.can_transact and should_not_be:
            self.cant_transact_reason = \
                    'Не должны выпоняться условия: '+self.cant_transact_reason
        elif not self.can_transact:
            self.cant_transact_reason = \
                    'Должны выполняться условия: '+self.cant_transact_reason

        return self.can_transact
                
class AnyGroupBehavior(GroupBehavior):
    cant_transact_reason: str
    can_transact: bool

    def check_buy(
            self, country: Country, count: int,
            components: list[Component], should_not_be: bool
    ):
        self.cant_transact_reason = ''
        self.can_transact = False
        for can_transact, component in self.get_can_transacts(
                country, count, components, should_not_be
            ):
            if can_transact:
                self.can_transact = True
                break
            else:
                self.cant_transact_reason+=component.cant_transact_reason

        if not self.can_transact and should_not_be:
            self.cant_transact_reason = \
                    'Не должно выполняться какое либо из условий: '+self.cant_transact_reason
        elif not self.can_transact:
            self.cant_transact_reason = \
                    'Должно выполняться какое либо из условий: '+self.cant_transact_reason

        return self.can_transact

class GroupNeededForPurchase(Component):
    """
    Класс представляющий группу необходимых для покупки предмета зданий

    """

    item: Item
    should_not_be: bool
    type: GroupBehavior
    components: list[Component]

    cant_transact_reason: str

    def __init__(self, item: Item, group_id: int):
        group_info = database().select_one(
            'SELECT should_not_be, type '
           f'FROM {item.table_name}_groups_needed_for_purchase '
           f'WHERE {item.arguments_name}_group_id = %s',
            group_id
        )

        self.should_not_be = group_info['should_not_be']
        if group_info['type'] == 'All': self.type = AllGroupBehavior()
        elif group_info['type'] == 'Any': self.type = AnyGroupBehavior()

        needed_for_purchases = database().select(
           f'SELECT {item.arguments_name}_needed_for_purchase_id AS id '
           f'FROM {item.table_name}_needed_for_purchase_groups '
           f'WHERE {item.arguments_name}_group_id = %s',
            group_id
        )
        self.components = []
        for needed_for_purchase in needed_for_purchases:
            self.add_component(NeededForPurchase(item, needed_for_purchase['id']))

        needed_for_purchase_groups = database().select(
           f'SELECT included_{item.arguments_name}_group_id AS id '
           f'FROM {item.table_name}_groups_groups '
           f'WHERE {item.arguments_name}_group_id = %s',
            group_id
        )
        for group in needed_for_purchase_groups:
            self.add_component(GroupNeededForPurchase(item, group['id']))

    def check_buy(self, country: Country, count: int) -> bool:
        can_transact = self.type.check_buy(
                country, count, self.components, self.should_not_be
        )
        self.cant_transact_reason = self.type.cant_transact_reason

        return can_transact

    def add_component(self, component: Component):
        self.components.append(component)

    def remove_component(self, component: Component):
        self.components.remove(component)

    
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

    def _check_ability(self, cur: cursor, item: Item, item_id: int, ability: str):
        cur.execute(
            f'SELECT {ability} '
            f'FROM {item.table_name} '
            f'WHERE {item.arguments_name}_id = %s',
             (item_id, )
        )
        if not cur.fetchone()[0]:
            self.transact_ability = False
            self.needed_for_transact[ability] = False
            return False

        return True
    

class BuyOrder(Order):
    transact_ability: bool
    needed_for_transact: dict[str, Any]

    def check_transact_ability(
        self, cur: cursor, country: Country, item: Item, item_id: int, count: int
    ):
        assert country.len_ == 1
                
        if not self._check_ability(cur, item, item_id, 'buyability'): return
        self._check_money(cur, country, item, item_id, count)
        self._check_needed_for_purchase(cur, country, item, item_id, count)
        
    def _check_money(
        self, cur: cursor, country: Country, item: Item, item_id: int, count: int
    ):
        cur.execute(
            f'SELECT get_needed_price_for_{item.arguments_name}'
             '(%s, %s, %s) AS money',
             (country.id_[0], item_id, count)
        )
        self.money = cur.fetchone()[0]
        
        if self.money < 0.0:
            self.transact_ability = False
            self.needed_for_transact['money'] = self.money

    def _check_needed_for_purchase(
        self, cur: cursor, country: Country, item: Item, item_id: int, count: int
    ):
        cur.execute(
            f'SELECT {item.arguments_name}_group_id '
            f'FROM {item.table_name}_groups_needed_for_purchase '
            f'WHERE {item.arguments_name}_id = %s',
             (item_id, )
        )
        if group_id := cur.fetchone():
            group = GroupNeededForPurchase(item, group_id[0])

            if not group.check_buy(country, count):
                self.transact_ability = False
                self.needed_for_transact['builds'] = group.cant_transact_reason


    def transact(self, cur: cursor, country: Country, item: Item, 
                 item_id: int, count: int):
        item_inventory = f'{item.table_name}_inventory'
        id_ = f'{item.arguments_name}_id'

        cur.execute(
            f'INSERT INTO {item_inventory}'
            f'(country_id, {id_}, count) '
             'VALUES(%s, %s, %s) ' 
            f'ON CONFLICT (country_id, {id_}) DO UPDATE '
            f'SET count = {item_inventory}.count + %s',
            (country.id_[0], item_id, count, count)
        )

        cur.execute(
            'UPDATE countries '
            'SET money = %s '
            'WHERE country_id = %s;',
            (self.money, country.id_[0])
        )

class SellOrder(Order):
    transact_ability: bool
    needed_for_transact: dict[str, Any]

    def check_transact_ability(
            self, cur: cursor, country_seller: Country, country_customer: Country,
            item: Item, item_id: int, count: int, price: int
    ):
        assert country_seller.len_ == 1 and country_customer.len_ == 1

        if not self._check_ability(cur, item, item_id, 'saleability'): return
        self._check_seller_item_count(cur, country_seller, item, item_id, count)
        self._check_customer_money(cur, country_customer, price)

    def _check_seller_item_count(
            self, cur: cursor, country_seller: Country, 
            item: Item, item_id: int, count: int
    ):
        cur.execute(
            f'SELECT get_needed_count_{item.arguments_name}(%s, %s, %s)',
             (country_seller.id_[0], item_id, count)
        )
        self.new_seller_count = cur.fetchone()[0]
        if self.new_seller_count < 0.0:
            self.transact_ability = False
            self.needed_for_transact['item'] = self.new_seller_count

    def _check_customer_money(
            self, cur: cursor, country_customer: Country, price: float
    ):
        cur.execute(f'SELECT get_needed_money(%s, %s)', 
                     (country_customer.id_[0], price))

        self.new_customer_money = cur.fetchone()[0]
        if self.new_customer_money < 0.0:
            self.transact_ability = False
            self.needed_for_transact['money'] = self.new_customer_money


    def transact(
            self, cur: cursor, country_seller: Country, country_customer: Country,
            item: Item, item_id: int, count: int, price: int
    ):
        item_inventory = f'{item.table_name}_inventory'
        id_ = f'{item.arguments_name}_id'
        
        if self.new_seller_count > 0.0:
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


if __name__ == '__main__':
    item = Build()
    item.update(
        10,
        {'needed_for_purchase': 
            {'parameters': {'should_not_be': True},
             'needed_for_purchase': [{'needed_build_id': 9, 'count': 2, 'proportionally_items': True}, ],
             'groups': [{'parameters': {'type': 'Any'}, 'needed_for_purchase': [{'needed_build_id': 11, 'count': 5}], 'groups': []}]
             }
            }
        )

