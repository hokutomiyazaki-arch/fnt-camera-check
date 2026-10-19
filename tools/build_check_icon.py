"""FNT アドバンスの3アプリ＋アプリ集のアイコンを SVG で描き、PNG に書き出す。
共通：黒地（#070707〜#1a1916 のにじみ）・金（#d8bd84）の細い枠・下に Cormorant Garamond の英字1語。
モチーフだけを変える。"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/private/tmp/camera_check_design/icons/out")
OUT.mkdir(parents=True, exist_ok=True)

GOLD = "#d8bd84"
GOLD2 = "#a8874f"
RED = "#e5483a"

# ---- モチーフ（512 の座標・中心は (256, 210) 付近。下 400〜470 に英字） ----
NECK = f'''
<g fill="none" stroke="{GOLD}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round">
  <!-- 右向きの横顔と首 -->
  <path d="M206 338 L206 292 C170 270 158 222 166 182 C178 124 226 98 268 100 C318 104 344 140 344 182 L344 196 L362 228 L344 236 L344 254 C344 270 334 278 318 278 L300 278 L300 338"/>
</g>
<!-- 首のまわりの回旋の矢印（後ろ側は細い破線） -->
<path d="M163 322 A 96 24 0 0 1 349 322" fill="none" stroke="{GOLD2}" stroke-width="6" stroke-dasharray="4 12" stroke-linecap="round"/>
<path d="M349 322 A 96 24 0 0 1 182 338" fill="none" stroke="{GOLD}" stroke-width="11" stroke-linecap="round"/>
<path d="M196 322 L172 337 L198 354" fill="none" stroke="{GOLD}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
<!-- 鼻先の狙う点 -->
<circle cx="412" cy="214" r="17" fill="none" stroke="{GOLD}" stroke-width="6"/>
<circle cx="412" cy="214" r="6" fill="{GOLD}"/>
'''

VORC = f'''
<!-- 目 -->
<path d="M150 214 Q256 120 362 214 Q256 308 150 214 Z" fill="none" stroke="{GOLD}" stroke-width="14" stroke-linejoin="round"/>
<circle cx="256" cy="214" r="42" fill="none" stroke="{GOLD}" stroke-width="12"/>
<circle cx="256" cy="214" r="17" fill="{GOLD}"/>
<!-- 頭が動く向き（上下左右） -->
<g fill="none" stroke="{GOLD2}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round">
  <path d="M104 190 L80 214 L104 238"/>
  <path d="M408 190 L432 214 L408 238"/>
  <path d="M232 104 L256 80 L280 104"/>
  <path d="M232 324 L256 348 L280 324"/>
</g>
'''

SVV = f'''
<!-- 丸い窓 -->
<circle cx="256" cy="214" r="138" fill="none" stroke="{GOLD2}" stroke-width="6" opacity=".9"/>
<!-- 本当の垂直（金の破線） -->
<line x1="256" y1="96" x2="256" y2="332" stroke="{GOLD}" stroke-width="7" stroke-dasharray="14 12" stroke-linecap="round"/>
<!-- 傾いた赤い線 -->
<g transform="rotate(16 256 214)">
  <line x1="256" y1="100" x2="256" y2="328" stroke="{RED}" stroke-width="16" stroke-linecap="round"/>
</g>
<circle cx="256" cy="214" r="9" fill="{GOLD}"/>
'''

APPS = f'''
<g fill="none" stroke="{GOLD}" stroke-width="11">
  <rect x="150" y="104" width="94" height="94" rx="22"/>
  <rect x="268" y="104" width="94" height="94" rx="22"/>
  <rect x="150" y="222" width="94" height="94" rx="22"/>
</g>
<rect x="268" y="222" width="94" height="94" rx="22" fill="{GOLD}"/>
<path d="M296 269 L315 288 L338 252" fill="none" stroke="#141008" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
'''


CHECK = f'''<g transform="translate(256 214) scale(1.16) translate(-256 -214)">
<!-- カメラのファインダーの四隅 -->
<g fill="none" stroke="{GOLD2}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round">
  <path d="M120 128 L120 92 L162 92"/>
  <path d="M350 92 L392 92 L392 128"/>
  <path d="M120 300 L120 336 L162 336"/>
  <path d="M392 300 L392 336 L350 336"/>
</g>
<!-- 目（中の瞳はレンズの絞り） -->
<path d="M160 214 Q256 136 352 214 Q256 292 160 214 Z" fill="none" stroke="{GOLD}" stroke-width="13" stroke-linejoin="round"/>
<circle cx="256" cy="214" r="40" fill="none" stroke="{GOLD}" stroke-width="11"/>
<circle cx="256" cy="214" r="15" fill="{GOLD}"/>
<!-- チェックの印（右下の金の丸） -->
<circle cx="372" cy="318" r="40" fill="{GOLD}" stroke="#0e0e0f" stroke-width="8"/>
<path d="M352 318 L366 332 L392 302" fill="none" stroke="#141008" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
</g>'''

ICONS = {
    "check": (CHECK, "CHECK"),
}


def svg(motif, word, *, mode):
    """mode: any（角丸・外は透明）/ full（全面。iOS 用）/ mask（全面・中身を80%の安全域へ）/ fav（32px 用：字なし）"""
    bg = '''<defs><radialGradient id="g" cx="50%" cy="0%" r="110%">
      <stop offset="0" stop-color="#1f1d18"/><stop offset=".55" stop-color="#0e0e0f"/><stop offset="1" stop-color="#050505"/>
    </radialGradient></defs>'''
    if mode == "any":
        base = '<rect x="0" y="0" width="512" height="512" rx="112" fill="url(#g)"/>'
        frame = f'<rect x="26" y="26" width="460" height="460" rx="90" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="4"/>'
    else:
        base = '<rect x="0" y="0" width="512" height="512" fill="url(#g)"/>'
        frame = '' if mode == "mask" else f'<rect x="26" y="26" width="460" height="460" rx="90" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="4"/>'
    if mode == "fav":
        base = '<rect x="0" y="0" width="512" height="512" rx="96" fill="url(#g)"/>'
        inner = f'<g transform="translate(256 256) scale(1.15) translate(-256 -214)">{motif}</g>'
        frame = ''
    else:
        size = 64 if len(word) <= 4 else 54
        ls = ".14em" if len(word) <= 4 else ".08em"
        label = (f'<text x="256" y="452" text-anchor="middle" font-family="Cormorant Garamond" font-weight="600" '
                 f'font-size="{size}" letter-spacing="{ls}" fill="{GOLD}">{word}</text>')
        inner = motif + label
        if mode == "mask":
            inner = f'<g transform="translate(256 256) scale(.74) translate(-256 -270)">{inner}</g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">{bg}{base}{frame}{inner}</svg>'


HTML = '''<!doctype html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&display=block" rel="stylesheet">
<style>html,body{margin:0;background:transparent}#c{width:%dpx;height:%dpx}#c svg{width:100%%;height:100%%;display:block}</style>
</head><body><div id="c">%s</div></body></html>'''


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for key, (motif, word) in ICONS.items():
            for mode, sizes in [("any", [512, 192]), ("full", [180, 512]), ("mask", [512]), ("fav", [32])]:
                s = svg(motif, word, mode=mode)
                (OUT / f"{key}-{mode}.svg").write_text(s)
                for px in sizes:
                    pg.set_viewport_size({"width": px, "height": px})
                    pg.set_content(HTML % (px, px, s))
                    pg.evaluate("document.fonts.ready")
                    pg.wait_for_timeout(300)
                    ok = pg.evaluate("document.fonts.check('600 20px \"Cormorant Garamond\"')")
                    if not ok and mode != "fav":
                        raise SystemExit(f"font not loaded for {key}")
                    pg.locator("#c").screenshot(path=str(OUT / f"{key}-{mode}-{px}.png"), omit_background=True)
        b.close()


if __name__ == "__main__":
    main()
