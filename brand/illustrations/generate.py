#!/usr/bin/env python3
import json, os, re, sys, time, urllib.request, urllib.error

ENV = "/Users/kandeev/клод/стратсеессии/konstruktor/.env.local"
OUTDIR = "/Users/kandeev/клод/стратсеессии/design-system/brand/illustrations"
BASE = "https://api.kie.ai/api/v1/jobs"

def load_key():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("KIEAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("no key")

KEY = load_key()
HEAD = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

STYLE = ("ultra-realistic cinematic 3D render, single subject centered, deep charcoal "
         "near-black background hex 0D0D0D, dramatic single-source warm bronze champagne "
         "rim light from upper right, muted desaturated palette, matte premium materials, "
         "generous negative space, museum lighting, subtle volumetric haze, elegant minimal "
         "luxury editorial, ultra high detail, sharp focus, no text, no watermark")

JOBS = {
  "route":   "An antique solid brass nautical compass with fine engraving, lid open, resting "
             "on a dark weathered marble slab, faint topographic contour lines etched in the "
             "shadows behind it, symbolizing strategy and a chosen route. " + STYLE,
  "system":  "An elegant exposed clockwork mechanism of precisely interlocking polished brass "
             "gears, suspended in darkness, symbolizing a working system rather than "
             "inspiration. " + STYLE,
  "mastery": "A classical Greco-Roman white marble bust sculpture, three-quarter view, refined "
             "chiaroscuro, edge catching a warm bronze rim light, symbolizing timeless mastery "
             "and thinking. " + STYLE + ", no people, this is a stone statue",
  "growth":  "A single elegant bonsai sapling with sparse refined branches growing out of a "
             "cracked dark stone, lit by one warm light, symbolizing disciplined growth. " + STYLE,
}

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers=HEAD, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEAD, method="GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def create(prompt):
    body = {"model": "nano-banana-2",
            "input": {"prompt": prompt, "image_input": [], "aspect_ratio": "1:1",
                      "resolution": "2K", "output_format": "jpg"}}
    res = post("/createTask", body)
    return res

def find_urls(obj):
    """recursively pull any image urls from a nested dict/list/str."""
    found = []
    def walk(x):
        if isinstance(x, str):
            for m in re.findall(r'https?://[^\s"\\]+\.(?:jpg|jpeg|png|webp)', x):
                found.append(m)
            # resultJson sometimes is a JSON string
            if x.strip().startswith("{"):
                try: walk(json.loads(x))
                except Exception: pass
        elif isinstance(x, dict):
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(obj)
    return found

os.makedirs(OUTDIR, exist_ok=True)
tasks = {}
for name, prompt in JOBS.items():
    try:
        res = create(prompt)
        print(name, "create ->", json.dumps(res, ensure_ascii=False)[:200])
        tid = (res.get("data") or {}).get("taskId") or (res.get("data") or {}).get("task_id")
        if tid: tasks[name] = tid
        else: print(name, "NO taskId")
    except urllib.error.HTTPError as e:
        print(name, "HTTP", e.code, e.read().decode()[:300])
    except Exception as e:
        print(name, "ERR", repr(e))

print("\n--- polling ---")
done = {}
deadline = time.time() + 360
while tasks and time.time() < deadline:
    time.sleep(8)
    for name, tid in list(tasks.items()):
        try:
            res = get(f"/recordInfo?taskId={tid}")
        except Exception as e:
            print(name, "poll err", repr(e)); continue
        data = res.get("data") or {}
        state = str(data.get("state") or data.get("status") or "").lower()
        urls = find_urls(res)
        if urls:
            done[name] = urls[0]; tasks.pop(name)
            print(name, "DONE", urls[0][:90])
        elif state in ("fail", "failed", "error"):
            print(name, "FAILED", json.dumps(res, ensure_ascii=False)[:200]); tasks.pop(name)
        else:
            print(name, "...", state or "pending")

print("\n--- downloading ---")
for name, url in done.items():
    try:
        path = os.path.join(OUTDIR, f"{name}.jpg")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
        print("saved", path, os.path.getsize(path), "b")
    except Exception as e:
        print(name, "dl err", repr(e))
print("\nremaining (timed out):", list(tasks))
