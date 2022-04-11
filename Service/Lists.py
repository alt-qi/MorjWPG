if __name__ == '__main__':
    import sys; sys.path.append('..')
from typing import Any

from Database.Database import database
from Service.Country import Country
from Service.Items import ItemFabric, Item
from Service.exceptions import OperationOnlyForOneCountry


class List:
    """Класс списков, которые использует предметы"""
    item: Item

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
            
            print(values)
        
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

class ListFabric:
    """Класс фабрики создания списков"""

    item_fabric: ItemFabric = ItemFabric()

class ShopFabric(ListFabric):
    def get_shop(self, item: str) -> Shop:
        return Shop(self.item_fabric.get_item(item))

class InventoryFabric(ListFabric):
    def get_inventory(self, country: Country, item: str) -> Inventory:
        return Inventory(self.item_fabric.get_item(item), country)


if __name__ == '__main__':
    shop = ShopFabric().get_shop('build')
    print(shop.get_shop())