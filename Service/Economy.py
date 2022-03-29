if __name__ == '__main__':
    import sys; sys.path.append('..')

from DataBase.database import database
from Country import Country
from exceptions import OperationOnlyForOneCountry


class Economy:
    country: Country

    def __init__(self, country: Country):
        self.country = country

    def money(self):
        if self.country.len_ != 1:
            raise OperationOnlyForOneCountry
        
        return database().select_one(
            'SELECT money '
            'FROM countries '
           f'{self.country.where}'
           )['money']

    def edit_money(self, money: int):
        database().insert(
            'UPDATE countries '
            'SET money = money+%s '
           f'{self.country.where}', money
           )

    def delete_money(self):
        database().insert(
            'UPDATE countries '
            'SET money = 0 '
           f'{self.country.where}'
           )
