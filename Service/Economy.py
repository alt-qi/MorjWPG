if __name__ == '__main__':
    import sys; sys.path.append('..')

from psycopg2._psycopg import cursor

from Database.Database import database
from Service.Country import Country
from Service.exceptions import OperationOnlyForOneCountry, CantTransact


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

    def income(self):
        if self.country.len_ != 1:
            raise OperationOnlyForOneCountry
        
        return database().select_one(
            'SELECT COALESCE(get_income_country(%s), 0) AS income',
            self.country.id_[0]
        )['income']

    def pay(self, country_payee: Country, money: int|float):
        self.pay_ability = True
        self.needed_for_pay = {}

        conn = database().get_conn()
        conn.set_isolation_level('READ COMMITED')
        with conn:
            with conn.cursor() as cur:
                self._check_pay_ability(cur, country_payee, money)

                if self.pay_ability:
                    self._pay(cur, country_payee, money)
                else:
                    raise CantTransact(self.needed_for_pay)
                
    def _check_pay_ability(
            self, cur: cursor, country_payee: Country, money: int|float
            ):
        if self.country.len_ != 1 or country_payee.len_ != 1:
            raise OperationOnlyForOneCountry

        cur.execute('SELECT get_needed_money(%s, %s)',
                    (self.country.id_[0], money))
                
        self.new_money = cur.fetchone()[0]
        if self.new_money < 0:
            self.pay_ability = False
            self.needed_for_pay['money'] = self.new_money

    def _pay(self, cur: cursor, country_payee: Country, money: int|float):
        cur.execute('UPDATE countries '
                    'SET money = %s '
                    'WHERE country_id = %s',
                    (self.new_money, self.country.id_[0]))

        cur.execute('UPDATE countries '
                    'SET money = money + %s '
                    'WHERE country_id = %s',
                    (money, country_payee.id_[0]))

    def edit_money(self, money: int|float):
        print(money)
        print(self.country.where)
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
