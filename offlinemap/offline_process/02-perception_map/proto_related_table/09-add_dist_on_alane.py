# -*- coding: UTF-8 -*-
"""
将perception map中的所有道路元素绑定到alane上，计算元素到alane起点的偏移量，用于在alane上将道路元素由近到远排序
"""
import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg,ctf
import pandas as pd
from shapely import wkt,wkb
import warnings

warnings.filterwarnings('ignore')


def find_longest_alane(alane_ids):
    alane_ids = [int(x) for x in alane_ids.split(':')]
    df = df_alane[df_alane.alane_id.isin(alane_ids)]
    dic = {}
    for index,row in df.iterrows():
        id = row['alane_id']
        utm = wkb.loads(row['utm'],hex=True)
        length = utm.length
        dic[id] = length
    dic = {k: v for k, v in sorted(dic.items(), key=lambda item: item[1],reverse=True)}
    return list(dic.keys())[0]


def add_dist(table,df_alane,id_column):
    if table in ['pm_stop_lines','pm_junction_lights','pm_cross_walks']:
        l = []
        df = pg.get(table)
        for alane_ids, group in df.groupby('alane_ids'):
            alane_id = find_longest_alane(alane_ids)
            df1 = df_alane[df_alane['alane_id']==alane_id]
            alane_geom = ctf.utm(wkt.loads(df1['geometry'].values[0]))
            for index,row in group.iterrows():
                geom = ctf.utm(wkt.loads(row['geometry']))
                point = geom.representative_point()
                # line = alane_geom.interpolate(alane_geom.project(point))
                distance = alane_geom.project(point)
                dic = {f"{id_column}":row[id_column],'dist_on_alane':distance}
                l.append(dic)
        df=pd.DataFrame(l)
        if df.shape[0] > 0:
            sql = "drop table if exists df;"
            pg.execute(sql)
            pg.df_to_pg(df,'df')
            sql = (f"alter table {table} drop column if exists dist_on_alane;"
                f"alter table {table} add column dist_on_alane numeric;"
                f"update {table} a set dist_on_alane = df.dist_on_alane from df where df.{id_column} = a.{id_column}")
            pg.execute(sql)
    else:
        l = []
        df = pg.get(table)
        for alane_id, group in df.groupby('alane_id'):
            df1 = df_alane[df_alane['alane_id']==alane_id]
            alane_geom = ctf.utm(wkt.loads(df1['geometry'].values[0]))
            for index,row in group.iterrows():
                geom = ctf.utm(wkt.loads(row['geometry']))
                point = geom.representative_point()
                # line = alane_geom.interpolate(alane_geom.project(point))
                distance = alane_geom.project(point)
                dic = {f"{id_column}":row[id_column],'dist_on_alane':distance}
                l.append(dic)
        df=pd.DataFrame(l)
        if df.shape[0] > 0:
            sql = "drop table if exists df;"
            pg.execute(sql)
            pg.df_to_pg(df,'df')
            sql = (f"alter table {table} drop column if exists dist_on_alane;"
                f"alter table {table} add column dist_on_alane numeric;"
                f"update {table} a set dist_on_alane = df.dist_on_alane from df where df.{id_column} = a.{id_column}")
            pg.execute(sql)


# 处理lane_lines和feature_points，直接用sequence代替在alane上的距离
sql = ("alter table pm_lane_lines drop column if exists dist_on_alane;"
        "alter table pm_lane_lines add column dist_on_alane numeric;"
        "update pm_lane_lines set dist_on_alane = sequence::numeric;"
        "alter table pm_feature_points drop column if exists dist_on_alane;"
        "alter table pm_feature_points add column dist_on_alane numeric;"
        "update pm_feature_points a set dist_on_alane = b.dist_on_alane from pm_lane_lines b where b.related_feature_point_id = a.feature_point_id;")
pg.execute(sql)

df_alane = pg.get('alane')
dic_table = {'pm_cross_walks':'cross_walk_id','pm_junction_lights':'junction_light_id','pm_lane_arrows':'lane_arrow_id','pm_stop_lines':'stop_line_id'}

for table in dic_table:
    print(table)
    id_column = dic_table[table]
    add_dist(table, df_alane, id_column)








