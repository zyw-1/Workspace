# PowerShell版本的离线处理脚本
# 顺序执行多个Python脚本
# cd f:\Ykzx_ws\OfflineMap\offlinemap
# powershell -ExecutionPolicy Bypass -File .\offline_process.ps1

$files = @(
    "offline_process/00-base/00-source_to_pg.py",
    "offline_process/01-relative_map/lane/00-check_neighbors.py",
    "offline_process/01-relative_map/lane/01-add_info.py",
    "offline_process/01-relative_map/lane/02-lane_scatters.py",
    "offline_process/01-relative_map/lane/03-lane_scatter_add_info.py",
    "offline_process/01-relative_map/lane/04-chg_flg.py",
    "offline_process/01-relative_map/lane_mark/00-mark_scatters.py",
    "offline_process/01-relative_map/lane_mark/01-mark_scatter_add_info.py",
    "offline_process/01-relative_map/proto_related_table/01-stop_lines.py",
    "offline_process/01-relative_map/proto_related_table/02-cross_walks.py",
    "offline_process/01-relative_map/proto_related_table/03-lane_arrows.py",
    "offline_process/01-relative_map/proto_related_table/04-traffic_lights.py",
    "offline_process/01-relative_map/proto_related_table/05-junctions.py",
    "offline_process/01-relative_map/proto_related_table/06-traffic_signs.py",
    "offline_process/01-relative_map/proto_related_table/07-lane_marks.py",
    "offline_process/01-relative_map/proto_related_table/08-lanes.py",
    "offline_process/02-perception_map/alane/00-lane_to_alane.py",
    "offline_process/02-perception_map/alane/01-generate_alane.py",
    "offline_process/02-perception_map/alane/02-alane_conn.py",
    "offline_process/02-perception_map/alane/03-alane_add_pre_and_suc.py",
    "offline_process/02-perception_map/alane/04-add_alane_side.py",
    "offline_process/02-perception_map/feature_point/00-marking_add_node_id.py",
    "offline_process/02-perception_map/feature_point/01-lane_feature_point.py",
    "offline_process/02-perception_map/feature_point/02-marking_feature_points.py",
    "offline_process/02-perception_map/proto_related_table/01-feature_points_process.py",
    "offline_process/02-perception_map/proto_related_table/02-lane_lines_process.py",
    "offline_process/02-perception_map/proto_related_table/03-lane_lines_distinct.py",
    "offline_process/02-perception_map/proto_related_table/04-mark_type_has_change.py",
    "offline_process/02-perception_map/proto_related_table/05-lane_arrow_process.py",
    "offline_process/02-perception_map/proto_related_table/06-cross_walk_process.py",
    "offline_process/02-perception_map/proto_related_table/07-stop_line_process.py",
    "offline_process/02-perception_map/proto_related_table/08-junction_light_process.py",
    "offline_process/02-perception_map/proto_related_table/09-add_dist_on_alane.py",
    "offline_process/02-perception_map/proto_related_table/10-all_features_to_on_table.py",
    "offline_process/03-topo_map/lane_virtual_change.py",
    "offline_process/03-topo_map/topo_map.py",   # 需要依赖topo_graph.proto转的topo_graph_pb2.py
    "offline_process/all_table_to_pb.py"  # 需要依赖perception_map.proto和relative_map.proto转的perception_map_pb2.py和relative_map_pb2.py
)

Write-Host "=== Starting Python script sequence ===" -ForegroundColor Green

foreach ($pyFile in $files) {
    if (Test-Path $pyFile) {
        Write-Host "Executing: $pyFile" -ForegroundColor Yellow
        
        # 使用ykzx_py3.12环境的Python执行脚本
        $pythonPath = "C:\Users\13995\AppData\Local\conda\conda\envs\ykzx_py3.12\python.exe"
        & $pythonPath $pyFile
        
        # 检查上一个命令的退出状态
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: $pyFile execution failed! Terminating process" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "Warning: File $pyFile does not exist, skipping" -ForegroundColor Magenta
    }
}

Write-Host "=== All scripts completed ===" -ForegroundColor Green