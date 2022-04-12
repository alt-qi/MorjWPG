if __name__ == '__main__':
    import sys; sys.path.append('..')
from abc import ABC, abstractmethod
from datetime import time, timezone, timedelta, datetime
import threading

from Database.Database import database


offset = timezone(timedelta(hours=3))

class Observer(ABC):
    """
    Класс наблюдателя, нужен, чтобы публикатор(который выдает доход)
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
    income_time: int
    timer: threading.Timer

    def __init__(self):
        self.observers = []

        self.timer = None
        self.start_timer()
    
    def income(self):
        database().insert('SELECT give_out_income()')
        self.notify()

        self.start_timer()


    def start_timer(self):
        self._get_income_time()
        
        if self.timer:
            self.timer.cancel()

        if self.income_time:
            self.timer = threading.Timer(self.income_time, self.income)
            self.timer.start()
    
    def _get_income_time(self):
        now_datetime = datetime.now(offset)+timedelta(minutes=1)
        self.income_time = database().select_one(
                'SELECT get_next_income_time(%s) AS income_time',
                now_datetime)['income_time']

        if self.income_time:
            now_time = time(hour=now_datetime.hour, minute=now_datetime.minute)
            income_datetime = datetime(
                year=now_datetime.year, 
                month=now_datetime.month, 
                day=now_datetime.day,
                hour=self.income_time.hour,
                minute=self.income_time.minute,
                tzinfo=offset
            )
            if now_time>self.income_time:
                income_datetime+timedelta(days=1)

            self.income_time = (income_datetime-now_datetime).seconds
    

    def get_income_times(self):
        income_times = []
        for i in database().select(
            'SELECT income_time '
            'FROM income_times '
            'ORDER BY income_time'
            ):
            income_times.append(str(i['income_time']))
        
        return income_times
    
    def add_income_time(self, time_: time):
        database().insert('INSERT INTO income_times '
                          'VALUES(%s)', time_)
        self.start_timer()

    def delete_income_time(self, time_: time):
        database().insert('DELETE FROM income_times '
                          'WHERE income_time = %s',
                          time_)
        self.start_timer()
