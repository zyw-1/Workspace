# 离线地图数据处理系统 (python-cl2)

## 工程概述
该工程是一个离线地图数据处理系统，主要用于处理高精度地图数据，生成可供自动驾驶系统使用的地图格式。系统通过一系列Python脚本实现数据提取、转换、平滑处理和protobuf格式生成等功能。

## 目录结构
```
python-cl2/
├── data/                 # 地图数据文件
│   ├── pb.txt/           # protobuf格式数据
│   └── topo_graph.pb.txt # 拓扑图数据
├── data copy/            # 数据备份
├── fake_vehicle_run.csv  # 模拟车辆运行数据
├── lib/                  # 工具库
│   ├── config.py         # 配置文件
│   ├── coord_trans.py    # 坐标转换
│   └── pg.py             # PostgreSQL数据库操作
├── offline_process/      # 离线处理脚本
│   ├── 00-base/          # 基础数据处理
│   ├── 01-relative_map/  # 相对地图处理
│   ├── 02-perception_map/ # 感知地图处理
│   └── 03-topo_map/      # 拓扑地图处理
├── offline_process.sh    # 处理流程执行脚本
└── test.py               # 测试脚本
```

## 主要功能
1. 从PostgreSQL数据库读取原始地图数据
2. 坐标转换（经纬度与UTM坐标转换）
3. 车道线、交通标志、交叉路口等地图元素处理
4. 地图数据平滑处理
5. 生成protobuf格式的地图数据
6. 构建道路拓扑结构

## 依赖项
- Python 3.x
- PostgreSQL数据库
- 相关Python库：pyproj, psycopg2, pandas, shapely, networkx等

## 使用方法
1. 配置数据库连接信息（lib/config.py）
2. 执行处理脚本：
   ```bash
   ./offline_process.sh
   ```

## 注意事项
- 确保PostgreSQL数据库服务正常运行
- 处理前请备份原始数据
- 根据实际需求调整config.py中的参数