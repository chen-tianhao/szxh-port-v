#!/usr/bin/env python3
"""抓取 Esri World Imagery 瓦片并拼接成码头底图，输出经纬度变换参数。

用法:
    python3 tools/fetch_imagery.py --lat 31.667 --lon 121.183 --z 17 --km 2.6

依赖: Pillow
输出: assets/imagery/imagery_z{z}.png + assets/imagery/imagery_z{z}.json (变换参数)

注意: Esri World Imagery 属第三方影像，仅用于内部分析与示意底图，
      对外发布需替换为已授权影像（天地图/甲方提供）；README 已注明归属。
"""
import argparse, json, math, os, sys, time, urllib.request

TILE_URL = ("https://services.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}")

def deg2num(lat, lon, z):
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n
    return x, y

def num2deg(x, y, z):
    n = 2.0 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon

def fetch_tile(z, x, y, cache):
    path = os.path.join(cache, f"{z}_{x}_{y}.jpg")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    url = TILE_URL.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": "szxh-port-v/0.2 (+research)"})
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(req, timeout=30).read()
            with open(path, "wb") as f:
                f.write(data)
            return path
        except Exception as e:
            if attempt == 2:
                print(f"  ! tile {z}/{x}/{y} failed: {e}", file=sys.stderr)
                return None
            time.sleep(1.5 * (attempt + 1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, default=31.667)
    ap.add_argument("--lon", type=float, default=121.183)
    ap.add_argument("--z", type=int, default=17)
    ap.add_argument("--km", type=float, default=2.6, help="目标宽度（公里）")
    ap.add_argument("--out", default="assets/imagery")
    ap.add_argument("--cache", default="assets/imagery/tiles")
    args = ap.parse_args()

    from PIL import Image
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(args.cache, exist_ok=True)

    m_per_px = 156543.03392 * math.cos(math.radians(args.lat)) / (2 ** args.z)
    target_px = int(args.km * 1000 / m_per_px)
    n_tiles = max(1, math.ceil(target_px / 256))
    cx, cy = deg2num(args.lat, args.lon, args.z)
    x0 = int(cx) - n_tiles // 2
    y0 = int(cy) - n_tiles // 2

    canvas = Image.new("RGB", (n_tiles * 256, n_tiles * 256))
    ok = 0
    for i in range(n_tiles):
        for j in range(n_tiles):
            p = fetch_tile(args.z, x0 + i, y0 + j, args.cache)
            if p:
                canvas.paste(Image.open(p).convert("RGB"), (i * 256, j * 256))
                ok += 1

    png = os.path.join(args.out, f"imagery_z{args.z}.png")
    canvas.save(png, optimize=True)

    # 左上角与右下角的地理坐标 + 每像素米数
    lat_nw, lon_nw = num2deg(x0, y0, args.z)
    lat_se, lon_se = num2deg(x0 + n_tiles, y0 + n_tiles, args.z)
    meta = {
        "z": args.z, "tiles": n_tiles, "tiles_ok": ok,
        "width": canvas.width, "height": canvas.height,
        "lat_nw": lat_nw, "lon_nw": lon_nw,
        "lat_se": lat_se, "lon_se": lon_se,
        "m_per_px": m_per_px,
        "source": "Esri World Imagery (internal use / replace before publishing)",
        "attribution": "© Esri, Maxar, Earthstar Geographics",
    }
    with open(os.path.join(args.out, f"imagery_z{args.z}.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
