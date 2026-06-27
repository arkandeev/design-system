#!/usr/bin/env python3
import base64, subprocess, os, tempfile, re

DS = "/Users/kandeev/клод/стратсеессии/design-system"
MAT = "/Users/kandeev/клод/стратсеессии/материалы/фото-портреты/премиум-тёмные"
OUT = os.path.join(DS, "дизайн-система.html")

def css(path):
    return open(path, encoding="utf-8").read()

def img_uri(path, maxpx=1100, q=78):
    """resize with sips to a temp jpg, return data URI."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(q),
                    "-Z", str(maxpx), path, "--out", tmp],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    data = open(tmp, "rb").read()
    os.unlink(tmp)
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()

tokens = css(os.path.join(DS, "core/tokens.css"))
base = css(os.path.join(DS, "web/base.css"))
# убрать @import google fonts из base (подключим <link> в head, чтобы @import не ломался)
base = re.sub(r'@import url\([^)]*fonts\.googleapis[^)]*\);', '', base)

imgs = {
  "route":   img_uri(os.path.join(DS, "brand/illustrations/route.jpg")),
  "system":  img_uri(os.path.join(DS, "brand/illustrations/system.jpg")),
  "mastery": img_uri(os.path.join(DS, "brand/illustrations/mastery.jpg")),
  "growth":  img_uri(os.path.join(DS, "brand/illustrations/growth.jpg")),
  "hero":    img_uri(os.path.join(MAT, "77.jpg"), maxpx=1500),
  "bw":      img_uri(os.path.join(MAT, "73.jpg")),
}

TPL = open(os.path.join(os.path.dirname(__file__), "guide_template.html"), encoding="utf-8").read()
html = (TPL.replace("/*__TOKENS__*/", tokens)
           .replace("/*__BASE__*/", base))
for k, v in imgs.items():
    html = html.replace("__IMG_%s__" % k.upper(), v)

open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, round(os.path.getsize(OUT)/1024/1024, 2), "MB")
