# -*- coding: UTF-8 -*-
import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path)
from lib.config import pg_from,pg_map,boundary,ctf,srid
from shapely.geometry import Polygon,LineString
from shapely import wkt,wkb
import pandas as pd
import binascii

"""
将原始高精度地图数据库中需要的数据拷贝到CL2单独的数据库中，还涉及到一些项目需要的定制处理
"""

# 替换12号路口左转的虚拟车道
# s = 'LINESTRING (109.7864313606726 39.59358099945101, 109.786525000 39.593622222, 109.7865446775849 39.59363551516147, 109.7865554595425 39.5936521864036, 109.786559716255 39.59367136388279, 109.7865588513653 39.59369185468789, 109.7865542685159 39.59371246590899, 109.7865473713496 39.59373200463758, 109.7865395635089 39.59374927796645, 109.7865322486366 39.59376309298946, 109.7865268303752 39.59377225680093, 109.7865241373746 39.59377688652204, 109.7864017632715 39.59397642540091)'
# replace_geom = wkt.loads(s)
# replace_coords = list(ctf.utm(replace_geom).coords)
# half_width = 3.451/2

# left = []
# right = []

# for i in range(1,len(replace_coords)):
#     p1 = replace_coords[i]
#     p2 = replace_coords[i - 1]
#     # 计算线段方向向量
#     v = (p2[0] - p1[0], p2[1] - p1[1])
#     # 计算垂直向量
#     v_perp = (-v[1], v[0])
#     # 计算垂直向量的长度
#     length = (v_perp[0] ** 2 + v_perp[1] ** 2) ** 0.5
#     if length != 0:
#         # 归一化垂直向量
#         v_perp_normalized = (v_perp[0] / length, v_perp[1] / length)
#     else:
#         # 如果垂直向量长度为 0，使用默认值
#         v_perp_normalized = (0, 1)
#     # 计算左右两侧的点
#     left_point = (p1[0] + half_width * v_perp_normalized[0], p1[1] + half_width * v_perp_normalized[1])
#     right_point = (p1[0] - half_width * v_perp_normalized[0], p1[1] - half_width * v_perp_normalized[1])
#     left.append(left_point)
#     right.append(right_point)

# # 处理最后一个点
# p1 = replace_coords[0]
# p2 = replace_coords[1]
# # 计算线段方向向量
# v = (p2[0] - p1[0], p2[1] - p1[1])
# # 计算垂直向量
# v_perp = (-v[1], v[0])
# # 计算垂直向量的长度
# length = (v_perp[0] ** 2 + v_perp[1] ** 2) ** 0.5
# if length != 0:
#     # 归一化垂直向量
#     v_perp_normalized = (v_perp[0] / length, v_perp[1] / length)
# else:
#     # 如果垂直向量长度为 0，使用默认值
#     v_perp_normalized = (0, 1)
# # 计算左右两侧的点
# left_point = (p1[0] - half_width * v_perp_normalized[0], p1[1] - half_width * v_perp_normalized[1])
# right_point = (p1[0] + half_width * v_perp_normalized[0], p1[1] + half_width * v_perp_normalized[1])
# left.insert(0,left_point)
# right.insert(0,right_point)



def process(table):
    if table == 'rns_road_mark':
        sql = f"select a.* from {table} a, (select st_geomfromtext('{boundary.wkt}',4326) as geom) b where (st_intersects(a.geom,b.geom)=true);"
    # elif table == 'rns_lane':
    #     sql = f"select a.* from {table} a, (select st_geomfromtext('{boundary.wkt}',4326) as geom) b where (st_intersects(a.geom,b.geom)=true) and a.lane_id != '23618';"
    elif table == 'rns_signal_phase':
        sql = f"SELECT phase.* FROM rns_signal_phase phase INNER JOIN rns_link link ON phase.link_id = link.link_id CROSS JOIN (SELECT ST_GeomFromText('{boundary.wkt}',4326) AS geom) b WHERE ST_Intersects(link.geom, b.geom);"
    else:
        sql = f"select a.* from {table} a, (select st_geomfromtext('{boundary.wkt}',4326) as geom) b where st_intersects(a.geom,b.geom)=true;"
    data = pg_from.execute(sql,True)
    sql = f"select column_name from information_schema.columns where table_schema=\'public\' and table_name= \'{table}\'"
    columns = pg_from.execute(sql,True)
    columns = [x[0] for x in columns]
    df=pd.DataFrame(data,columns=columns)
    sql = f"drop table if exists {table};"
    pg_map.execute(sql)

    # todo ：宝坻项目插入掉头车道
    if table == 'rns_road_mark':
        # 7号路口，插入掉头车道的lane_mark
        uturn_geom_hex1 = "01020000001e000000bfdebfdee1515d408d1fe2aeb7d843400a3540d3e1515d40708a13f0b7d843401a6105c5e1515d40f9aa132fb8d843401dcb29b4e1515d4064976d6bb8d84340b7bbcca0e1515d408250b1a4b8d84340f821128be1515d408e9174dab8d84340ac502273e1515d406195530cb9d8434083b32959e1515d4099cff139b9d84340a77c583de1515d405b98fa62b9d84340494be21fe1515d4066c92187b9d84340d3cbfd00e1515d406a4b24a6b9d843407652e4e0e0515d408692c8bfb9d84340c570d1bfe0515d401209dfd3b9d843402987029ee0515d40ee6742e2b9d84340fa52b67be0515d40b1fbd7eab9d84340157a2c59e0515d4035d68fedb9d84340ba14a536e0515d4024ec64eab9d843409d366014e0515d40591e5de1b9d84340fc779df2df515d40f52e89d2b9d843409c7f9bd1df515d4046a204beb9d84340848e97b1df515d40b68bf5a3b9d84340510ecd92df515d4023478c84b9d84340f5227575df515d40221f0360b9d84340ad40c659df515d40cfe09d36b9d84340f4c6f33fdf515d40fe5da908b9d843402da12d28df515d40acde7ad6b8d84340b5ed9f12df515d40b8826fa0b8d8434005ac72ffde515d401995eb66b8d843407672c9eede515d40bad1592ab8d84340392cc3e0de515d406a9f2aebb7d84340"
        # 9999左车道线
        df.loc[len(df)] = {
            'id': '999999',
            'geom': uturn_geom_hex1,
            'marking_id': '9997',
            'link_id': '9999',
            'sequence': 1,
            'type': 0,
            'color': 999,
            'material': None,
            'width': None,
            'length': 16.704,
            'height': None,
            'mesh_id': 20599273,
            'map_id': None,
            'bdry_type': 999,
        }
        # 9999右车道线
        uturn_geom_hex2 = "01020000001e000000fb548972e2515d408190ff9cb7d84340e8c93769e2515d407fdf4807b8d84340e225d15ae2515d40c620476fb8d84340bbc97747e2515d403a1302d4b8d8434032e6592fe2515d40cd3f8934b9d84340b00db112e2515d409037f68fb9d84340dbaac1f1e1515d40c2b96ee5b9d843403f5ddacce1515d40dcbc2634bad84340a23d53a4e1515d40a255627bbad84340b00b8d78e1515d40bf7777babad843400947f049e1515d40b68bcff0bad84340c835ec18e1515d405ed6e81dbbd84340e6daf5e5e0515d4098ae5741bbd84340dede86b1e0515d40527ec75abbd84340456d1c7ce0515d406e8cfb69bbd84340fa093646e0515d40be8dcf6ebbd84340bd605410e0515d40a6fb3769bbd843400612f8dadf515d409e2f4259bbd84340f47fa0a6df515d405543143fbbd84340379eca73df515d40bdb5ec1abbd84340c7c7ef42df515d40dcd521edbad843402d9d8414df515d40bef420b6bad843401deef7e8de515d4081606d76bad84340ecb0b1c0de515d40e22a9f2ebad84340630a129cde515d4036be61dfb9d843403868707bde515d4033447289b9d843405bb01a5fde515d4063e29d2db9d8434001875447de515d4064d0bfccb8d8434027ad5634de515d40984cbf67b8d8434018794e26de515d401d748dffb7d84340"
        df.loc[len(df)] = {
            'id': '999998',
            'geom': uturn_geom_hex2,
            'marking_id': '9999',
            'link_id': '9999',
            'sequence': 1,
            'type': 0,
            'color': 999,
            'material': None,
            'width': None,
            'length': 28.523,
            'height': None,
            'mesh_id': 20599273,
            'map_id': None,
            'bdry_type': 999,
        }
        # 7号路口，插入掉头车道的lane_mark
        uturn_geom_hex3 = "01020000001e0000004ba8d421e1515d40a50ebee2c1d84340ecbc201fe1515d4073773191c1d84340c61d1221e1515d40f6b88e3fc1d84340065da227e1515d40f0f4e3eec0d84340c0c2bb32e1515d4094183ca0c0d84340cb943942e1515d4043699b54c0d843404b90e855e1515d405327fc0cc0d843404d93876de1515d40f7514bcabfd843404f74c888e1515d400a97658dbfd84340e20451a7e1515d40d3781457bfd84340163cbcc8e1515d403ab30b28bfd84340c9849bece1515d400ee9e600bfd84340932b7812e2515d4003a127e2bed8434090e7d439e2515d40199933ccbed84340eb782f62e2515d40f27553bfbed84340e457028be2515d4070d2b1bbbed84340a46ec6b3e2515d40bfb25ac1bed843403ed8f4dbe2515d408d5c3bd0bed843400d9f0803e3515d40059522e8bed84340a9748028e3515d40b543c108bfd84340c65de04be3515d404778ab31bfd84340784cb36ce3515d40afcf5962bfd8434084a38c8ae3515d4025342b9abfd84340c99d09a5e3515d4032f266d8bfd843401795d2bbe3515d40d71b3f1cc0d8434032249ccee3515d40fc31d364c0d843404f2028dde3515d404a0b33b1c0d84340ce6646e7e3515d40deee6100c1d843407c7cd5ece3515d4085d85951c1d843405ffcc2ede3515d40c7db0ea3c1d84340"
        # 9998左车道线
        df.loc[len(df)] = {
            'id': '999997',
            'geom': uturn_geom_hex3,
            'marking_id': '9994',
            'link_id': '9998',
            'sequence': 1,
            'type': 0,
            'color': 999,
            'material': None,
            'width': None,
            'length': 16.704,
            'height': None,
            'mesh_id': 20599273,
            'map_id': None,
            'bdry_type': 999,
        }
        # 9998右车道线
        uturn_geom_hex4 = "01020000001e0000002339ef84e0515d400ffeb0f4c1d84340599bfe85e0515d4089225782c1d8434099b72d8de0515d40fc34e010c1d84340485a679ae0515d4010119ba1c0d84340aa7b84ade0515d407718d035c0d8434015b34cc6e0515d40d069bdcebfd8434068dd76e4e0515d40d135936dbfd84340e2f4a907e1515d40873d7013bfd84340de177e2fe1515d4016845ec1bed8434065bb7d5be1515d40a73d5078bed843401306278be1515d409c041d39bed843404e4fedbde1515d40495d7f04bed8434062be3af3e1515d407c8f12dbbdd84340ba04722ae2515d403edc50bdbdd84340262ef062e2515d40011592abbdd84340bb810e9ce2515d407a980aa6bdd84340e26d24d5e2515d400fb8caacbdd84340d079890de3515d40b287bebfbdd84340bc369744e3515d40a818aedebdd84340072bab79e3515d409f1e3e09bed84340c2b128ace3515d401dfdf03ebed84340f3c87adbe3515d40333a287fbed8434059c91507e4515d40325226c9bed843409102792ee4515d40f5e6101cbfd84340dd363051e4515d405644f376bfd8434038f2d46ee4515d405832c1d8bfd84340acb80f87e4515d40bd0c5a40c0d8434083089999e4515d40d8168cacc0d84340512d3aa6e4515d40dd01181cc1d8434064e1cdace4515d40379bb48dc1d84340"
        df.loc[len(df)] = {
            'id': '999996',
            'geom': uturn_geom_hex4,
            'marking_id': '9996',
            'link_id': '9998',
            'sequence': 1,
            'type': 0,
            'color': 999,
            'material': None,
            'width': None,
            'length': 28.523,
            'height': None,
            'mesh_id': 20599273,
            'map_id': None,
            'bdry_type': 999,
        }
        # # 10号路口，插入掉头车道的lane_mark
        # uturn_geom_hex5 = "01020000001e000000c561f97aff515d4052f7783d62da43406bb31a83ff515d40afb7942862da4340cb3eca8bff515d40988c9a1462da434018720195ff515d403992990162da4340e854b99eff515d404028a0ef61da43407d8deaa8ff515d4005e7bbde61da434052668db3ff515d403b95f9ce61da4340f2d399beff515d404a1e65c061da43400d7b07caff515d404c8909b361da4340c6b6cdd5ff515d40b2f0f0a661da4340459fe3e1ff515d40a17a249c61da43406b1040eeff515d400a52ac9261da4340c1b0d9faff515d4076a08f8a61da434089f8a60700525d40a388d48361da4340f4389e1400525d40d721807e61da434072a3b52100525d400f74967a61da43402151e32e00525d40ec741a7861da4340484a1d3c00525d407a050e7761da4340e18d594900525d40c1f0717761da43402b198e5600525d402feb457961da43403aefb06300525d40cd92887c61da43408920b87000525d404d70378161da43407bd2997d00525d40eaf84e8761da4340cf464c8a00525d401191ca8e61da4340ffe2c59600525d40df8fa49761da43408537fda200525d406a43d6a161da4340fc06e9ae00525d40d1f557ad61da43401c4d80ba00525d4011f320ba61da43409145bac500525d40998f27c861da434097728ed000525d409a2f61d761da4340"
        # # 9997左车道线
        # df.loc[len(df)] = {
        #     'id': '999995',
        #     'geom': uturn_geom_hex5,
        #     'marking_id': '9991',
        #     'link_id': '9997',
        #     'sequence': 1,
        #     'type': 0,
        #     'color': 999,
        #     'material': None,
        #     'width': None,
        #     'length': 16.704,
        #     'height': None,
        #     'mesh_id': 20599273,
        #     'map_id': None,
        #     'bdry_type': 999,
        # }
        # # 9997右车道线
        # uturn_geom_hex6 = "01020000001e000000d1a003dcfe515d405c64bc5d62da434084d162d4fe515d40e4484d0d62da43404df37dd1fe515d40da7ea3bb61da4340c8195fd3fe515d408f5ddb6961da4340a8b9ffd9fe515d40f6a5111961da43407dbf48e5fe515d402ea35fca60da434012e012f5fe515d401457d77e60da43403a212709ff515d4030c07f3760da43403d993f21ff515d40044651f55fda43404962083dff515d40205832b95fda43408abe205cff515d40c74bf4835fda43400b691c7eff515d40148350565fda4340a90e85a2ff515d407ce7e5305fda434013eadbc8ff515d407fc036145fda4340327d9bf0ff515d4008eea6005fda4340f761391900525d40b48c7af65eda43403c2c284200525d40a008d5f55eda43402e56d96a00525d401ca2b8fe5eda43408f30bf9200525d40ce6506115fda434007d04eb900525d4078987e2c5fda4340d8f001de00525d40e294c1505fda43405eca580001525d40dd18517d5fda4340f7cbdb1f01525d40e4fc91b15fda4340583d1d3c01525d405150ceec5fda434094bcba5401525d40e3d2372e60da4340a5945e6901525d40dac2ea7460da4340e0e7c07901525d4001f6f0bf60da434028aaa88501525d40cb32450e61da43409467ec8c01525d40dcbdd65e61da4340c3d4728f01525d40ae0f8db061da4340"
        # df.loc[len(df)] = {
        #     'id': '999994',
        #     'geom': uturn_geom_hex6,
        #     'marking_id': '9993',
        #     'link_id': '9997',
        #     'sequence': 1,
        #     'type': 0,
        #     'color': 999,
        #     'material': None,
        #     'width': None,
        #     'length': 28.523,
        #     'height': None,
        #     'mesh_id': 20599273,
        #     'map_id': None,
        #     'bdry_type': 999,
        # }
        # # 宝平公路北环路，插入掉头车道的lane_mark
        # uturn_geom_hex7 = "01020000001e0000004071237f57525d40b3ddf5ff7cde43400256077357525d40c876e1137dde434073a4486657525d40bfc525267dde434006c9f55857525d40551eae367dde4340dbd71d4b57525d40b8ca67457dde4340b17bd03c57525d40b22042527dde434028e41d2e57525d4089942e5d7dde434072b3161f57525d406fc920667dde43407eebcb0f57525d40889f0e6d7dde4340b9da4e0057525d40583ff0717dde43407908b1f056525d40a522c0747dde4340272104e156525d40bb1a7b757dde43403ce259d156525d40005420747dde43402f06c4c156525d40e956b1707dde4340653054b256525d403906326b7dde43403dd91ba356525d40a09aa8637dde4340443a2c9456525d40ad9b1d5a7dde4340be3a968556525d4029d69b4e7dde43407f5c6a7756525d40db4f30417dde434041a9b86956525d40d038ea317dde43407aa0905c56525d4025dada207dde4340d525015056525d407d82150e7dde43405570184456525d402170aff97cde434042fae33856525d40fcb8bfe37cde4340e771702e56525d4076305fcc7cde434035abc92456525d405b4ba8b37cde43406592fa1b56525d40f001b7997cde43409b1f0d1456525d4044b0a87e7cde4340984b0a0d56525d40fbf49b627cde43409b05fa0656525d40a58eb0457cde4340"
        # # 8887左车道线
        # df.loc[len(df)] = {
        #     'id': '999993',
        #     'geom': uturn_geom_hex7,
        #     'marking_id': '8887',
        #     'link_id': '9996',
        #     'sequence': 1,
        #     'type': 0,
        #     'color': 999,
        #     'material': None,
        #     'width': None,
        #     'length': 16.704,
        #     'height': None,
        #     'mesh_id': 20599617,
        #     'map_id': None,
        #     'bdry_type': 999,
        # }
        # # 宝平公路北环路，8889右车道线
        # uturn_geom_hex8 = "01020000001e0000000e36ce0f58525d40300d932b7dde4340ae511c0358525d40326a58707dde4340797e01f357525d40afcd32b27dde4340c6f2a7df57525d40239c75f07dde4340516642c957525d405da47d2a7ede43404e8d0bb057525d4038cbb25f7ede4340887e459457525d40509a898f7ede43402c06397657525d408aad84b97ede4340f4e6345657525d40befb35dd7ede4340b90b8d3457525d4023f73ffa7ede434081ab991157525d40838256107fde43404262b6ed56525d40c0b83f1f7fde4340c64041c956525d408f84d4267fde43401ed699a456525d40ea0601277fde43402835208056525d4028cbc41f7fde4340bff8335c56525d402cc832117fde43402349333956525d40b12e71fb7ede43402de5791756525d403205b9de7ede4340d73160f755525d406d9255bb7ede43408b523ad955525d401998a3917ede4340974c57bd55525d40c65f10627ede4340143800a455525d40679c182d7ede43404980778d55525d40782347f37dde43409935f87955525d401b8133b57dde4340b072b56955525d40df6a80737dde434091d6d95c55525d404315da2e7dde4340df14875355525d405b70f4e77cde4340879dd54d55525d402f50899f7cde4340b45cd44b55525d40a28556567cde4340ae93884d55525d40f1ec1b0d7cde4340"
        # df.loc[len(df)] = {
        #     'id': '999992',
        #     'geom': uturn_geom_hex8,
        #     'marking_id': '8889',
        #     'link_id': '9996',
        #     'sequence': 1,
        #     'type': 0,
        #     'color': 999,
        #     'material': None,
        #     'width': None,
        #     'length': 28.523,
        #     'height': None,
        #     'mesh_id': 20599617,
        #     'map_id': None,
        #     'bdry_type': 999,
        # }
        # # 津围线，插入掉头车道的lane_mark
        # uturn_geom_hex9 = "01020000001e000000b0ad5614c7515d407bea67e7add5434070a0d806c7515d403f5d61e0add54340988f30fac6515d401c46afd4add543407c02c5eec6515d40c763b0c4add54340647cf2e4c6515d40584ae6b0add543401f8f08ddc6515d409249f199add543406e5647d7c6515d403f5a8b80add54340ae70ddd3c6515d40a63b8265add543403185e6d2c6515d40cef0b049add543403b646ad4c6515d4052d2f82dadd54340b5c75cd8c6515d40de6c3a13add5434099b69ddec6515d4028664efaacd54340f887fae6c6515d40e5a1fee3acd54340597d2ff1c6515d4050deffd0acd5434087e7e9fcc6515d40fdfbebc1acd543405bc4ca09c7515d404f1f3db7acd5434068c06917c7515d4003d349b1acd5434019845825c7515d401f4b42b0acd5434093312633c7515d4077de2eb4acd54340fff66240c7515d401dc3efbcacd543406698a34cc7515d40e90f3ecaacd543405fd48457c7515d40e1faaddbacd543401f88ae60c7515d407342b2f0acd543407179d667c7515d40b8a5a008add5434003b0c26cc7515d40ab47b722add54340064b4b6fc7515d409fd1223eadd5434037c45b6fc7515d404423055aadd543402396f36cc7515d40125a7c75add5434060402668c7515d4024f7a98fadd543409ba91a61c7515d40a4e9b9a7add54340"
        # # 8884左车道线
        # df.loc[len(df)] = {
        #     'id': '999991',
        #     'geom': uturn_geom_hex9,
        #     'marking_id': '8886',
        #     'link_id': '9995',
        #     'sequence': 1,
        #     'type': 0,
        #     'color': 999,
        #     'material': None,
        #     'width': None,
        #     'length': 16.704,
        #     'height': None,
        #     'mesh_id': 20599267,
        #     'map_id': None,
        #     'bdry_type': 999,
        # }
        # # 津围线，8885右车道线
        # uturn_geom_hex10 = "01020000001e0000005eb29375c6515d40faecaf80aed5434010e2b761c6515d400900b652aed5434091a80c51c6515d40f31deb1faed5434050e3db43c6515d40a65a30e9add54340d905603ac6515d404f3c78afadd54340d416c334c6515d40a588c273add54340c3f51d33c6515d407dd71737add54340cfec7735c6515d404efe84faacd543407790c63bc6515d40e96816bfacd54340c0eded45c6515d40fc73d385acd543400d06c153c6515d4010deb94facd5434080960265c6515d401763b91dacd5434076276679c6515d401796aff0abd543405d5f9190c6515d404c0b64c9abd5434015931daac6515d40c5e384a8abd54340e38c99c5c6515d40bec9a38eabd543401d828be2c6515d402a6b337cabd54340e02e7300c7515d40817d8571abd543406c0ecc1ec7515d40ad53c96eabd5434064a60f3dc7515d40520c0b74abd54340b6dab75ac7515d401e5c3381abd54340e73f4177c7515d4002f50796abd543406b612d92c7515d408a882cb2abd5434004f204abc7515d40ed6024d5abd543406fdc59c1c7515d40b08954feabd54340302bc9d4c7515d40457e062dacd5434018bffce4c7515d40e0526b60acd54340e9ccacf1c7515d4060499f97acd54340791ba1fac7515d4085c2add1acd54340d5fcb1ffc7515d40ef79950dadd54340"
        # df.loc[len(df)] = {
        #     'id': '999990',
        #     'geom': uturn_geom_hex10,
        #     'marking_id': '8884',
        #     'link_id': '9995',
        #     'sequence': 1,
        #     'type': 0,
        #     'color': 999,
        #     'material': None,
        #     'width': None,
        #     'length': 28.523,
        #     'height': None,
        #     'mesh_id': 20599267,
        #     'map_id': None,
        #     'bdry_type': 999,
        # }
    if table == 'rns_lane':
        # 7号路口，掉头车道9999
        uturn_geom_hex1 = "01020000001e000000f199a428e2515d40c4d8f0a5b7d8434054f45e1ee2515d406cc42ffcb7d84340f34c2910e2515d4026cf2a50b8d84340e8b622fee1515d4025512aa1b8d84340bd9d72e8e1515d4062287deeb8d84340366f48cfe1515d40f33b7a37b9d843409833dbb2e1515d40daed817bb9d843404f156993e1515d401578ffb9b9d84340fcd83671e1515d40f8316af2b9d8434013478f4ce1515d4005bb4624bad843404e88c225e1515d40c108284fbad84340617625fde0515d402355b072bad843406ee210d3e0515d40abeb918ebad84340c6d2e0a7e0515d4051d38fa2bad84340acb9f37be0515d40d8537eaebad84340caa6a94fe0515d406d5543b2bad843401c756323e0515d40b599d6adbad8434025f781f7df515d40d7cd41a1bad843402d2365ccdf515d405275a08cbad8434066416ba2df515d40cdad1f70bad84340c11df079df515d4074ccfd4bbad843402c3f4c53df515d40a5d58920bad84340f625d42edf515d4021d022eeb9d843400a93d70cdf515d4040f536b5b9d8434081d9a0edde515d40e2bf4276b9d84340183c74d1de515d4036dccf31b9d84340ee578fb8de515d40acfa73e8b8d84340be9d28a3de515d409488cf9ab8d84340d9da6e91de515d404d518c49b8d84340c7d28883de515d40f20a5cf5b7d84340"
        df.loc[len(df)] = {
            'id': '999999',
            'geom': uturn_geom_hex1,
            'lane_id': '9999',
            'mesh_id': 20599273,
            'map_id': None,
            'link_id': '9999',
            'snode_id': '1953',
            'enode_id': '1885',
            'length': 22.929,
            'direction': 2,
            'lane_seq': 1,
            'width': 3.8,
            'lmkg_id': '9997',
            'rmkg_id': '9999',
            'chg_flg': 0,
            'vt_type': 1,
            'pre_lanes': '1647',
            'suc_lanes': '1589',
            'spd_max': 10,
            'spd_min': 0,
            'arrow_type': None,
            'lane_type': 1,
            'memo': None,
            'spd_max_type': 0,
            'spd_min_type': 0,
            'trans_type': 0,
            'inters_id': 14,
            'conn_type': 4,
            'maneuvers': None,
        }
        # 7号路口，掉头车道9998
        uturn_geom_hex2 = "01020000001e000000ccf061d3e0515d402a87b7ebc1d8434003628adce0515d40df079098c1d84340c1fe88e9e0515d405e6f7a47c1d84340cecb40fae0515d4084942bf9c0d8434017808c0ee1515d400a1d52aec0d84340d6d73e26e1515d4004f89467c0d8434083f92241e1515d4092e99125c0d84340b4ebfc5ee1515d40022bdce8bfd84340e01a8a7fe1515d407c22fbb1bfd84340d9ed81a2e1515d4003356981bfd84340b96796c7e1515d4080b59257bfd84340cad574eee1515d4027f3d434bfd84340fe87c616e2515d4062697d19bfd8434040923140e2515d40fb12c905bfd843400595596ae2515d4025e2e3f9bed843404b8be094e2515d40725ee8f5bed843404e9c67bfe2515d40a969dff9bed843400bef8fe9e2515d40fc2bc005bfd84340d17dfb12e3515d40b9277019bfd84340ece74d3be3515d406674c334bfd84340ab3f2d62e3515d40ab207d57bfd84340f9d24287e3515d403dba4f81bfd84340adec3baae3515d4098faddb1bfd84340068dcacae3515d400697bbe8bfd84340a017a6e8e3515d4027326e25c0d8434063f58b03e4515d40d26c6e67c0d843400729401be4515d40071429aec0d84340ded48d2fe4515d40356900f9c0d84340bfb04740e4515d400b824d47c1d84340ff6e484de4515d40babc6198c1d84340"
        df.loc[len(df)] = {
            'id': '999998',
            'geom': uturn_geom_hex2,
            'lane_id': '9998',
            'mesh_id': 20599275,
            'map_id': None,
            'link_id': '9998',
            'snode_id': '1749',
            'enode_id': '1758',
            'length': 22.929,
            'direction': 2,
            'lane_seq': 1,
            'width': 3.8,
            'lmkg_id': '9994',
            'rmkg_id': '9996',
            'chg_flg': 0,
            'vt_type': 1,
            'pre_lanes': '1482',
            'suc_lanes': '1489',
            'spd_max': 10,
            'spd_min': 0,
            'arrow_type': None,
            'lane_type': 1,
            'memo': None,
            'spd_max_type': 0,
            'spd_min_type': 0,
            'trans_type': 0,
            'inters_id': 14,
            'conn_type': 4,
            'maneuvers': None,
        }
        # # 10号路口，掉头车道9997
        # uturn_geom_hex3 = "01020000001e00000070817e2bff515d40aeae9a4d62da4340ec0a2529ff515d4019f9321562da4340f633de29ff515d4038fa9ddc61da434048cda72dff515d405b9986a461da434041667634ff515d406642966d61da4340706f353eff515d4017e6723861da4340af78c74aff515d40cb04bd0561da43400c8a065aff515d40bcc90dd660da43407a96c46bff515d40533cf5a960da4340eb06cc7fff515d402a8df88160da4340265ce095ff515d40b783905e60da43408ae5beadff515d408511284060da43407b8a1fc7ff515d402a0f1b2760da434021a4b5e1ff515d40de26b51360da4340f3e430fdff515d40f2ef300660da4340434b3e1900525d40d43db7fe5fda4340f31b893500525d40c0a45efd5fda434067e2bb5100525d408f352b0260da43409e72816d00525d406b710e0d60da434074ea858800525d409c75e71d60da434006af77a200525d40da5e833460da4340256308bb00525d4002e39d5060da43400ed4edd100525d40571fe27160da434086d9e2e600525d40ee98eb9760da4340bb26a8f900525d40256c47c260da43407809050a01525d40aca775f060da43406315c81701525d40f6ceea2161da434045b9c72201525d408a7f115661da43409abce22a01525d4038344c8c61da4340e3a3003001525d40df20f7c361da4340"
        # df.loc[len(df)] = {
        #     'id': '999997',
        #     'geom': uturn_geom_hex3,
        #     'lane_id': '9997',
        #     'mesh_id': 20599275,
        #     'map_id': None,
        #     'link_id': '9997',
        #     'snode_id': '1252',
        #     'enode_id': '1263',
        #     'length': 22.929,
        #     'direction': 2,
        #     'lane_seq': 1,
        #     'width': 3.8,
        #     'lmkg_id': '9991',
        #     'rmkg_id': '9993',
        #     'chg_flg': 0,
        #     'vt_type': 1,
        #     'pre_lanes': '1051',
        #     'suc_lanes': '1065',
        #     'spd_max': 10,
        #     'spd_min': 0,
        #     'arrow_type': None,
        #     'lane_type': 2,
        #     'memo': None,
        #     'spd_max_type': 0,
        #     'spd_min_type': 0,
        #     'trans_type': 0,
        #     'inters_id': None,
        #     'conn_type': None,
        #     'maneuvers': None,
        # }
        # # 宝平公路北环路，掉头车道9996
        # uturn_geom_hex4 = "01020000001e00000079d378c757525d402676c4157dde434009bd34bc57525d40749562477dde4340ed7696ae57525d402d9a95767dde4340c1dabe9e57525d4094a9eba27dde43407f1fd48c57525d40f8d0f9cb7dde43404c7d017957525d40af075df17dde434037c5766357525d40f81dbb127ede4340e6ed674c57525d408e96c32f7ede434039960c3457525d40c76830487ede43401e7f9f1a57525d408ba9c65b7ede4340dbfd5d0057525d406e19576a7ede4340196887e556525d40af96be737ede43401e7b5cca56525d40f171e6777ede4340a2bf1eaf56525d40f6a4c4767ede4340baeb0f9456525d40cdea5b707ede43405744717956525d403bb9bb647ede4340d5ff825f56525d40741b00547ede434012ab834656525d406e6e513e7ede43409192af2e56525d408affe3237ede43400431401856525d40688ef7047ede4340a3a46b0356525d4021b3d6e17dde4340a42c64f055525d40552ad6ba7dde434004b057df55525d40c80854907dde4340d04e6fd055525d406cd8b6627dde4340ecfecec355525d400ea16c327dde43405a3595b955525d40e5dee9ff7cde4340bf9cdab155525d409c69a8cb7cde4340e2d9b1ac55525d40654e26967cde4340b95e27aa55525d40ea9fe45f7cde4340594c41aa55525d40f33e66297cde4340"
        # df.loc[len(df)] = {
        #     'id': '999996',
        #     'geom': uturn_geom_hex4,
        #     'lane_id': '9996',
        #     'mesh_id': 20599617,
        #     'map_id': None,
        #     'link_id': '9996',
        #     'snode_id': '373',
        #     'enode_id': '304',
        #     'length': 22.929,
        #     'direction': 2,
        #     'lane_seq': 1,
        #     'width': 3.8,
        #     'lmkg_id': '8887',
        #     'rmkg_id': '8889',
        #     'chg_flg': 0,
        #     'vt_type': 1,
        #     'pre_lanes': '292',
        #     'suc_lanes': '302',
        #     'spd_max': 10,
        #     'spd_min': 0,
        #     'arrow_type': None,
        #     'lane_type': 2,
        #     'memo': None,
        #     'spd_max_type': 0,
        #     'spd_min_type': 0,
        #     'trans_type': 0,
        #     'inters_id': None,
        #     'conn_type': None,
        #     'maneuvers': None,
        # }
        # # 津围线，掉头车道9995
        # uturn_geom_hex5 = "01020000001e000000b730f5c4c6515d4091ec0b34aed543401ed635b5c6515d400d208d18aed543402b1d92a7c6515d40036ddef8add54340f08c509cc6515d406aa6a3d5add543407759ab93c6515d40b8f692afadd54340d236cf8dc6515d40f1317187add54340ed71da8ac6515d40e0db0d5eadd54340e653dc8ac6515d4019f73e34add5434002d3d48dc6515d4056b2dc0aadd54340dc92b493c6515d40a40abde2acd54340d6335d9cc6515d40e278afbcacd5434028f0a1a7c6515d40f7c07899acd543405e8348b5c6515d405cf8ce79acd54340a8570ac5c6515d409dd8555eacd54340d1f295d6c6515d40bd709b47acd54340929b90e9c6515d40aa461536acd54340a92e98fdc6515d4089f71d2aacd54340551a4512c7515d402b63f323acd54340d9752c27c7515d401c6cb523acd543404d2ae23bc7515d40c7526529acd543408821fb4fc7515d40f6aee534acd54340dc6f0f63c7515d40ea07fb45acd543406a6dbc74c7515d40d8074d5cacd5434049b4a684c7515d40b1446877acd5434021f97b92c7515d40e894c096acd54340aeb4f49dc7515d4038e4b3b9acd54340a195d5a6c7515d40b5798ddfacd5434052b3f0acc7515d40479e8907add543402d7b26b0c7515d40af90d930add54340e85366b0c7515d409fb2a75aadd54340"
        # df.loc[len(df)] = {
        #     'id': '999995',
        #     'geom': uturn_geom_hex5,
        #     'lane_id': '9995',
        #     'mesh_id': 20599267,
        #     'map_id': None,
        #     'link_id': '9995',
        #     'snode_id': '2440',
        #     'enode_id': '2596',
        #     'length': 22.929,
        #     'direction': 2,
        #     'lane_seq': 1,
        #     'width': 3.8,
        #     'lmkg_id': '8884',
        #     'rmkg_id': '8886',
        #     'chg_flg': 0,
        #     'vt_type': 1,
        #     'pre_lanes': '2043',
        #     'suc_lanes': '2178',
        #     'spd_max': 10,
        #     'spd_min': 0,
        #     'arrow_type': None,
        #     'lane_type': 2,
        #     'memo': None,
        #     'spd_max_type': 0,
        #     'spd_min_type': 0,
        #     'trans_type': 0,
        #     'inters_id': None,
        #     'conn_type': None,
        #     'maneuvers': None,
        # }
    if table == 'rns_link':
        # 7号路口，插入掉头车道的link
        uturn_geom_hex1 = "01020000001e000000a743844ce3515d40885d9e82b7d843408c354742e3515d40d95ec9eeb7d84340ea54ed32e3515d4069078258b8d84340b1799a1ee3515d406d7dd1beb8d8434023187e05e3515d40f1ddc820b9d84340ffd1d2e7e2515d40a46a837db9d843409fedddc5e2515d40ec9f28d4b9d8434038b4ee9fe2515d40742eee23bad84340b6b85d76e2515d408cd3196cbad84340ee088c49e2515d40110c03acbad84340044be219e2515d40e09d14e3bad843400cc9cfe7e1515d404af4cd10bbd84340356dc9b3e1515d404a4cc434bbd84340c9b0487ee1515d40ceada34ebbd843408f80ca47e1515d40c6af2f5ebbd843401719ce10e1515d4034054463bbd84340a7ddd3d9e0515d40ebd1d45dbbd84340702c5ca3e0515d4041c6ee4dbbd84340d732e66de0515d407201b733bbd8434083c4ee39e0515d40eeba6a0fbbd84340e537ef07e0515d406ab35ee1bad84340e54a5cd8df515d40016ffea9bad843405312a5abdf515d40233acb69bad8434086f63182df515d40b2fb5a21bad8434093bf635cdf515d40fed656d1b9d8434053b3923adf515d40d9a0797ab9d8434049c70d1ddf515d405c2b8e1db9d8434043e81904df515d40526c6dbbb8d843406959f1efde515d40a882fc54b8d84340392cc3e0de515d406a9f2aebb7d84340"
        df.loc[len(df)] = {
            'id': '99999',
            'geom': uturn_geom_hex1,
            'link_id': '9999',
            'mesh_id': 20599273,
            'map_id': None,
            'admin_code': None,
            'snode_id': '577',
            'enode_id': '561',
            'length': 36.287,
            'direction': 2,
            'lboundary': '9997',
            'rboundary': '9999',
            'material': None,
            'road_fc': 3,
            'road_type': 7,
            'pre_links': '471',
            'suc_links': '458',
            'inters_id': None,
            'conn_type': 4,
            'form_type': 1,
            'spd_max': None,
            'spd_min': None,
            'main_links': None,
            'opposites': None,
            'road_name': None,
            'vt_type': 0,
            'maneuvers': None,
            'relief_flg': None,
            's': None
        }
        # 7号路口，south->north插入掉头车道的link
        uturn_geom_hex2 = "01020000001e0000002eca7494df515d40bcc03310c2d843409b97d3a2df515d408ed67dadc1d84340034980b5df515d40d1c4b44dc1d84340fc7a55ccdf515d401f5198f1c0d84340dd7625e7df515d40dce5e099c0d84340478eba05e0515d4002213e47c0d843409b86d727e0515d407f7455fabfd843409613384de0515d4000dbc0b3bfd8434008609175e0515d40a3a30d74bfd84340aaa392a0e0515d401057bb3bbfd84340dbc4e5cde0515d4025b83a0bbfd84340fc0430fde0515d402de2ece2bed8434026b6122ee1515d407d8622c3bed84340b2f82b60e1515d40e14a1bacbed84340317f1793e1515d402f4a059ebed8434038576fc6e1515d40fab7fc98bed8434083b5ccf9e1515d401ba80b9dbed84340bbc3c82ce2515d4084fa29aabed843405f6efd5ee2515d40826b3dc0bed8434021310690e2515d4059c819dfbed8434022e080bfe2515d40b9478106bfd84340826c0eede2515d4077052536bfd84340aea25318e3515d4080a0a56dbfd84340fbe0f940e3515d40ccf993acbfd8434014c5af66e3515d40d71272f2bfd84340eece2989e3515d40e509b43ec0d84340f0f722a8e3515d401032c190c0d84340233d5dc3e3515d40f144f5e7c0d843405c1ba2dae3515d4089aba143c1d843405efcc2ede3515d40c7db0ea3c1d84340"
        df.loc[len(df)] = {
            'id': '99998',
            'geom': uturn_geom_hex2,
            'link_id': '9998',
            'mesh_id': 20599275,
            'map_id': None,
            'admin_code': None,
            'snode_id': '521',
            'enode_id': '522',
            'length': 36.287,
            'direction': 2,
            'lboundary': '9994',
            'rboundary': '9996',
            'material': None,
            'road_fc': 3,
            'road_type': 7,
            'pre_links': '428',
            'suc_links': '429',
            'inters_id': None,
            'conn_type': 4,
            'form_type': 1,
            'spd_max': None,
            'spd_min': None,
            'main_links': None,
            'opposites': None,
            'road_name': None,
            'vt_type': 0,
            'maneuvers': None,
            'relief_flg': None,
            's': None
        }
        # # 10号路口，north->south插入掉头车道的link
        # uturn_geom_hex3 = "01020000001e000000cbb6acf0fd515d40e06f808d62da43409b0b2af5fd515d40cd48aa1f62da434059ca02fffd515d4085713cb361da43402eb61e0efe515d402cd0414961da43402f9e5822fe515d400443bfe260da4340e8b87e3bfe515d404c1eb18060da4340e61e5359fe515d4024bf082460da43401d638c7bfe515d406c39aacd5fda43409d47d6a1fe515d4060266a7e5fda4340fa8cd2cbfe515d403e990b375fda43403dda19f9fe515d40243f3ef85eda434053bb3c29ff515d4096ae9cc25eda43405fb3c45bff515d4005ebaa965eda434063603590ff515d40d11fd5745eda43406dad0dc6ff515d400e966e5d5eda43405410c9fcff515d407de7b0505eda4340f4cfe03300525d40c670bb4e5eda4340d14fcd6a00525d40440493575eda4340e25d07a100525d4028de216b5eda43405f7f09d600525d400ada37895eda43404b39510901525d406de98ab15eda4340a651603a01525d4005cab7e35eda43402206be6801525d400dfa421f5fda43405d35f89301525d404de899635fda4340da77a4bb01525d40dc5c14b05fda4340e02561df01525d403317f60360da4340e447d6fe01525d40949d705e60da43400d6fb61902525d404139a5be60da4340ce73bf2f02525d40b81aa72361da4340bc18bb4002525d4098a07d8c61da4340"
        # df.loc[len(df)] = {
        #     'id': '99997',
        #     'geom': uturn_geom_hex3,
        #     'link_id': '9997',
        #     'mesh_id': 20599275,
        #     'map_id': None,
        #     'admin_code': None,
        #     'snode_id': '377',
        #     'enode_id': '380',
        #     'length': 36.287,
        #     'direction': 2,
        #     'lboundary': '9991',
        #     'rboundary': '9993',
        #     'material': None,
        #     'road_fc': 3,
        #     'road_type': 7,
        #     'pre_links': '306',
        #     'suc_links': '309',
        #     'inters_id': None,
        #     'conn_type': 4,
        #     'form_type': 1,
        #     'spd_max': None,
        #     'spd_min': None,
        #     'main_links': None,
        #     'opposites': None,
        #     'road_name': None,
        #     'vt_type': 0,
        #     'maneuvers': None,
        #     'relief_flg': None,
        #     's': None
        # }
        # # 宝平公路北环路插入掉头车道的link
        # uturn_geom_hex4 = "01020000001e000000cf92c5e158525d40e3eedf6a7dde43403dc7d0cd58525d408b07bfd27dde4340e470d2b458525d403f9529367ede4340d043099758525d40032e26947ede4340f3f9bf7458525d40f606c9eb7ede4340a1974c4e58525d40dc43363c7fde4340cb930f2458525d40ba1ea4847fde4340fce572f657525d4005e25cc47fde43407dfce8c557525d4082b0c0fa7fde4340419deb9257525d405a16472780de434065b4fa5d57525d40675f804980de434042139b2757525d407baf166180de4340372355f056525d40c0d9ce6d80de43406c8fb3b856525d4031f5886f80de4340f3e8418156525d40a6ac406680de43409f488b4a56525d40b6490d5280de434011f2181556525d40477a213380de434057fb70e155525d406cd1ca0980de434088fc14b055525d40c40471d67fde4340a5ca808155525d4050e894997fde4340ef40295655525d40372bcf537fde4340ba1b7b2e55525d40c0d8ce057fde4340a1e7d90a55525d4029a157b07ede4340ca079feb54525d40b8ee3f547ede4340a2d518d154525d40cbcb6ef27dde43404fdc89bb54525d403b9fd98b7dde4340bd3128ab54525d40b1c481217dde4340efee1ca054525d40fe0672b47cde4340e3c8839a54525d40c802bc457cde43400fcb6a9a54525d401b7875d67bde4340"
        # df.loc[len(df)] = {
        #     'id': '99996',
        #     'geom': uturn_geom_hex4,
        #     'link_id': '9996',
        #     'mesh_id': 20599617,
        #     'map_id': None,
        #     'admin_code': None,
        #     'snode_id': '122',
        #     'enode_id': '107',
        #     'length': 36.287,
        #     'direction': 2,
        #     'lboundary': '8887',
        #     'rboundary': '8889',
        #     'material': None,
        #     'road_fc': 3,
        #     'road_type': 7,
        #     'pre_links': '95',
        #     'suc_links': '97',
        #     'inters_id': None,
        #     'conn_type': 4,
        #     'form_type': 1,
        #     'spd_max': None,
        #     'spd_min': None,
        #     'main_links': None,
        #     'opposites': None,
        #     'road_name': None,
        #     'vt_type': 0,
        #     'maneuvers': None,
        #     'relief_flg': None,
        #     's': None
        # }
        # # 津围线插入掉头车道的link
        # uturn_geom_hex5 = "01020000001e0000005ea24b25c6515d408d8c32ceaed54340d846f223c6515d40c5ea6a97aed5434041d7e624c6515d40c3ce9a60aed543407e992728c6515d40094f252aaed5434024acae2dc6515d404dde6cf4add543401a117235c6515d407e99d2bfadd54340acbf633fc6515d403898b58cadd54340e7bd714bc6515d40de40725badd5434018418659c6515d408da1612cadd5434034d58769c6515d4022cfd8ffacd54340d78a597bc6515d406c4b28d6acd54340972bdb8ec6515d40a0739bafacd543403c74e9a3c6515d401ef8778cacd5434080545ebac6515d40755efd6cacd54340e03311d2c6515d408e8e6451acd54340fc3ad7eac6515d40ce6bdf39acd543400ca18304c7515d40e87a9826acd54340d4fce71ec7515d40fa94b217acd543408998d439c7515d4095a8480dacd5434014c81855c7515d400b896d07acd543400c418370c7515d4064cc2b06acd54340cf73e28bc7515d403fb88509acd5434020e504a7c7515d40b43d7511acd543409687b9c1c7515d404904ec1dacd543404814d0dbc7515d40e083d32eacd54340146219f5c7515d40742d0d44acd54340e3ba670dc8515d4053a2725dacd54340442e8f24c8515d4081f9d57aacd54340e5e0653ac8515d40b212029cacd543403258c44ec8515d4053f6bac0acd54340"
        # df.loc[len(df)] = {
        #     'id': '99995',
        #     'geom': uturn_geom_hex5,
        #     'link_id': '9995',
        #     'mesh_id': 20599267,
        #     'map_id': None,
        #     'admin_code': None,
        #     'snode_id': '777',
        #     'enode_id': '822',
        #     'length': 36.287,
        #     'direction': 2,
        #     'lboundary': '8884',
        #     'rboundary': '8886',
        #     'material': None,
        #     'road_fc': 3,
        #     'road_type': 7,
        #     'pre_links': '629',
        #     'suc_links': '667',
        #     'inters_id': None,
        #     'conn_type': 4,
        #     'form_type': 1,
        #     'spd_max': None,
        #     'spd_min': None,
        #     'main_links': None,
        #     'opposites': None,
        #     'road_name': None,
        #     'vt_type': 0,
        #     'maneuvers': None,
        #     'relief_flg': None,
        #     's': None
        # }
    if table == 'rns_object_arrow':
        df.loc[df[df.obj_id=='583'].index,'direction'] = 10
        df.loc[df[df.obj_id=='560'].index,'direction'] = 10
    if table == 'rns_lane':
        df.loc[df[df.lane_id=='583'].index,'direction'] = 10
        df.loc[df[df.lane_id=='560'].index,'direction'] = 10
    #########

    if table != 'rns_signal_phase':
        l = []
        for index,row in df.iterrows():
            geom = wkb.loads(row['geom'])
            utm = ctf.utm(geom)
            l.append(utm.wkt)
        df['utm'] = l

    # if table == 'rns_lane':
    #     df.loc[df[df.lane_id=='1153'].index,'geom'] = binascii.hexlify(replace_geom.wkb).decode('utf-8')
    #     df.loc[df[df.lane_id=='1153'].index,'utm'] = LineString(replace_coords).wkt
    #     df.loc[df[df.lane_id=='1153'].index,'vt_type'] = 0
    # if table == 'rns_road_mark':
    #     left_utm = LineString(left)
    #     left_geom = ctf.lonlat(left_utm)
    #     right_utm = LineString(right)
    #     right_geom = ctf.lonlat(right_utm)
    #     df.loc[df[df.marking_id=='1596'].index,'geom'] = binascii.hexlify(right_geom.wkb).decode('utf-8')
    #     df.loc[df[df.marking_id=='1596'].index,'utm'] = left_utm.wkt
    #     df.loc[df[df.marking_id=='1596'].index,'type'] = 3
    #     df.loc[df[df.marking_id=='1597'].index,'geom'] = binascii.hexlify(left_geom.wkb).decode('utf-8')
    #     df.loc[df[df.marking_id=='1597'].index,'utm'] = right_utm.wkt
    #     df.loc[df[df.marking_id=='1597'].index,'type'] = 3

    pg_map.df_to_pg(df,table)
    sql = (f"update {table} set utm = st_force2d(st_geomfromtext(utm,{srid})); "
           f"alter table {table} alter column utm type geometry;"
            f"alter table {table} add column geometry text;"
           f"update {table} set geometry = st_astext(geom);"
            f"update {table} set geom = st_force2d(st_geomfromtext(geometry,4326));"  # 先把geometry转换为二维，不考虑高程
            f"update {table} set geometry = st_astext(geom);"
            f"alter table {table} alter column geom type geometry;") 
    pg_map.execute(sql)



boundary = Polygon(boundary)
sql = (f"drop table if exists boundary;"
       f"create table boundary as select st_geomfromtext('{boundary.wkt}',4326) as geom;")
pg_map.execute(sql)


# no 'rns_lane_curb'
table_list = ['rns_lane','rns_link','rns_road_mark','rns_junction_polygon','rns_signal_phase','rns_object_arrow',
              'rns_object_cwalk','rns_object_sline','rns_junction_point','rns_object_sign','rns_lane_node']

for table in table_list:
    print(table)
    process(table)


# 补充路口的inters_code
# TODO: phase表中的inters_id对应的是junction_point表中的inters_cod
sql = ("alter table rns_junction_polygon drop column if exists inters_code;"
        "alter table rns_junction_polygon add column inters_code text;"
        "update rns_junction_polygon a set inters_code = b.inters_code from rns_junction_point b where a.inters_id = b.inters_id;")
pg_map.execute(sql)

remake_id = 999
df=pg_map.get('rns_junction_polygon')
l = []
for index,row in df.iterrows():
    inters_id = row['inters_id']
    inters_code = row['inters_code']
    if pd.isna(inters_code):
        inters_code = remake_id
        remake_id += 1
    dic = {'inters_id':inters_id,'inters_code':inters_code}
    l.append(dic)

df=pd.DataFrame(l)
sql = "drop table if exists df;"
pg_map.execute(sql)
pg_map.df_to_pg(df,'df')
sql = ("update rns_junction_polygon a set inters_code = df.inters_code from df where df.inters_id = a.inters_id and a.inters_code is null;"
    "drop table if exists df;")
pg_map.execute(sql)


# 将stop line合并
l = []
df=pg_map.get('rns_object_sline')
df_lane = pg_map.get('rns_lane')
obj_id = 1
for link_id,group in df.groupby('link_ids'):
    rows = df_lane[df_lane.link_id==link_id].sort_values('lane_seq')
    # max_idx = rows['lane_seq'].max()
    # first_lane = rows.iloc[0]
    # last_lane = rows.iloc[max_idx-1]
    # first_sl = df[df.lane_ids==first_lane['lane_id']].iloc[0]
    # last_sl = df[df.lane_ids==last_lane['lane_id']].iloc[0]
    sll = []
    for sl in rows.iloc:
        if (df[df.lane_ids==sl['lane_id']].empty):
            continue
        else:
            sll.append(df[df.lane_ids==sl['lane_id']].iloc[0])
    first_sl = sll[0]
    last_sl = sll[-1]

    first_line = wkb.loads(first_sl['geom'],hex=True)
    last_line = wkb.loads(last_sl['geom'],hex=True)
    merge_line = LineString([list(first_line.coords)[0],list(last_line.coords)[-1]])
    sub_type = group['sub_type'].values[0]
    inters_id = group['inters_id'].values[0]
    lane_ids = ':'.join(rows['lane_id'].tolist())
    utm = ctf.utm(merge_line)
    l.append({'obj_id':obj_id,'sub_type':sub_type,'inters_id':inters_id,'link_ids':link_id,'lane_ids':lane_ids,
            'geometry':merge_line.wkt,'utm':utm.wkt})
    obj_id += 1

import pandas as pd
df=pd.DataFrame(l)

sql = ("drop table if exists rns_object_sline_merge;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rns_object_sline_merge')
sql = ("alter table rns_object_sline_merge add column geom geometry;"
    "update rns_object_sline_merge set geom = st_geomfromtext(geometry,4326);"
    f"select UpdateGeometrySRID('rns_object_sline_merge', 'geom', 4326);")
pg_map.execute(sql)


# # 删除不需要的lane
# sql = "delete from rns_lane where lane_id in ('31750','405','396');"
# pg_map.execute(sql)

# drop_mark = []

# sql = "delete from rns_road_mark where marking_id in ('46063','550','551','549','548');"
# pg_map.execute(sql)


# sql = ("update rns_lane set lane_seq = 4 where lane_id = '397';"
#        "update rns_lane set lane_seq = 4 where lane_id = '406';"
#        "update rns_lane set lane_seq = 2 where lane_id = '31751';")
# pg_map.execute(sql)








