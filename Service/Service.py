from typing import Any
import sys; sys.path.append('.')

from DataBase.database import database

from abc import ABC, abstractmethod


class Country(ABC):
    '''Интерфейс страны, страны должны выдавать
    информацию о себе для обращения к БД'''
    @abstractmethod
    def get_access(self) -> dict[str: Any]:
        pass


class OneCountry(Country):
    def __init__(self, name: str):
        db = database()

        self.id = db.select('SELECT id FROM Country WHERE name = %s', name)
        if not self.id:
            self.id = db.select('INSERT INTO Country(name, money, income) VALUES(%s, %s, %s) RETURNING id', name, 0, 0)
        
        self.id = self.id[0]
    
    def get_access(self) -> dict[str: Any]:
        return {'from': 'Country',
                'where': f'id = {self.id}'}

class AllCountries(Country):
    def get_access(self) -> dict[str: Any]:
        return {'from': 'Country',
                'where': None}