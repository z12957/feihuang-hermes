# A2A 對接指引（節點間 agent-to-agent）

本文件說明如何用 **A2A (JSON-RPC 1.0)** 呼叫另一台的 Hermes agent。所有項目都經過
「打回我們自己 taipei server」實測驗證（HTTP 200 + `TASK_STATE_COMPLETED` + 回覆「pong」）。

## 1. 必備資訊（對端節點給你）

| 項目 | 範例（本節點） | 說明 |
|------|----------------|------|
| Endpoint | `http://100.82.9.91:9900/` | 對端 A2A server URL，**結尾要帶 `/`** |
| Bearer token | `<64-char shared token>` | 對端 `A2A_BEARER_TOKEN`，雙方共用同一支 |
| Agent name | `taipei` | 對端 `A2A_AGENT_NAME`（健康檢查會回傳） |
| 協議 | JSONRPC 1.0 | `supportedInterfaces[0].protocolBinding` |

> token 是**機密**，只走私網/密文 전달，**不要** commit 進本 repo。本文用佔位符。

## 2. 快速驗證（不發訊息，先看對端活著）

```bash
curl -s http://100.82.9.91:9900/health
# {"status": "ok", "agent": "taipei"}

curl -s http://100.82.9.91:9900/.well-known/agent.json
# 回傳 agent card：name / url / capabilities / skills / securitySchemes
```

`/health` 與 `/.well-known/agent.json` 都免 token；發訊息才需要 bearer。

## 3. 發訊息（SendMessage）— 實測 payload

```python
import json, urllib.request, time

URL  = "http://100.82.9.91:9900/"          # 對端 endpoint
TOK  = "<shared A2A_BEARER_TOKEN>"          # 對端 token
TEXT = "請你執行：<你的指揮訊息>"

body = {
  "jsonrpc": "2.0",
  "id": "cli-001",                          # 自己訂的請求 id，會原樣回傳
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "user",                       # 你是發起方 = user；對端回 agent
      "parts":  [ {"kind": "text", "text": TEXT} ]
    }
  }
}

req = urllib.request.Request(
    URL, data=json.dumps(body).encode(),
    headers={
      "Content-Type":  "application/json",
      "A2A-Version":   "1.0",
      "Authorization": f"Bearer {TOK}",
    })
with urllib.request.urlopen(req, timeout=600) as r:
    data = json.loads(r.read())

# 結果在 result.task.status.state / result.task.status.message.parts[].text
print(data["result"]["task"]["status"]["state"])     # TASK_STATE_COMPLETED
print(data["result"]["task"]["status"]["message"]["parts"][0]["text"])
```

### curl 版

```bash
curl -s http://100.82.9.91:9900/ \
  -H "Content-Type: application/json" \
  -H "A2A-Version: 1.0" \
  -H "Authorization: Bearer <shared-token>" \
  -d '{
    "jsonrpc":"2.0","id":"cli-001","method":"SendMessage",
    "params":{"message":{"role":"user","parts":[{"kind":"text","text":"你的訊息"}]}}
  }'
```

## 4. 回應結構（重點欄位）

```jsonc
{
  "jsonrpc": "2.0",
  "id": "cli-001",
  "result": {
    "task": {
      "id": "task-…",
      "contextId": "ctx-…",
      "status": {
        "state": "TASK_STATE_COMPLETED",      // 也看得到 TASK_STATE_WORKING 等
        "message": {
          "role": "ROLE_AGENT",
          "parts": [ {"text": "<agent 的回覆文字>"} ]
        }
      },
      "artifacts": [ ... ]                     // 額外出產物
    }
  }
}
```

> 對端 agent 的回覆常帶 reasoning 前綴（`💭 **Reasoning:**` 包 code block），
> 真正答案在其後的文字（例：`…\n\npong`）。讀取時取 `status.message.parts[].text` 即可。

## 5. Hermes 端設定（讓本機也把對端列為 peer）

`config.yaml`：
```yaml
a2a_agents:
  <peer-name>:            # e.g. dansui
    url: "http://<peer-ip>:9900/"
    auth:
      type: "bearer"
      token: "<shared-token>"
    timeout: 120
```

`.env`（本節點被呼叫時用的共用 token，雙方要一致）：
```
A2A_HOST=<你的 LAN IP>
A2A_PORT=9900
A2A_AGENT_NAME=<你的 agent 名>
A2A_REPLY_TIMEOUT=600
A2A_BEARER_TOKEN=<shared-token>
```

本節點 A2A server 由 Hermes gateway 自動 listen（`platforms.a2a.enabled: true`），
不需要手動起 process。驗證：`curl http://127.0.0.1:9900/health`。

## 6. 常見坑（實測）

1. **URL 結尾 `/` 不能漏**：`.../9900` 會 404；要 `.../9900/`。
2. **endpoint / agent name / token 三者要對同一台**。token 錯 → 401。
3. **token 是 64-char 共享值**，不是 GitHub 那支 `ghp_…`，別混用。
4. **長任務會佔住連線**：對端在跑時連線會等到完成或逾時才回。需要非同步就
   放 background，或把 `A2A_REPLY_TIMEOUT` 調大；別用 3s 這種小 timeout 去量。
5. **回覆含 reasoning**：取答案要看 `parts[].text` 尾段，別只切第一行。
6. **bearer 是 http scheme**（agent card `securitySchemes.bearer.type=http`），
   不是 basic；header 用 `Authorization: Bearer <tok>`。

## 7. 一行健康檢查（給 cron / 監控）

```bash
curl -sf http://<peer-ip>:9900/health >/dev/null && echo UP || echo DOWN
```
