import os
import sqlite3
from typing import List, Tuple  


class SQLiteDB:
    def __init__(self, db_path:str, db_name:str):
        self.db_files = []
        for root, dirs, files in os.walk(db_path):
            for file in files:
                if file.startswith(db_name) and file.endswith(".db"):
                    self.db_files.append(os.path.join(root, file))
        if not self.db_files:
            raise FileNotFoundError(f"没有找到以 {db_name} 开头的数据库文件")
        print(f"找到数据库文件: {self.db_files}")
        self.dbs: List[Tuple[sqlite3.Connection, sqlite3.Cursor]] = []  # 存储数据库连接对象
        self._init()

    def _init(self):
        if not self.dbs:
            # 如果没有连接对象，则创建一个新的连接对象
            for db_file in self.db_files:
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row  # 设置行工厂为 sqlite3.Row
                cursor = conn.cursor()
                self.dbs.append((conn, cursor))

    def _close(self):
        for conn, cursor in self.dbs:
            cursor.close()
            conn.close()

    def selcet_all(self, query, params=(), batch_size=100):
        """分批获取查询结果，以字典形式返回"""
        for conn, cursor in self.dbs:
            cursor.execute(query, params)
            while True:
                rows = cursor.fetchmany(batch_size)  
                if not rows:
                    break
                for row in rows:
                    yield dict(row) 

    def select_one(self, query, params=()):
        for conn, cursor in self.dbs:
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                return dict(row)  
        return None

    def select_count(self, query, params=()):
        count = 0
        for conn, cursor in self.dbs:
            cursor.execute(query, params)
            count += cursor.fetchone()[0]
        return count
    
    def get_tables(self):
        tables = []
        for conn, cursor in self.dbs:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables.extend([row[0] for row in cursor.fetchall()])
        return tables
    
    def get_tables_row_count(self, table_name):
        return self.select_count(f"SELECT COUNT(*) FROM {table_name}")

    def __del__(self):
        self._close()


if __name__ == "__main__":
    db_path = r"T:\tmp\wechat_37260"
    db_name = "MediaMSG"
    db = SQLiteDB(db_path, db_name)
    query = 'SELECT Buf FROM Media WHERE Reserved0 = 2209954653114443726;'
    row = db.select_one(query)
    print(row)