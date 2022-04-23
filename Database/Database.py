'''Модуль для работы с базой данных'''
import os
from abc import ABC, abstractmethod
from typing import Any

from psycopg2._psycopg import connection, cursor
from psycopg2.pool import AbstractConnectionPool, SimpleConnectionPool
import psycopg2.extras


_CURENT_DATABASE_VERSION = 1.1
class Database(ABC):

    @abstractmethod
    def init_db(self, conn: connection, cur: cursor):
        pass
    
    @abstractmethod
    def update_db(self, conn: connection, cur: cursor, database_version: float):
        pass

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


class SimpleDatabase(Database):
    url = os.environ['DATABASE_URL']
    pool: AbstractConnectionPool

    def __init__(self):
        self.pool = SimpleConnectionPool(1, 20, self.url)

        self._check_database_exists()
        self._check_version_database()
    
    def _check_database_exists(self):
        """Создает базу данных если ее нет"""

        conn = self.get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT * '
                'FROM information_schema.tables '
                'WHERE table_name = \'countries\''
            )
            if not cur.fetchall():
                self.init_db(conn, cur)
        finally:
            self.put_conn(conn)

    def init_db(self, conn: connection, cur: cursor):
        """Инициализирует базу данных"""

        with open('Database/create_db.sql', 'r') as r:
            sql = r.read()
        
        cur.execute(sql)
        cur.execute(
            'INSERT INTO config(database_version) '
            'VALUES(%s)',
            (_CURENT_DATABASE_VERSION, )
        )
        conn.commit()
    
    def _check_version_database(self):
        """Проверяет, соответсутвует ли база данных текущей версии"""

        conn = self.get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT database_version '
                'FROM config '
                'LIMIT 1'
            )

            database_version = cur.fetchone()[0]
            if database_version < _CURENT_DATABASE_VERSION:
                self.update_db(conn, cur, database_version)
        finally:
            self.put_conn(conn)

    def update_db(self, conn: connection, cur: cursor, database_version: float):
        for version in self._get_range_versions(database_version):
            with open(f'Database/Versions/{version}.sql') as r:
                sql = r.read()

            cur.execute(sql)

        cur.execute(
            'UPDATE config '
            'SET database_version = %s',
            (_CURENT_DATABASE_VERSION, )
        )
        conn.commit()

    def _get_range_versions(self, database_version: float):
        for version in range(int(database_version*10+1), int(_CURENT_DATABASE_VERSION*10+1)):
            yield version/10


    def get_conn(self) -> connection:
        return self.pool.getconn()
    
    def put_conn(self, conn: connection):
        self.pool.putconn(conn)
    

    def insert(self, sql: str, *values) -> None | Any:
        conn = self.get_conn()
        try:
            cur = conn.cursor()

            cur.execute(sql, values)
            conn.commit()
        finally:
            self.put_conn(conn)
    
    def select(self, sql: str, *values) -> Any:
        conn = self.get_conn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute(sql, values)
            value = cur.fetchall()
            conn.commit()

            return value
        finally:
            self.put_conn(conn)

    def select_one(self, sql: str, *values) -> Any:
        conn = self.get_conn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute(sql, values)
            value = cur.fetchone()
            conn.commit()

            return value
        finally:
            self.put_conn(conn)


db = SimpleDatabase()

def database() -> Database:
    return db
