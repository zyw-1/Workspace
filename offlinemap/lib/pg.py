# -*- coding: utf-8 -*-
"""
@Time ：2023/8/16 16:18
@Auth ：卢岩
@File ：pg.py
@Desc ：操作postgresql的类
"""

import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine
from urllib import parse


class PostgreSQL:
    def __init__(self, url):
        '''
        :param url: username:password@localhost:port/dbname
        '''
        self.host = url.split('@')[-1].split(':')[0]
        self.port = int(url.split('@')[-1].split(':')[1].split('/')[0])
        self.user = url.split(':')[0]
        self.database = url.split('/')[-1]
        self.password = url.split(':',maxsplit=1)[1].split('@' + url.split('@')[-1])[0]
        self.db = self.connect()

    def connect(self):
        connection = pg.connect(database=self.database, user=self.user, password=self.password, host=self.host,
                                port=self.port)
        return connection

    def get(self, table_name, query_sql=None):
        curs = self.db.cursor()
        if query_sql is None:
            sql = f"select * from {table_name}"
        else:
            sql = query_sql
        curs.execute(sql)
        data = curs.fetchall()
        sql = f"select column_name from information_schema.columns where table_schema=\'public\' and table_name= \'{table_name}\'"
        curs.execute(sql)
        listname = [i[0].lower() for i in curs.fetchall()]
        df = pd.DataFrame(data, columns=listname)

        return df

    def execute(self, sql, return_data=False):
        curs = self.db.cursor()
        try:
            curs.execute(sql)
            if return_data:
                data = list(curs.fetchall())
                return data
            self.db.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.db.rollback()  # 回滚以前的命令以避免事务阻塞
            curs.close()  # 关闭当前游标
            curs = self.db.cursor()  # 创建新的游标以继续后续操作
        finally:
            curs.close()  # 确保游标被正确关闭

    def df_to_pg(self,df,table_name):
        password = parse.quote_plus(self.password)
        engine = create_engine(
            'postgresql+psycopg2://' + self.user + ':' + password + '@' + self.host + ':' + str(self.port) + '/' + self.database)
        df.to_sql(name=table_name, con=engine, index=False)





