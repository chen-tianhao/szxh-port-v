#!/usr/bin/env python3
"""把 OSM 矢量叠加到影像底图上，用于核对岸线/栈桥/道路的配准是否正确。

用法:
    python3 tools/overlay_osm.py --osm scratch/osm_wide.osm --z 18
输出:
    assets/vectors/osm_aoi.json     截取到的矢量（shoreline / piers / conveyor / roads）
    scratch/overlay_check.png       叠加核对图
"""
import argparse, json, os, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

def load_meta(z):
    p = f"assets/imagery/imagery_z{z}.json"
    return json.load(open(p))

def to_px(lat, lon, meta):
    W, H = meta["width"], meta["height"]
    x = (lon - meta["lon_nw"]) / (meta["lon_se"] - meta["lon_nw"]) * (W - 1)
    y = (lat - meta["lat_nw"]) / (meta["lat_se"] - meta["lat_nw"]) * (H - 1)
    return x, y

def in_img(x, y, meta):
    return 0 <= x < meta["width"] and 0 <= y < meta["height"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osm", required=True)
    ap.add_argument("--z", type=int, default=18)
    ap.add_argument("--out-json", default="assets/vectors/osm_aoi.json")
    ap.add_argument("--out-png", default="../.hermes/cache/scratch/overlay_check.png")
    args = ap.parse_args()

    meta = load_meta(args.z)
    root = ET.parse(args.osm).getroot()
    nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.findall("node")}
    feats = {"shoreline": [], "piers": [], "conveyors": [], "roads": [], "industrial": [], "water": []}
    for w in root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
        coords = [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes]
        if len(coords) < 2:
            continue
        rec = {"id": w.get("id"), "tags": tags, "coords": [[round(la, 6), round(lo, 6)] for la, lo in coords]}
        if tags.get("natural") == "coastline":
            # 只保留落在图幅内的那一段
            seg = []
            for c in coords:
                px = to_px(c[0], c[1], meta)
                if in_img(px[0], px[1], meta):
                    seg.append(c)
            if len(seg) >= 2:
                rec["coords"] = [[round(la, 6), round(lo, 6)] for la, lo in seg]
                feats["shoreline"].append(rec)
        elif tags.get("man_made") == "pier":
            feats["piers"].append(rec)
        elif tags.get("man_made") == "goods_conveyor":
            feats["conveyors"].append(rec)
        elif tags.get("highway"):
            feats["roads"].append(rec)
        elif tags.get("landuse") == "industrial":
            feats["industrial"].append(rec)
        elif tags.get("natural") == "water" or tags.get("waterway"):
            feats["water"].append(rec)

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump({"meta": meta, "features": feats}, f, ensure_ascii=False, indent=1)

    # 叠加核对图（缩到 2048 便于目视）
    im = Image.open(f"assets/imagery/imagery_z{args.z}.png").convert("RGB")
    scale = im.width / 2048
    im = im.resize((2048, 2048), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    colors = {"shoreline": (255, 40, 40), "piers": (60, 255, 120), "conveyors": (255, 220, 40),
              "roads": (80, 180, 255), "industrial": (255, 120, 255), "water": (0, 255, 255)}
    for kind, items in feats.items():
        for rec in items:
            pts = [tuple(v / scale for v in to_px(la, lo, meta)) for la, lo in rec["coords"]]
            d.line(pts, fill=colors[kind], width=3 if kind in ("shoreline", "conveyors") else 2)
    im.save(args.out_png)
    print(json.dumps({k: len(v) for k, v in feats.items()}, ensure_ascii=False), "->", args.out_png)

if __name__ == "__main__":
    main()
