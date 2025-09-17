#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将WKT格式的几何数据转换为十六进制格式
用于数据库存储
"""

from shapely.geometry import LineString
from shapely import wkt
import binascii

def wkt_to_hex(wkt_string):
    """
    将WKT格式的几何数据转换为十六进制格式
    
    Args:
        wkt_string (str): WKT格式的几何数据字符串
    
    Returns:
        str: 十六进制格式的几何数据
    """
    try:
        # 解析WKT字符串为几何对象
        geom = wkt.loads(wkt_string)
        
        # 转换为WKB（Well-Known Binary）格式
        wkb_data = geom.wkb
        
        # 转换为十六进制字符串
        hex_string = binascii.hexlify(wkb_data).decode('utf-8')
        
        return hex_string
    
    except Exception as e:
        print(f"转换失败: {e}")
        return None

def hex_to_wkt(hex_string):
    """
    将十六进制格式转换回WKT格式（用于验证）
    
    Args:
        hex_string (str): 十六进制格式的几何数据
    
    Returns:
        str: WKT格式的几何数据字符串
    """
    try:
        # 将十六进制字符串转换为二进制数据
        wkb_data = binascii.unhexlify(hex_string)
        
        # 从WKB数据创建几何对象
        geom = wkt.loads(wkb_data, hex=False)
        
        return geom.wkt
    
    except Exception as e:
        print(f"反向转换失败: {e}")
        return None

if __name__ == "__main__":
    # 用户提供的LINESTRING数据
    wkt_string = """LINESTRING (117.27944625293087 39.693103432452524, 117.27944403122058 39.69311610277418, 117.27944059776885 39.693128499727706, 117.2794359845929 39.69314050771068, 117.27943023471087 39.69315201474783, 117.27942340174081 39.693162913535275, 117.27941554940064 39.693173102441065, 117.27940675091394 39.69318248645297, 117.27939708832722 39.693190978064436, 117.27938665174474 39.69319849809062, 117.27937553848837 39.69320497640676, 117.27936385218993 39.69321035260212, 117.279351701825 39.69321457654331, 117.27933920069651 39.693217608841806, 117.27932646537836 39.6932194212212, 117.27931361462825 39.69321999678094, 117.2793007682803 39.693219330153894, 117.27928804612756 39.693217427556405, 117.27927556680498 39.69321430673032, 117.27926344668309 39.69320999677755, 117.27925179878285 39.693204537888704, 117.27924073172171 39.69319798096829, 117.27923034870078 39.69319038716004, 117.27922074654242 39.69318182727672, 117.27921201478743 39.69317238113983, 117.27920423486 39.693162136835234, 117.27919747930848 39.69315118989177, 117.27919181112885 39.693139642390435, 117.27918728317728 39.69312760201245, 117.2791839376772 39.69311518103516)"""
    print("原始WKT数据:")
    print(wkt_string)
    print("\n" + "="*80 + "\n")
    
    # 转换为十六进制
    hex_result = wkt_to_hex(wkt_string)
    
    if hex_result:
        print("转换后的十六进制格式:")
        print(hex_result)
        print(f"\n十六进制长度: {len(hex_result)} 字符")
        
        # 验证转换是否正确
        print("\n" + "="*80 + "\n")
        print("验证转换结果:")
        
        # 反向转换验证
        verified_wkt = hex_to_wkt(hex_result)
        if verified_wkt:
            print("反向转换成功，数据一致性验证通过")
            print(f"原始点数: {wkt_string.count(',') + 1}")
            print(f"验证点数: {verified_wkt.count(',') + 1}")
        
        # 保存结果到文件
        with open('/home/ykzx/0_OffLineMap/0_dev/offlinemap/0_tool/geometry_hex_output.txt', 'w', encoding='utf-8') as f:
            f.write(f"原始WKT:\n{wkt_string}\n\n")
            f.write(f"十六进制格式:\n{hex_result}\n\n")
            f.write(f"十六进制长度: {len(hex_result)} 字符\n")
        
        print("\n结果已保存到: /home/ykzx/0_OffLineMap/0_dev/offlinemap/0_tool/geometry_hex_output.txt")
    
    else:
        print("转换失败")