#!/usr/bin/env python3
"""Публикатор HTML на GitHub Pages.

Заливает локальный файл в публичный репозиторий arkandeev/design-system через
GitHub Git Data API (надёжно для больших файлов, без git-push) и возвращает
живую ссылку. Pages на репозитории уже включён.

Токен берётся из macOS Keychain (security find-internet-password -s github.com).
Токен 'стратсессии-push' имеет Contents+Pages write на этом репо.

Использование:
    python3 publish.py <локальный_файл> [путь_в_репо]
Примеры:
    python3 publish.py дизайн-система.html            -> index.html (корень)
    python3 publish.py лендинг.html lendingi/sessiya.html

URL результата: https://arkandeev.github.io/design-system/<путь_в_репо>
(index.html в корне открывается как .../design-system/).
"""
import base64, json, subprocess, sys, urllib.request, urllib.error

OWNER, REPO = "arkandeev", "design-system"
API = "https://api.github.com"

def token():
    return subprocess.check_output(
        ["security", "find-internet-password", "-s", "github.com", "-w"]).decode().strip()

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: publish.py <file> [repo_path]")
    local = sys.argv[1]
    repo_path = sys.argv[2] if len(sys.argv) > 2 else "index.html"
    H = {"Authorization": "token " + token(), "Accept": "application/vnd.github+json",
         "Content-Type": "application/json", "User-Agent": "kandeev-deploy"}

    def req(method, path, body=None):
        url = path if path.startswith("http") else API + path
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(url, data=data, headers=H, method=method)
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")

    st, ref = req("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/main")
    parent = ref["object"]["sha"]
    _, commit = req("GET", f"/repos/{OWNER}/{REPO}/git/commits/{parent}")
    base_tree = commit["tree"]["sha"]

    content = base64.b64encode(open(local, "rb").read()).decode()
    _, blob = req("POST", f"/repos/{OWNER}/{REPO}/git/blobs",
                  {"content": content, "encoding": "base64"})
    _, tree = req("POST", f"/repos/{OWNER}/{REPO}/git/trees",
                  {"base_tree": base_tree,
                   "tree": [{"path": repo_path, "mode": "100644", "type": "blob", "sha": blob["sha"]}]})
    _, newc = req("POST", f"/repos/{OWNER}/{REPO}/git/commits",
                  {"message": f"publish {repo_path}", "tree": tree["sha"], "parents": [parent]})
    st, _ = req("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/main", {"sha": newc["sha"]})

    url = f"https://{OWNER}.github.io/{REPO}/"
    if repo_path != "index.html":
        url += repo_path[:-len("index.html")] if repo_path.endswith("/index.html") else repo_path
    print("OK" if st == 200 else f"ERR {st}")
    print(url)

if __name__ == "__main__":
    main()
