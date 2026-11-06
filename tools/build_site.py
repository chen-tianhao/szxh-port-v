#!/usr/bin/env python3
"""生成 site.json：把 OSM 矢量 + 人工数字化堆场多边形 + 泊位配置合成一份站点数据。

坐标约定：
  - 数据统一用 WGS84 经纬度存
  - 前端用 ENU 局部平面坐标（东西=X 米，南北=Z 米，北为 -Z）
  - 所有 px 均为 imagery_z18 底图上的像素坐标（4096²，0.508 m/px）

数字化来源：
  - 岸线 / 突堤 / 皮带机栈桥 / 道路：OpenStreetMap（ODbL）
  - 堆场多边形、内港池：按影像人工数字化（本文件 YARDS_PX）
  - 泊位编号与长度：交通运输部/海事局/苏州港集团公开资料（见 docs/02）
"""
import json, os

IMAGERY_META = "assets/imagery/imagery_z18.json"
OSM = "assets/vectors/osm_aoi.json"
OUT = "assets/vectors/site.json"

# ---- 人工数字化的堆场多边形（imagery_z18 的 1024 网格坐标，1px = 4m）----
# 说明：1024 网格是 4096 底图 1/4，故 1024px 上 1px = 4 × 0.508 = 2.03 m
YARDS_PX = [
    {"id": "Y1", "name": "散货/件杂堆场（含仓库）", "cargo": "件杂货", "color": "#4a6b8a",
     "poly": [[8, 172], [190, 168], [300, 300], [300, 640], [8, 640]]},
    {"id": "Y2", "name": "煤炭堆场（湿式长条堆）", "cargo": "煤炭", "color": "#2b2b30",
     "poly": [[242, 396], [640, 396], [700, 588], [562, 700], [300, 700]]},
    {"id": "Y3", "name": "煤炭堆场（东南块）", "cargo": "煤炭", "color": "#33333a",
     "poly": [[648, 630], [795, 700], [760, 792], [620, 700]]},
]

# ---- 内港池（驳船作业区）----
BASIN_PX = [[60, 62], [330, 62], [330, 132], [60, 132]]

# ---- 泊位：沿岸线在 [start_px, end_px] 之间等分 ----
BERTH_FRONTAGE_M = 2045.0     # 海事局通告：鑫海码头 1#-9# 泊位码头前沿长 2045 米
BERTH_COUNT = 9
BERTH_START_PX = [150, 85]    # 西北端（上游）
BERTH_END_PX = [830, 680]     # 东南端（下游）
# 公开资料里的设备分布（用于给每段泊位挂设备，编号顺序待甲方确认）
BERTH_HINT = [
    ("1#", "散货", "门机"),
    ("2#", "散货", "门机"),
    ("3#", "散货", "门机"),
    ("4#", "件杂", "门机"),
    ("5#", "煤炭", "桥式抓斗卸船机"),
    ("6#", "煤炭", "桥式抓斗卸船机"),
    ("7#", "煤炭", "卸船机+装船机"),
    ("8#", "煤炭", "卸船机+装船机"),
    ("9#", "矿石", "门机"),
]
BARGE_BERTHS = 8
BARGE_FRONTAGE_M = 706.0      # 苏州港集团：驳船泊位 8 个，总长 706 米


def px1024_to_latlon(x, y, meta):
    """1024 网格坐标 -> 经纬度（1024 网格由 4096 底图 1/4 缩放而来）"""
    fx = x / 1024.0
    fy = y / 1024.0
    lat = meta["lat_nw"] + (meta["lat_se"] - meta["lat_nw"]) * fy
    lon = meta["lon_nw"] + (meta["lon_se"] - meta["lon_nw"]) * fx
    return [round(lat, 6), round(lon, 6)]


def main():
    meta = json.load(open(IMAGERY_META))
    osm = json.load(open(OSM))

    yards = []
    for y in YARDS_PX:
        yards.append({
            "id": y["id"], "name": y["name"], "cargo": y["cargo"], "color": y["color"],
            "coords": [px1024_to_latlon(x, yy, meta) for x, yy in y["poly"]],
        })

    site = {
        "site": {
            "name": "太仓鑫海码头（含万方一体化运营区）",
            "note": "岸线/突堤/栈桥/道路来自 OpenStreetMap（ODbL）；堆场多边形按影像数字化；"
                    "泊位编号顺序按上游→下游推定，待甲方确认。",
        },
        "ref": [31.6672, 121.1825],
        "imagery": {
            "file": "assets/imagery/imagery_z18.png",
            "lat_nw": meta["lat_nw"], "lon_nw": meta["lon_nw"],
            "lat_se": meta["lat_se"], "lon_se": meta["lon_se"],
            "m_per_px": meta["m_per_px"],
            "width": meta["width"], "height": meta["height"],
            "attribution": meta["attribution"],
        },
        "shoreline": osm["features"]["shoreline"],
        "piers": osm["features"]["piers"],
        "conveyors": osm["features"]["conveyors"],
        "roads": osm["features"]["roads"],
        "context_areas": osm["features"]["industrial"],
        "yards": yards,
        "basin": {"name": "内港池（驳船作业区）",
                  "coords": [px1024_to_latlon(x, y, meta) for x, y in BASIN_PX]},
        "berths": {
            "count": BERTH_COUNT,
            "frontage_m": BERTH_FRONTAGE_M,
            "start": px1024_to_latlon(*BERTH_START_PX, meta),
            "end": px1024_to_latlon(*BERTH_END_PX, meta),
            "hints": [{"id": i, "cargo": c, "equipment": e} for i, c, e in BERTH_HINT],
            "source": "太航通〔2024〕0043号：1#-9# 泊位前沿长 2045 米",
        },
        "barge_berths": {
            "count": BARGE_BERTHS, "frontage_m": BARGE_FRONTAGE_M,
            "source": "苏州港集团：驳船泊位 8 个，总长 706 米，内档可靠泊 1.5 万吨船",
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(site, f, ensure_ascii=False, indent=1)
    print(f"site.json 写出: 岸线{len(site['shoreline'])}段 突堤{len(site['piers'])} "
          f"栈桥{len(site['conveyors'])} 道路{len(site['roads'])} 堆场{len(yards)}")


if __name__ == "__main__":
    main()
