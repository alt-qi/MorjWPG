import sys; sys.path.append('..')

import pytest

from Database.Database import database
from Country import Country, OneCountry, AllCountries
from Economy import Economy
from Lists import Item, List, Build, Unit, Shop, Inventory
from exceptions import NoImportantParameter, OperationOnlyForOneCountry


countries = (OneCountry('Россия'), AllCountries())
@pytest.fixture(scope='class', params=countries)
def country(request):
    return request.param

class TestCountry:
    """Класс для тестирования стран"""

    def test_check_len_country(self, country: Country):
        """Проверка на длинну страны"""

        if country.id_ == None:
            assert country.len_ == -1
        else:
            assert len(country.id_) == country.len_

    def test_check_where_country(self, country: Country):
        """Проверка на правильность WHERE в странах"""

        if country.len_ == -1:
            countries = database().select('SELECT country_id '
                                          'FROM countries')
        else:
            countries = database().select('SELECT country_id '
                                          'FROM countries '
                                          'WHERE country_id IN %s',
                                          country.id_)

        countries_check = database().select('SELECT country_id '
                                            'FROM countries '
                                           f'{country.where}')
        assert countries_check == countries


class TestEconomy:
    """Класс для тестирования экономики"""

    def test_getting_money(self, country: Country):
        """Проверка на получение денег страны"""

        if country.len_ == 1:
            money = database().select_one('SELECT money '
                                          'FROM countries '
                                          'WHERE country_id = %s', country.id_)
            assert Economy(country).money() == money['money']
        else:
            with pytest.raises(OperationOnlyForOneCountry):
                Economy(country).money()

    def test_edit_money(self, country: Country):
        """Проверка на изменение денег стране"""

        get_money_query = ('SELECT money '
                           'FROM countries '
                          f'{country.where}')

        old_money = database().select(get_money_query)
        Economy(country).edit_money(100)
        new_money = database().select(get_money_query)

        for i in range(0, len(old_money)):
            assert new_money[i]['money'] - old_money[i]['money'] == 100.0

    def test_delete_money(self, country: Country):
        """Проверка на удаление денег из стран"""

        Economy(country).delete_money()
        money = database().select('SELECT money '
                                  'FROM countries '
                                 f'{country.where}')
        
        for i in money:
            assert i['money'] == 0


items = (Build(), Unit())
@pytest.fixture(scope='class', params=items)
def item(request):
    return request.param

class TestItems:
    """Проверка класса предметов"""

    @pytest.fixture(scope='function')
    def delete_item(self, item):
        delete_query = (f'DELETE FROM {item.table_name} '
                         'WHERE name IN %s')

        database().insert(delete_query, ('Test', 'Test1'))
        yield
        database().insert(delete_query, ('Test', 'Test1'))
        
    def test_create_item(self, delete_item, item: Item):
        """Проверка создания предметов"""

        test_data = {'name': 'Test',
                     'price': 19.5,
                     'description': 'Just build for test',
                     'needed_for_purchase': {1: 1,
                                             3: 2}}
        if type(item) == Build:
            test_data['income'] = 19.5
        elif type(item) == Unit:
            test_data['features'] = 'Атака: 0, Защита: 0, Скорость: 0'
        
        item.insert(test_data)
        check_data = ('SELECT * '
                     f'FROM {item.table_name} '
                      'WHERE name = %s AND price = %s AND description = %s ')
        if type(item) == Build:
            check_data = check_data + 'AND income = %s'
        elif type(item) == Unit:
            check_data = check_data + 'AND features = %s'

        check_data = database().select_one(check_data, *test_data.values())
        check_needed_for_purchase = database().select(
                'SELECT * '
               f'FROM {item.table_name}_needed_for_purchase '
               f'WHERE {item.arguments_name}_id = %s AND needed_build_id IN %s '
                'AND count IN %s', 
                check_data[f'{item.arguments_name}_id'], (1,1), (1,2))

        assert check_data and check_needed_for_purchase

    @pytest.fixture(scope='function', name='item_id')
    def create_item(self, delete_item, item: Item):
        test_data = {'name': 'Test',
                     'price': 19.5}
        if type(item) == Unit:
            test_data['features'] = 'Атака: 0, Защита: 0, Скорость: 0'

        item.insert(test_data)
        item_query = (f'SELECT {item.arguments_name}_id '
                      f'FROM {item.table_name} '
                       'WHERE name = %s')

        item_id = database().select_one(item_query, 'Test')[f'{item.arguments_name}_id']
        return item_id

    def test_update_item(self, item_id, item: Item):
        """Проверка на обновление параметров предметов"""

        item.update(item_id, parameters={'name': 'Test1',
                                         'price': 15,
                                         'needed_for_purchase': {1: 2,
                                                                 4: 1}})
        check_data = database().select('SELECT * '
                                      f'FROM {item.table_name} '
                                       'WHERE name = %s AND price = %s',
                                       'Test1', 15)
        check_needed_for_purchase = database().select(
                'SELECT * '
               f'FROM {item.table_name}_needed_for_purchase '
               f'WHERE {item.arguments_name}_id = %s AND needed_build_id IN %s '
                'AND count IN %s', item_id, (1,4), (2,1)
                )

        assert check_data and check_needed_for_purchase

    def test_delete_item(self, item_id, item: Item):
        """Проверка на удаление предмета"""

        item_query = (f'SELECT {item.arguments_name}_id '
                      f'FROM {item.table_name} '
                       'WHERE name = %s')
        item.delete(item_id)

        assert not database().select_one(item_query, 'Test')

    def test_get_item_by_name(self, item: Item):
        """Проверка на получение предметов по имени"""

        if type(item) == Build:
            assert item.get_id('мелниц')
        elif type(item) == Unit:
            assert item.get_id('пехта')

    def test_buy_item(self, item: Item, country: Country):
        """Проверка покупки предмета"""

        if country.len_ == 1:
            if type(item) == Build:
                fail_order = 'Казармы'
                fail_needed_for_buy = {'builds': {'Завод винтовок': 2}}
                pass_order = 'Мельница'
            elif type(item) == Unit:
                fail_order = 'Пехота'
                fail_needed_for_buy = {'builds': {'Казармы': 1}}
                pass_order = 'Ополчение'

            item_id = item.get_id(fail_order)[fail_order]
            order = item.order(country, item_id, 1)
            assert order.buy_ability == False and \
                   order.needed_for_buy == fail_needed_for_buy

            item_id = item.get_id(pass_order)[pass_order]
            order = item.order(country, item_id, 1)
            assert order.buy_ability == True

        else:
            with pytest.raises(OperationOnlyForOneCountry):
                item.order(country, 1, 1)
