deepseek-file-vision-demo

**在线试验台：https://782042369.github.io/deepseek-file-vision-demo/**

DeepSeek 官方 Files API 最小试验：**上传一次图片 → 拿 `file_id` → 引用 `file_id` 重复识图**。

零依赖（Python 3 标准库），自动生成 100×100 纯红测试图，上传一次后用同一个 `file_id` 问两个不同问题。

## 运行

```bash
API_KEY=sk-xxx python3 demo.py

# 走自建网关/中转时：
API_KEY=sk-xxx BASE_URL=https://your-gateway MODEL=deepseek-flash python3 demo.py
```

预期输出（官方直连）：

```
[1] POST /files -> 200 {"id": "file-api-xxxx-...", "object": "file", "bytes": 335, "filename": "red.png", "purpose": "user_data"}
    file_id = file-api-xxxx-...
[2] POST /chat/completions -> 200 answer: '红色' | prompt_tokens: 225
[2] POST /chat/completions -> 200 answer: '没有' | prompt_tokens: 223
```

## curl 等价命令

```bash
# 1. 上传（multipart，purpose 必须是 user_data）
curl https://api.deepseek.com/files -H 'Authorization: Bearer sk-xxx' \
  -F purpose=user_data -F file=@red.png
# => {"id":"file-api-xxxx-...","bytes":335,"filename":"red.png","purpose":"user_data"}

# 2. 引用 file_id 识图（可反复调用，file 归属上传时的那个 API key）
curl https://api.deepseek.com/chat/completions -H 'Authorization: Bearer sk-xxx' \
  -H 'Content-Type: application/json' -d '{
    "model": "deepseek-flash",
    "messages": [{"role": "user", "content": [
      {"type": "text", "text": "这张图片主要是什么颜色？"},
      {"type": "file", "file_id": "file-api-xxxx-..."}
    ]}]
  }'
```

## 关键格式注意

- 内容块是 `{"type": "file", "file_id": "..."}`，**不是** `image_url`；
- `file` 块内 `file_data`（内联 base64 data URL）与 `file_id` 互斥，二选一；
- 文件归属上传它的 API key：同 key 下重复引用永久有效（默认不过期）；
- 单文件 ≤64MiB；`file_id` 方式不计入 48MiB 请求体限制，适合大图。

## 实测结论（2026-10）

| 目标 | /files 上传 | file_id 引用识图 | 备注 |
|---|---|---|---|
| api.deepseek.com 官方直连 | ✅ | ✅ 100% | 本 demo 验证 |
| new-api 自建网关（官方直连渠道） | ❌ 400（未实现 Files API） | ⚠️ 取决于渠道 | `type:file` 块可无损透传；但渠道配多 key 轮询时文件只归属一个 key，引用成功率=1/key数 |
| 第三方 new-api 站（sub2ai.vip） | ❌ 400 | ❌ 静默丢弃 | 返回 200 但图没进模型（prompt_tokens 仅文本）；该站只能用标准 `image_url` 格式 |

**验图技巧**：看响应里的 `prompt_tokens`——只有几十说明图没进模型（被网关丢弃），几百起说明图真的被处理了。

## 文档

- https://api-docs.deepseek.com/zh-cn/guides/files_api
- https://api-docs.deepseek.com/zh-cn/guides/vision