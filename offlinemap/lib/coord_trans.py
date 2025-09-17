
from functools import partial
import pyproj
import shapely.ops as ops
import warnings
warnings.filterwarnings('ignore')

class CoordTransformer(object):
    # def __init__(self,zone,width):
    #     if width==6:
    #         utm_proj = pyproj.Proj(f"+proj=utm +zone={zone} +ellps=WGS84")  # 创建utm投影
    #     if width==3:
    #         utm_proj = pyproj.Proj(f"+proj=tmerc +lat_0=0 +lon_0={zone * 3 - 180} +k=0.9996 +x_0=500000 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
    #     self.proj = utm_proj

    def __init__(self,long):
        utm_proj = pyproj.Proj(f"+proj=tmerc +lat_0=0 +lon_0={long} +k=0.9996 +x_0=500000 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
        self.proj = utm_proj


    def utm(self,geometry):
        proj_LATLONG_UTM = partial(
            pyproj.transform,
            pyproj.Proj(proj='latlong'),
            self.proj)  # 创建从经纬度坐标到UTM投影的投影转换
        utm_geom = ops.transform(proj_LATLONG_UTM, geometry)

        return utm_geom

    def lonlat(self,geometry):
        proj_UTM_LATLONG = partial(
            pyproj.transform,
            self.proj,
            pyproj.Proj(proj='latlong')
        ) 
        lonlat = ops.transform(proj_UTM_LATLONG, geometry)
        return lonlat



