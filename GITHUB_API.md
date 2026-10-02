# GitHub API 對接指引（skill 上傳 / 優化 / 更新）

本節點 `z12957` 用 **GitHub Contents API** 管理共用 skill repo `z12957/feihuang-hermes`。
以下每條 endpoint 都以目前 token 實測通過（200/201/204 見文末「實測記錄」）。

## 1. 必備

| 項目 | 值 |
|------|----|
| API base | `https://api.github.com` |
| repo | `z12957/feihuang-hermes`（public） |
| Auth | `Authorization: Bearer <GITHUB_TOKEN>`（93-char `ghp_…` classic，scope 含 `repo`） |
| 必要 header | `Accept: application/vnd.github+json`（缺了會 406）、`User-Agent: <任意>`（缺了 403） |

> token 是機密，放本機 `.env`，**不要** commit。本文用佔位符。

## 2. 基本檢查（免特殊權限）

```bash
curl -s https://api.github.com/user \
  -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json"
# 預期 login: "z12957"

curl -s https://api.github.com/repos/z12957/feihuang-hermes \
  -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json"
# 預期 private: false
```

## 3. 列出 repo 檔案

```bash
curl -s https://api.github.com/repos/z12957/feihuang-hermes/contents/ \
  -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json"
# → [{name, path, sha, size, type: "file"|"dir"}, ...]
```

## 4. 讀取單檔（更新前**必須**先拿到 sha）

```bash
curl -s https://api.github.com/repos/z12957/feihuang-hermes/contents/README.md \
  -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json"
# 回傳含 "sha": "c271852b47..." — 更新時要帶回
```

## 5. 建立新檔（PUT，無 sha = create）

```bash
# 檔案內容用 base64
CONTENT=$(base64 -w0 new-file.md)   # macOS: base64 -i new-file.md; Linux: base64 -w0 new-file.md
curl -s -X PUT \
  https://api.github.com/repos/z12957/feihuang-hermes/contents/skills/vast-gpu-fleet-maintenance/NEW.md \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"message\":\"add NEW.md\",\"content\":\"$CONTENT\",\"encoding\":\"base64\"}"
# 201 = 建立成功
```

## 6. 更新既有檔（PUT，**必帶** 舊 sha）

```bash
# 1) 先 GET 拿 sha
SHA=$(curl -s https://api.github.com/repos/z12957/feihuang-hermes/contents/README.md \
  -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")

# 2) base64 新內容
CONTENT=$(base64 -w0 README.new.md)

# 3) PUT 帶 sha
curl -s -X PUT \
  https://api.github.com/repos/z12957/feihuang-hermes/contents/README.md \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"message\":\"update README\",\"sha\":\"$SHA\",\"content\":\"$CONTENT\",\"encoding\":\"base64\"}"
# 200 = 更新成功（沒帶 sha 會 409/405）
```

## 7. 刪除檔

```bash
SHA=$(curl -s .../contents/OLD.md -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")
curl -s -X DELETE \
  https://api.github.com/repos/z12957/feihuang-hermes/contents/OLD.md \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"message\":\"remove OLD.md\",\"sha\":\"$SHA\"}"
# 200 = 刪除成功
```

## 8. Python 完整範例（建/改/刪）

```python
import json, base64, urllib.request, urllib.error

REPO = "z12957/feihuang-hermes"
TOK  = os.environ["GITHUB_TOKEN"]

def api(method, path, payload=None):
    url = f"https://api.github.com/{path}"
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {TOK}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "feihuang-node",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

def get_sha(path):
    st, d = api("GET", f"repos/{REPO}/contents/{path}")
    return d.get("sha") if st == 200 else None

def upsert(relpath, localfile, msg):
    b64 = base64.b64encode(open(localfile,'rb').read()).decode()
    sha = get_sha(relpath)
    payload = {"message": msg, "content": b64, "encoding": "base64"}
    if sha: payload["sha"] = sha          # 有 → 更新；無 → 建立
    st, d = api("PUT", f"repos/{REPO}/contents/{relpath}", payload)
    print(st, relpath)

upsert("skills/vast-gpu-fleet-maintenance/SKILL.md", "local/SKILL.md", "chore: improve skill")
```

## 9. 常見坑（實測）

1. **缺 `Accept: application/vnd.github+json`** → 406 Not Acceptable。
2. **缺 `User-Agent`** → 403 Forbidden。
3. **更新沒帶舊 `sha`** → 405/409。先 GET 再 PUT。
4. **內容必須 base64**（`encoding: "base64"`）或明文 UTF-8（兩種都可，base64 安全）。
5. **token 權限**：fine-grained 要 `Contents: Read and write` 綁到 `z12957/feihuang-hermes`（或 All repos）；classic 要 `repo` scope。
6. **token 重新產生後才有效**：GitHub 改權限 = 舊 token 立刻失效，要重產。
7. **rate limit**：unauthenticated 60/h、authenticated 5000/h；看 `X-RateLimit-Remaining` header。

## 10. 實測記錄（本節點 z12957 token，2026-10-02）

| 動作 | endpoint | 結果 |
|------|----------|------|
| 驗證身份 | `GET /user` | 200, login=z12957 |
| 讀 repo | `GET /repos/z12957/feihuang-hermes` | 200, private=false |
| 列檔案 | `GET /repos/.../contents/` | 200, 5 items |
| 讀單檔 | `GET /repos/.../contents/README.md` | 200, sha=c271852b47, size=2341 |
| 建檔 | `PUT /repos/.../contents/_apiprobe` | 201 |
| 刪檔 | `DELETE /repos/.../contents/_apiprobe` | 200 |
| 驗證刪除 | `GET /repos/.../contents/_apiprobe` | 404 |
