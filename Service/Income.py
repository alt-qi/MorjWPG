if __name__ == '__main__':
    import sys; sys.path.append('..')
from abc import ABC, abstractmethod
from typing import Any

from Database.database import database
from Country import Country
from exceptions import OperationOnlyForOneCountry


class Observer(ABC):
    """Класс наблюдателя, нужен, чтобы публикатор(который выдает доход)
    уведомлял наблюдателей об этом
    """

    @abstractmethod
    def update(self):
        pass

class Publisher(ABC):
    """Класс публикатора, который уведомляет наблюдателей(о выдаче дохода)"""

    observers: list[Observer]

    def add_observer(self, observer: Observer):
        self.observers.append(observer)

    def remove_observer(self, observer: Observer):
        self.observers.remove(observer)

    def notify(self):
        for i in self.observers:
            i.update()


class Income(Publisher):
    observers: list[Observer]
    income_times: list[datetime]

    def __init__(self)
