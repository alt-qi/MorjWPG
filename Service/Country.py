if __name__ == '__main__':
    import sys; sys.path.append('..')

from DataBase.database import database


class Country:
    """Интерфейс страны, страны должны выдавать
    информацию о себе для обращения к БД
    """
    len_: int
    id_: tuple[int]


class OneCountry(Country):
    len_: int = 1
    id_: tuple[int]
    where: str

    def __init__(self, name: str):
        self.id_ = database().select_one('SELECT country_id '
                                         'FROM countries '
                                         'WHERE name = %s', name)['country_id']
        if not self.id_:
            self.id_ = database().select_one('INSERT INTO countries(name)'
                                             'VALUES(%s) RETURNING country_id', 
                                             name)['country_id']

        self.id_ = (self.id_, )
        self.where = f'WHERE country_id = {self.id_[0]}'

class AllCountries(Country):
    len_: int = -1
    id_: tuple[int] = None
    where: str = ''
