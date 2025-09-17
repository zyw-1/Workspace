# -*- coding: UTF-8 -*-
import pandas as pd
from scripts.config import pg_map
import numpy as np
import json


def mark_in_which_line(mark_id):
    line_id = df_lane_lines[df_lane_lines.marking_id==str(mark_id)]['line_id'].values[0]
    return line_id


def line_start_and_end_mark(line_id):
    df=df_lane_lines[df_lane_lines.line_id==line_id].sort_values('s_offset')
    heading_list = df['heading'].tolist()
    all_mark_ids = df['marking_id'].tolist()
    mark_ids = []
    for i in all_mark_ids:
        if i not in mark_ids:
            mark_ids.append(i)
    return mark_ids[0],mark_ids[-1],heading_list[0],heading_list[-1]


def heading_to_degree(heading):
    heading_deg = np.degrees(heading)
    heading_deg = (heading_deg + 360) % 360
    return heading_deg


def headings_diff(heading1,heading2):
    if abs(heading_to_degree(heading1) - heading_to_degree(heading2)) > 5:
        return False
    else:
        return True


def neighbor_is_smooth(line_id):
    dic_suc,dic_pre = {},{}
    start_mark,end_mark,start_heading,end_heading = line_start_and_end_mark(line_id)

    pre_marks = df_mark[df_mark.marking_id==str(start_mark)]['pre_marks'].values[0]
    if pd.isna(pre_marks):
        pre_marks = []
    else:
        pre_marks = pre_marks.split(':')
    for mark in pre_marks:
        df = df_lane_lines[df_lane_lines.marking_id==str(mark)].sort_values('s_offset')
        try:
            compare_heading = df['heading'].tolist()[-1]
            dic_pre[mark] = headings_diff(compare_heading,start_heading)
        except:
            pass

    suc_marks = df_mark[df_mark.marking_id==str(end_mark)]['suc_marks'].values[0]
    if pd.isna(suc_marks):
        suc_marks = []
    else:
        suc_marks = suc_marks.split(':')
    for mark in suc_marks:
        df = df_lane_lines[df_lane_lines.marking_id==str(mark)].sort_values('s_offset')
        try:
            compare_heading = df['heading'].tolist()[0]
            dic_suc[mark] = headings_diff(compare_heading,end_heading)
        except:
            pass

    return dic_suc,dic_pre


def func(dic):
    if len(dic) > 0:
        s = list(set([dic[x] for x in dic]))
        if len(s) == 2:
            return 'true-false'
        else:
            if s[0] == True:
                return 'true'
            else:
                return 'false'
    else:
        return 'true'


df_mark = pg_map.get('mod_mark')
df_lane_lines = pg_map.get('pm_lane_lines')


dic_neighbor_num = {}
for line_id,group in df_lane_lines.groupby('line_id'):
    start_mark,end_mark,start_heading,end_heading = line_start_and_end_mark(line_id)
    pre_marks = df_mark[df_mark.marking_id==str(start_mark)]['pre_marks'].values[0]
    if pd.isna(pre_marks):
        pre_marks = []
    else:
        pre_marks = pre_marks.split(':')
    suc_marks = df_mark[df_mark.marking_id==str(end_mark)]['suc_marks'].values[0]
    if pd.isna(suc_marks):
        suc_marks = []
    else:
        suc_marks = suc_marks.split(':')
    num = len(pre_marks) + len(suc_marks)
    if num not in dic_neighbor_num:
        dic_neighbor_num[num] = [line_id]
    else:
        dic_neighbor_num[num].append(line_id)
dic_neighbor_num = dict(sorted(dic_neighbor_num.items(), key=lambda item: item[0]))

dic_smooth = {}
dic_done={}
for num in dic_neighbor_num:
    for line_id in dic_neighbor_num[num]:
        dic_smooth[line_id] = {'start':None,'end':None}
        dic_done[f"{line_id}_start"] = []
        dic_done[f"{line_id}_end"] = []


# True: 该点与其他相连line的点重合  False：不可以重合
for num in dic_neighbor_num:
    for line_id in dic_neighbor_num[num]:
        print(line_id)
        dic_suc,dic_pre = neighbor_is_smooth(line_id)
        suc_label = func(dic_suc)
        pre_label = func(dic_pre)
        if suc_label == 'true-false' or suc_label == 'true':
            dic_smooth[line_id]['end'] = True
            dic_done[f"{line_id}_end"].append(True)
            for suc in dic_suc:
                suc_line = mark_in_which_line(suc)
                if dic_suc[suc]:
                    dic_smooth[suc_line]['start'] = True
                    dic_done[f"{suc_line}_start"].append(True)
                else:
                    dic_smooth[suc_line]['start'] = False
                    dic_done[f"{suc_line}_start"].append(False)
        if suc_label == 'false':
            dic_smooth[line_id]['end'] = False
            dic_done[f"{line_id}_end"].append(False)
            for suc in dic_suc:
                suc_line = mark_in_which_line(suc)
                dic_smooth[suc_line]['start'] = True
                dic_done[f"{suc_line}_start"].append(True)
        
        if pre_label == 'true-false' or pre_label == 'true':
            dic_smooth[line_id]['start'] = True
            dic_done[f"{line_id}_start"].append(True)
            for pre in dic_pre:
                pre_line = mark_in_which_line(pre)
                if dic_pre[pre]:
                    dic_smooth[pre_line]['end'] = True
                    dic_done[f"{pre_line}_end"].append(True)
                else:
                    dic_smooth[pre_line]['end'] = False
                    dic_done[f"{pre_line}_end"].append(False)
        if pre_label == 'false':
            dic_smooth[line_id]['start'] = False
            dic_done[f"{line_id}_start"].append(False)
            for pre in dic_pre:
                pre_line = mark_in_which_line(pre)
                dic_smooth[pre_line]['end'] = True
                dic_done[f"{pre_line}_end"].append(True)


for i in dic_done:
    line_id = i.split('_')[0]
    position = i.split('_')[1]
    if True in dic_done[i] and False in dic_done[i]:
        print(f"check {i}")
        print(dic_done[i])

with open('data.json', 'w') as json_file:
    json.dump(dic_done, json_file, indent=4)


with open('dic_smooth.json', 'w') as json_file:
    json.dump(dic_smooth, json_file)



