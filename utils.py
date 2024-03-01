import os.path
import re
import sqlite3
from typing import Callable


def is_valid_string(s):
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', s))


class StorageDataEntrance:

    def __init__(self, key: str, init_sql_path: str):
        if not is_valid_string(key):
            raise Exception(f'Invalid key name: {key}')
        self.target_filepath = f"save/{key}.sqlite3"
        if not os.path.exists(self.target_filepath):
            with open(init_sql_path, 'r') as init_sql_file:
                try:
                    conn = sqlite3.connect(self.target_filepath)
                    conn.cursor().executescript(init_sql_file.read())
                except sqlite3.Error as e:
                    print('Failed to init sql script:', e)
                finally:
                    conn.close()

    def select(self, from_table: str, condition: str | None = None):
        sql = f'select * from {from_table}' + f' where {condition}' if isinstance(condition, str) else ''
        res = conn = None
        try:
            conn = sqlite3.connect(self.target_filepath)
            res = conn.cursor().execute(sql).fetchall()
        except sqlite3.Error as e:
            print('Failed to select:', sql)
            print(e)
        finally:
            conn.close()
        return res

    def insert(self, into_table: str, value: dict[str, str]):
        sql = f'insert into {into_table} (' + ', '.join(value.keys()) + ') values (' + ', '.join(value.values()) + ')'
        conn = None
        try:
            conn = sqlite3.connect(self.target_filepath)
            conn.cursor().execute(sql)
            conn.commit()
        except sqlite3.Error as e:
            print('Failed to insert:', sql)
            print(e)
        finally:
            conn.close()

    def remove(self, from_table: str, condition: str):
        sql = f'delete from {from_table} where {condition}'
        conn = None
        try:
            conn = sqlite3.connect(self.target_filepath)
            conn.cursor().execute(sql)
            conn.commit()
        except sqlite3.Error as e:
            print('Failed to remove:', sql)
            print(e)
        finally:
            conn.close()

    def update(self, table: str, set_value: dict[str, str], condition: str):
        sql = f'update {table} set ' + ', '.join(
            f'{key} = {value}' for key, value in set_value.items()) + f' where {condition}'
        conn = None
        try:
            conn = sqlite3.connect(self.target_filepath)
            conn.cursor().execute(sql)
            conn.commit()
        except sqlite3.Error as e:
            print('Failed to update:', sql)
            print(e)
        finally:
            conn.close()

    def execute(self, fun: Callable[[sqlite3.Cursor], None]):
        conn = None
        try:
            conn = sqlite3.connect(self.target_filepath)
            fun(conn.cursor())
            conn.commit()
        except sqlite3.Error as e:
            print('Failed to execute!')
            print(e)
        finally:
            conn.close()
