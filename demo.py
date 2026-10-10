#!/usr/bin/env python3
"""DeepSeek Files API minimal demo: upload once -> file_id -> recognize repeatedly.

Usage:
  API_KEY=sk-xxx python3 demo.py
  API_KEY=sk-xxx BASE_URL=https://your-gateway MODEL=deepseek-flash python3 demo.py

Stdlib only, no dependencies. Generates a red test PNG inline, uploads it once,
then asks two different questions referencing the same file_id.
"""
import json, os, struct, sys, urllib.error, urllib.request, uuid, zlib

BASE_URL = os.environ.get("BASE_URL", "https://api.deepseek.com").rstrip("/")
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ.get("MODEL", "deepseek-flash")
CRLF = bytes([13, 10])


def make_red_png(w=100, h=100):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = b""
    for _ in range(h):
        raw += bytes([0]) + bytes([0xE8, 0, 0]) * w
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    sig = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def multipart(fname, fdata, ftype):
    b = "----" + uuid.uuid4().hex
    parts = [
        "--" + b,
        'Content-Disposition: form-data; name="purpose"',
        "",
        "user_data",
        "--" + b,
        'Content-Disposition: form-data; name="file"; filename="' + fname + '"',
        "Content-Type: " + ftype,
        "",
    ]
    head = CRLF.join(x.encode() for x in parts) + CRLF
    tail = CRLF + ("--" + b + "--").encode() + CRLF
    return head + fdata + tail, "multipart/form-data; boundary=" + b


def http(method, path, headers, body=None):
    req = urllib.request.Request(BASE_URL + path, data=body, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def upload_image():
    body, ctype = multipart("red.png", make_red_png(), "image/png")
    st, data = http("POST", "/files", {"Authorization": "Bearer " + API_KEY, "Content-Type": ctype}, body)
    print("[1] POST /files ->", st, json.dumps(data, ensure_ascii=False))
    return data.get("id")


def ask(content):
    payload = {"model": MODEL, "messages": [{"role": "user", "content": content}], "max_tokens": 300}
    st, data = http("POST", "/chat/completions",
                    {"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"},
                    json.dumps(payload).encode())
    msg = (data.get("choices") or [{}])[0].get("message", {})
    print("[2] POST /chat/completions ->", st, "answer:", repr(msg.get("content")),
          "| prompt_tokens:", data.get("usage", {}).get("prompt_tokens"))


def main():
    if not API_KEY:
        sys.exit("set API_KEY env first")
    fid = upload_image()
    if not fid:
        sys.exit("upload failed, no file_id")
    print("    file_id =", fid)
    ask([{"type": "text", "text": "这张图片主要是什么颜色？只回答颜色名"},
         {"type": "file", "file_id": fid}])
    ask([{"type": "text", "text": "这张图片里有没有文字？只回答有或没有"},
         {"type": "file", "file_id": fid}])


if __name__ == "__main__":
    main()