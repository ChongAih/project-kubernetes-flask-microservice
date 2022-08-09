import functools
import sqlite3
from datetime import datetime
from sqlite3 import Error as SQLiteError, Connection, Cursor

import app
from app.util.logger import logger

DB_PATH = app.config.DB_PATH
DB_NAME = app.config.CALCULATOR_SQLITE_DB_NAME
TABLE_NAME = app.config.CALCULATOR_SQLITE_TABLE_NAME


def handle_sqlite_error(_func=None, *, db_path: str = "",
                        db_name: str = "test", msg: str = "DB issue"):
    """
        Log error and rollback if necessary in the event of SQLite error

        The below try except can be further improvised with ContextManager
        https://docs.python.org/3/library/sqlite3.html
    """

    def error_wrapper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            conn: Connection = None
            try:
                conn = sqlite3.connect(f'{db_path}/{db_name}.db')
                cur = conn.cursor()
                result = func(*args, **kwargs, cur=cur)
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


@handle_sqlite_error(db_path=DB_PATH, db_name=DB_NAME,
                     msg=f"DB issue ({DB_NAME}) - execution error")
def execute(statement: str, cur: Cursor = None):
    cur.execute(statement)
    return cur.fetchall()


@handle_sqlite_error(db_path=DB_PATH, db_name=DB_NAME,
                     msg=f"DB issue ({DB_NAME}) - insert/update error in insert_message")
def insert_json_message(task_id: str, json_message: str, table: str = TABLE_NAME, cur: Cursor = None):
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


@handle_sqlite_error(db_path=DB_PATH, db_name=DB_NAME,
                     msg=f"DB issue ({DB_NAME}) - update error in update_status_output_message")
def update_status_output_message(task_id: str, status: str, status_message: str,
                                 output: float, table: str = TABLE_NAME, cur: Cursor = None) -> None:
    cur.execute(f"""
        UPDATE {table} 
        SET status = '{status}', status_message = '{status_message}', output = {output}
        WHERE task_id = '{task_id}'""")


@handle_sqlite_error(db_path=DB_PATH, db_name=DB_NAME,
                     msg=f"DB issue ({DB_NAME}) - error while fetching records in get_json_messages")
def get_json_messages(event_time: int, table: str = TABLE_NAME, cur: Cursor = None) -> list:
    rows = []
    for row in cur.execute(f"""
        SELECT 
            json_message
        FROM {table} 
        WHERE event_time <= {event_time} and status = 'PROCESSING'
    """):
        rows.append(row[0])
    return rows


@handle_sqlite_error(db_path=DB_PATH, db_name=DB_NAME,
                     msg=f"DB issue ({DB_NAME}) - error while fetching records in get_status")
def get_status(task_id: str, table: str = TABLE_NAME, cur: Cursor = None):
    for row in cur.execute(f"""
        SELECT 
            status, status_message 
        FROM {table}
        WHERE task_id = '{task_id}'
    """):
        return row[0], row[1]
    return "NOT FOUND", "NOT FOUND"


@handle_sqlite_error(db_path=DB_PATH, db_name=DB_NAME,
                     msg=f"DB issue ({DB_NAME}) - error while fetching records in get_result")
def get_result(task_id: str, table: str = TABLE_NAME, cur: Cursor = None):
    for row in cur.execute(f"""
        SELECT 
            status, output, status_message 
        FROM {table}
        WHERE task_id = '{task_id}'
    """):
        return row[0], row[1], row[2]
    return "NOT FOUND", -1, "NOT FOUND"


def create_table(table: str = TABLE_NAME):
    execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            task_id TEXT PRIMARY KEY,
            event_time INTEGER, 
            json_message TEXT,
            status TEXT,
            status_message TEXT,
            output FLOAT
        )
    """)
