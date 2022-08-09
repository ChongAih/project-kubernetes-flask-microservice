import functools
import sqlite3
from datetime import datetime
from sqlite3 import Error as SQLiteError, Connection, Cursor
from typing import Optional

from app.config import Config
from app.util.logger import logger


class CalculatorDatabase:
    __DB_PATH_VAR: str = "DB_PATH"
    __DB_NAME_VAR: str = "DB_NAME"
    __CLASSNAME: str = "CalculatorDatabase"

    def __init__(self, config: Config):
        self.config = config
        self.DB_PATH = self.config.DB_PATH
        self.DB_NAME = self.config.CALCULATOR_SQLITE_DB_NAME
        self.TABLE_NAME = self.config.CALCULATOR_SQLITE_TABLE_NAME

    def _handle_sqlite_error(_func=None, *, db_path_var: str = __DB_PATH_VAR,
                             db_name_var: str = __DB_NAME_VAR, msg: str = "DB issue"):
        def error_wrapper(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                conn: Optional[Connection] = None
                try:
                    # Get runtime instance db_path & db_name
                    db_path = getattr(self, db_path_var)
                    db_name = getattr(self, db_name_var)
                    conn = sqlite3.connect(f'{db_path}/{db_name}.db')
                    cur = conn.cursor()
                    result = func(self, *args, **kwargs, cur=cur)
                    conn.commit()
                    return result
                except SQLiteError as e:
                    logger.error(e, exc_info=True)
                    # rollback to the last commit
                    if conn:
                        conn.rollback()
                    raise SQLiteError(f"{msg} - {repr(e)}")
                finally:
                    if conn:
                        conn.close()

            return wrapper

        return error_wrapper(_func) if (_func) else error_wrapper

    @_handle_sqlite_error(msg=f"DB issue ({__CLASSNAME}) - execution error")
    def execute(self, statement: str, cur: Cursor = None):
        cur.execute(statement)
        return cur.fetchall()

    @_handle_sqlite_error(msg=f"DB issue ({__CLASSNAME}) - insert/update error in insert_message")
    def insert_json_message(self, task_id: str, json_message: str, cur: Cursor = None):
        table = self.TABLE_NAME
        cur.execute(f"""
            INSERT INTO {table}(
                task_id, event_time, json_message, status, status_message
            ) 
            VALUES ('{task_id}',{int(datetime.now().strftime('%s'))}, '{json_message}', 'PROCESSING', 'PROCESSING')
            ON CONFLICT(task_id) DO 
            UPDATE SET 
            json_message = '{json_message}',
            status = 'PROCESSING'
        """)

    @_handle_sqlite_error(msg=f"DB issue ({__CLASSNAME}) - update error in update_status_output_message")
    def update_status_output_message(self, task_id: str, status: str, status_message: str,
                                     output: float, cur: Cursor = None) -> None:
        table = self.TABLE_NAME
        cur.execute(f"""
            UPDATE {table} 
            SET status = '{status}', status_message = '{status_message}', output = {output}
            WHERE task_id = '{task_id}'""")

    @_handle_sqlite_error(msg=f"DB issue ({__CLASSNAME}) - error while fetching records in get_json_messages")
    def get_json_messages(self, event_time: int, cur: Cursor = None) -> list:
        table = self.TABLE_NAME
        rows = []
        for row in cur.execute(f"""
            SELECT 
                json_message
            FROM {table} 
            WHERE event_time <= {event_time} and status = 'PROCESSING'
        """):
            rows.append(row[0])
        return rows

    @_handle_sqlite_error(msg=f"DB issue ({__CLASSNAME}) - error while fetching records in get_status")
    def get_status(self, task_id: str, cur: Cursor = None):
        table = self.TABLE_NAME
        for row in cur.execute(f"""
            SELECT 
                status, status_message 
            FROM {table}
            WHERE task_id = '{task_id}'
        """):
            return row[0], row[1]
        return "NOT FOUND", "NOT FOUND"

    @_handle_sqlite_error(msg=f"DB issue ({__CLASSNAME}) - error while fetching records in get_result")
    def get_result(self, task_id: str, cur: Cursor = None):
        table = self.TABLE_NAME
        for row in cur.execute(f"""
            SELECT 
                status, output, status_message 
            FROM {table}
            WHERE task_id = '{task_id}'
        """):
            return row[0], row[1], row[2]
        return "NOT FOUND", -1, "NOT FOUND"

    def create_table(self):
        table = self.TABLE_NAME
        self.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                task_id TEXT PRIMARY KEY,
                event_time INTEGER, 
                json_message TEXT,
                status TEXT,
                status_message TEXT,
                output FLOAT
            )
        """)
