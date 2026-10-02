# Contributing — 共同維護協議

本 repo 是兩節點（**taipei** / **dansui**）的共同 skill 資料庫，由 Kevin 所有（account `z12957`）。
本文件是**公開**的协作协议；內部端點、token、機房資訊**一律不進 repo**（參 `SECURITY.md`）。

## 1. 什麼放進 repo

| ✅ 放 | ❌ 留本機 |
|---|---|
| 通用 playbook / 診斷流程（不綁定任何機房） | 具體 machine ID、SSH alias、LAN/BMC IP |
| 空白 template（讓各節點自己填） | 已填好的 fleet inventory |
| 健檢腳本（不含憑證，讀環境變數即可） | 任何 token / 密碼 / DPAPI blob 路徑 |
| 踩坑紀律（"為什麼"型） | 單次事件日誌（放各節點自己的 session/skill） |

判定原則：**把 repo 內容原樣給一個陌生節點，它能直接照做且不洩露我方資產 = 可以放。**

## 2. 結構

```
skills/<skill-name>/
├── SKILL.md          # frontmatter + playbook
├── references/       # 細節文件（按需載入）
└── scripts/          # 可執行腳本
README.md / SECURITY.md / CONTRIBUTING.md
```

- 新 skill = 新目錄；frontmatter 必填 `name` / `description`。
- 一個 skill 一個主題，不做大雜燴。

## 3. 如何貢獻（兩條路）

### 路徑 A — git（推薦）
```bash
git clone https://github.com/z12957/feihuang-hermes
# 改完
git add -A && git commit -m "skills: <一句話>" && git push
```
需要的 token 權限：`Contents: Read+Write`，repository access 綁定本 repo（fine-grained PAT）或 classic `repo` scope。

### 路徑 B — GitHub REST API
`PUT /repos/z12957/feihuang-hermes/contents/<path>`（更新必帶舊 `sha`；缺 `Accept: application/vnd.github+json` 會 406）。
完整端點與範例由 Kevin 經 A2A 私傳，**不放公 repo**。

## 4. 審核紀律

- 兩節點皆可讀；**push 前**：
  1. secret scan（grep 已知 token 前綴 / IP / 機房字眼）
  2. 確認第 1 節的進/留分界
- Kevin 是唯一 final approver；有疑義先問再推。
- 破壞性操作（刪 skill、改 SECURITY.md）需 Kevin 明確同意。

## 5. 各節點本地落地

```bash
hermes skills tap add z12957/feihuang-hermes
hermes skills install z12957/feihuang-hermes/<skill-name>   # community source 加 --force
```
本地 skill 與 repo 版的分工：**repo 版 = 通用流程；本地版 = 通用流程 + 本節點 inventory（private，不 commit）。**
