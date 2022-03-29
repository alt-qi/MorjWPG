'''Модуль для работы с базой данных'''
import os
from abc import ABC, abstractmethod
from typing import Any

from psycopg2._psycopg import connection, cursor
from psycopg2.pool import AbstractConnectionPool, SimpleConnectionPool
import psycopg2.extras


class DataBase(ABC):
    @abstractmethod
    def get_conn(self) -> connection:
        pass

    @abstractmethod
    def put_conn(self, conn: connection):
        pass

    @abstractmethod
    def insert(self, sql: str, *values) -> None|Any:
        pass
    
    @abstractmethod
    def select(self, sql: str, *values) -> Any:
        pass

    @abstractmethod
    def select_one(self, sql: str, *values) -> Any:
        pass


class SimpleDataBase(DataBase):
    url: str = os.getenv('DATABASE_URL')
    pool: AbstractConnectionPool

    def __init__(self):
        self.pool = SimpleConnectionPool(1, 20, self.url)
        self.check_database_exists()
    
    def check_database_exists(self):
        """Создает базу данных если ее нет"""
        conn = self.get_conn()
        cur = conn.cursor()

        cur.execute('SELECT * '
                    'FROM information_schema.tables '
                    'WHERE table_name = \'countries\'')
        if not cur.fetchall:
            self.init_db(conn, cur)
        
        self.put_conn(conn)

    def init_db(self, conn: connection, cur: cursor):
        """Инициализирует базу данных"""
        with open('DataBase/create_db.sql', 'r') as r:
            sql = r.read()
        
        cur.execute(sql)
        conn.commit()
    

    def get_conn(self) -> connection:
        return self.pool.getconn()
    
    def put_conn(self, conn: connection):
        self.pool.putconn(conn)
    

    def insert(self, sql: str, *values) -> None | Any:
        conn = self.get_conn()
        cur = conn.cursor()

        cur.execute(sql, values)
        conn.commit()

        self.put_conn(conn)
    
    def select(self, sql: str, *values) -> Any:
        conn = self.get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(sql, values)
        value = cur.fetchall()
        conn.commit()

        self.put_conn(conn)
        return value

    def select_one(self, sql: str, *values) -> Any:
        conn = self.get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(sql, values)
        value = cur.fetchone()
        conn.commit()

        self.put_conn(conn)
        return value


db = SimpleDataBase()

def database() -> DataBase:
    return db
