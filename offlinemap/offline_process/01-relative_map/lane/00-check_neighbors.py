
"""
检查lane图层的前继后记字段是否正确，如有错误通过拓扑关系进行修正，生成一个新表mod_lane
"""
import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import networkx as nx
from lib.config import pg_from,pg_map,boundary,ctf,srid
from shapely import wkt


def net_construct(df,type):
    if type == 'DiGraph':
        G = nx.DiGraph()
    if type == 'MultiGraph':
        G = nx.MultiGraph()
    for index,row in df.iterrows():
        snode = row['snode_id']
        enode = row['enode_id']
        edge = row['lane_id']
        G.add_edge(snode, enode, edge=edge)

    return G


def get_successors(DG,MG,node):
    l=[]
    DG_successors = list(DG.successors(node))
    for i in DG_successors:
        MG_data = MG.get_edge_data(node,i)
        if len(MG_data) > 1:
            for j in MG_data:
                l.append(MG_data[j]['edge'])
        else:
            l.append(DG.get_edge_data(node,i)['edge'])
    return l


def get_predecessors(DG,MG,node):
    l=[]
    DG_predecessors = list(DG.predecessors(node))
    for i in DG_predecessors:
        MG_data = MG.get_edge_data(i,node)
        if len(MG_data) > 1:
            for j in MG_data:
                l.append(MG_data[j]['edge'])
        else:
            l.append(DG.get_edge_data(i,node)['edge'])
    return l


df_lane = pg_map.get('rns_lane')
DG = net_construct(df_lane,'DiGraph')
MG = net_construct(df_lane,'MultiGraph')
no_need_list = []

for edge in DG.edges():
    snode = edge[0]
    enode = edge[1]
    df = df_lane[(df_lane.snode_id==snode)&(df_lane.enode_id==enode)]
    lane_id = DG.get_edge_data(snode,enode)['edge']
    if lane_id in no_need_list:
        pass
    else:
        if df.shape[0] == 1:
            pre_lanes = df.pre_lanes.values[0]
            suc_lanes = df.suc_lanes.values[0]
            if pre_lanes is None:
                pre_list = []
            else:
                pre_list = pre_lanes.split(':')
            if suc_lanes is None:
                suc_list = []
            else:
                suc_list = suc_lanes.split(':')
            if len(list(DG.predecessors(snode))) >= 0:
                supply_pre_list = get_predecessors(DG,MG,snode)
                supply_pre_lanes = ':'.join(supply_pre_list)
                if set(supply_pre_list) != set(pre_list):
                    df_lane.loc[df_lane.lane_id==lane_id,'pre_lanes'] = supply_pre_lanes
                    print(
                        'wrong lane id is ' + lane_id + ', wrong pre lanes is ' + ':'.join(pre_list) + ', modify pre lanes is ' + supply_pre_lanes)
            else:
                df_lane.loc[df_lane.lane_id == lane_id, pre_lanes] = ''
            if len(list(DG.successors(enode))) >= 0:
                supply_suc_list = get_successors(DG,MG,enode)
                supply_suc_lanes = ':'.join(supply_suc_list)
                if set(supply_suc_list) != set(suc_list):
                    df_lane.loc[df_lane.lane_id == lane_id, 'suc_lanes'] = supply_suc_lanes
                    print('wrong lane id is ' + lane_id + ', wrong suc lanes is ' + ':'.join(suc_list) + ', modify suc lanes is ' + supply_suc_lanes)
            else:
                df_lane.loc[df_lane.lane_id == lane_id, 'suc_lanes'] = ''
        else:
            # 存在辅路的情况，检查后发现pre和suc不需要修改，所以这里先不做处理
            print('lane id is ' + lane_id +', num is ' + str(df.shape[0]))
            pass


sql = f"drop table if exists mod_lane;"
pg_map.execute(sql)
pg_map.df_to_pg(df_lane,'mod_lane')
sql = (f"alter table mod_lane alter column geom type geometry;"
       f"alter table mod_lane alter column utm type geometry;"
       f"update mod_lane set pre_lanes = null where pre_lanes = '';"
       f"update mod_lane set suc_lanes = null where suc_lanes = '';")
pg_map.execute(sql)


index_name = 'spetial_mod_lane_on_utm'
table_name = index_name.split('spetial_')[1].split('_on')[0]
sql = f"SELECT * FROM pg_indexes WHERE schemaname = 'public' AND indexname = '{index_name}'; "
data = pg_map.execute(sql,True)
if len(data) == 0:
    sql = f"create index {index_name} on {table_name} using gist(utm);"
    pg_map.execute(sql)


index_name = 'spetial_rns_link_on_utm'
table_name = index_name.split('spetial_')[1].split('_on')[0]
sql = f"SELECT * FROM pg_indexes WHERE schemaname = 'public' AND indexname = '{index_name}'; "
data = pg_map.execute(sql,True)
if len(data) == 0:
    sql = f"create index {index_name} on {table_name} using gist(utm);"
    pg_map.execute(sql)