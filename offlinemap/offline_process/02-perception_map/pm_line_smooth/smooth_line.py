# -*- coding: UTF-8 -*-
# import pandas as pd
# from scripts.config import pg_map
# import numpy as np
import json
import os,sys
path = os.path.dirname(os.path.join(os.path.abspath(__file__)))
print(path)
# sys.path.append(os.path.join(os.path.dirname(__file__), "build"))
sys.path.append(path)
import spline.spline_demo.static_libs.pybind_solver as pybind_solver
# from shapely.geometry import Point 

# '''
# pybind_solver result: 
# std::vector<std::vector<double>> results(6);
# results[0] = std::move(smooth_x);
# results[1] = std::move(smooth_y);
# results[2] = std::move(smooth_s);
# results[3] = std::move(smooth_heading);
# results[4] = std::move(smooth_kappa);, kappa = 1/r (curvature)
# results[5] = std::move(smooth_dkappa);
# '''

# def group_curvatures(curvatures):
#     intervals = [
#         (0, 50),        # 区间 [0, 50]
#         (50, 2000),     # 区间 (50, 2000]
#         (2000, 10000)   # 区间 (2000, 10000]
#     ]
#     # 初始化存储结果的列表
#     result = []
#     current_group = []  # 存放当前区间的元素
#     current_interval = None  # 当前区间
    
#     # 遍历输入的曲率半径列表
#     for curvature in curvatures:
#         # 判断曲率半径属于哪个区间
#         if 0 <= 1/curvature <= 50:
#             interval = intervals[0]
#         elif 50 < 1/curvature <= 2000:
#             interval = intervals[1]
#         elif 2000 < 1/curvature:
#             interval = intervals[2]
#         else:
#             raise ValueError(f"曲率半径 {curvature} 不在指定的区间范围内")
        
#         # 如果当前元素属于新的区间或当前区间为空
#         if interval != current_interval:
#             # 如果有已收集的组，将其添加到结果列表中
#             if current_group:
#                 result.append(current_group)
#             # 初始化新的分组
#             current_group = [curvature]
#             current_interval = interval
#         else:
#             # 否则，继续添加到当前组
#             current_group.append(curvature)
    
#     # 添加最后一个分组到结果中
#     if current_group:
#         result.append(current_group)
    
#     idx = []
#     x = 0
#     for i in result:
#         l = []
#         for j in i:
#             l.append(x)
#             x+=1
#         idx.append(l)

#     return result,idx


# def thin_smooth_points(group_kappas,group_idx,result):
#     thin_idx = []
#     for index,group in enumerate(group_kappas):
#         curvature = 1/group[0]
#         if 0 <= curvature <= 50:
#             interval = 2
#         elif 50 < curvature <= 2000:
#             interval = 4
#         elif 2000 < curvature:
#             interval = 8
#         for idx in range(0,len(group),interval):
#             thin_idx.append(group_idx[index][idx])
#         if thin_idx[-1] != group_idx[index][-1]:
#             thin_idx.append(group_idx[index][-1])

#     x = [float(result[0][x]) for x in thin_idx]
#     y = [float(result[1][x]) for x in thin_idx]
#     s = [float(result[2][x]) for x in thin_idx]
#     heading = [float(result[3][x]) for x in thin_idx]
#     kappa = [float(result[4][x]) for x in thin_idx]

#     return x,y,s,heading,kappa


    
# with open('dic_remake_xy.json','r') as f:
#     dic_remake_xy = json.load(f)
# df_lane_lines = pg_map.get('pm_lane_lines')
# dic_lane_lines = {}
# solver = pybind_solver.Solver()
# df_lines = pd.DataFrame()


# line_ids = list(set(df_lane_lines['line_id'].tolist()))
# # line_ids = ['1']
# for line_id in line_ids[0:]:
#     print(line_id)
#     row = df_lane_lines[df_lane_lines.line_id==int(line_id)].iloc[0]
#     remake_x,remake_y,start_heading,end_heading = dic_remake_xy[str(line_id)]
#     # print(remake_x)
#     # print(remake_y)
#     solver.init(remake_x,remake_y,start_heading,end_heading)
#     result = solver.get_solution()
#     kappas = [abs(float(x)) for x in result[4]]
#     group_kappas,group_idx = group_curvatures(kappas)
#     x,y,s,heading,kappa = thin_smooth_points(group_kappas,group_idx,result)
#     # print(x)
#     # print(y)
#     sequence = [x+1 for x in range(len(s))]
#     geometry = [ctf.lonlat(Point(i[0],i[1])).wkt for i in zip(x,y)] 
#     link_id = [row['link_id'] for i in range(len(s))]
#     related_feature_point_id = [row['related_feature_point_id'] for i in range(len(s))]
#     line_type = [row['line_type'] for i in range(len(s))]
#     line_color = [row['line_color'] for i in range(len(s))]
#     is_virtual = [row['is_virtual'] for i in range(len(s))]
#     side = [row['side'] for i in range(len(s))]
#     alane_id = [row['alane_id'] for i in range(len(s))]
#     marking_id = [row['marking_id'] for i in range(len(s))]
#     is_virtual_mod = [row['is_virtual_mod'] for i in range(len(s))]
#     type_has_change = [row['type_has_change'] for i in range(len(s))]
#     dic = {'line_id':[line_id for i in range(len(s))],'related_feature_point_id':related_feature_point_id,'s_offset':s,'heading':heading,
#         'curvature':kappa,'line_type':line_type,'line_color':line_color,'is_virtual':is_virtual,'x':x,'y':y,
#         'sequence':sequence,'geometry':geometry,'link_id':link_id,'side':side,'alane_id':alane_id,'marking_id':marking_id,'geom':geometry,
#         'is_virtual_mod':is_virtual_mod,'type_has_change':type_has_change,'dist_on_alane':sequence}
#     df1 = pd.DataFrame(dic)
#     df_lines = pd.concat([df_lines, df1], ignore_index=True)


# l=[]
# new_id = 1
# for index,row in df_lines.iterrows():
#     l.append(new_id)
#     new_id+=1
# df_lines['lane_line_id'] = l
# df=df_lines.drop_duplicates(subset=['geometry','line_id', 'side'])

# l = []
# dic={}
# uuid=0
# for geometry,group in df.groupby('geometry'):
#     uuid+=1
#     for index,row in group.iterrows():
#         lane_line_id = row['lane_line_id']
#         dic[lane_line_id] = uuid
# for index,row in df.iterrows():
#     lane_line_id = row['lane_line_id']
#     l.append(dic[lane_line_id])

# df['uuid'] = l

# sql = "drop table if exists smooth_lane_lines;"
# pg_map.execute(sql)
# pg_map.df_to_pg(df,'smooth_lane_lines')
# sql = ("alter table smooth_lane_lines alter column geom type geometry;")
# pg_map.execute(sql)




