#!/usr/bin/env python3
"""把 site.json 的堆场/泊位/岸线画回影像上，用于核对数字化精度。

用法: python3 tools/check_site.py
输出: ../.hermes/cache/scratch/site_check.png
"""
import json
from PIL import Image, ImageDraw

SITE = "assets/vectors/site.json"
OUT = "/home/chenth/.hermes/cache/scratch/site_check.png"
S = 1024


def latlon_to_px(lat, lon, img):
    x = (lon - img["lon_nw"]) / (img["lon_se"] - img["lon_nw"]) * S
    y = (lat - img["lat_nw"]) / (img["lat_se"] - img["lat_nw"]) * S
    return x, y


def main():
    site = json.load(open(SITE))
    img = site["imagery"]
    im = Image.open(img["file"]).convert("RGB").resize((S, S), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")

    for y in site["yards"]:
        pts = [latlon_to_px(la, lo, img) for la, lo in y["coords"]]
        col = y["color"].lstrip("#")
        rgb = tuple(int(col[i:i+2], 16) for i in (0, 2, 4))
        d.polygon(pts, outline=rgb + (255,), fill=rgb + (70,))
        d.text((pts[0][0] + 4, pts[0][1] + 4), f'{y["id"]} {y["cargo"]}', fill=(255, 255, 0, 255))

    b = site["basin"]
    pts = [latlon_to_px(la, lo, img) for la, lo in b["coords"]]
    d.polygon(pts, outline=(0, 255, 255, 255), fill=(0, 255, 255, 40))

    # 泊位：起止点连线等分
    p0 = latlon_to_px(*site["berths"]["start"], img)
    p1 = latlon_to_px(*site["berths"]["end"], img)
    n = site["berths"]["count"]
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        d.line([(x - 6, y - 6), (x + 6, y + 6)], fill=(255, 0, 255, 255), width=2)
        if i < n:
            d.text((x + 4, y - 12), str(i + 1), fill=(255, 0, 255, 255))
    d.line([p0, p1], fill=(255, 0, 255, 200), width=2)

    im.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
