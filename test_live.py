import requests
import io
import time

print("Testing chunked upload on live server...")
pdf_10kb = b"%PDF-1.4\n" + b"A" * (10 * 1024)

# 1. Start Upload
res = requests.post("https://tradutor-pdf-servsolda.fly.dev/upload/start", json={"filename": "test.pdf"})
print(f"Start: {res.status_code} - {res.text}")
data = res.json()
upload_id = data["upload_id"]
machine_id = data.get("machine_id", "")

headers = {}
if machine_id:
    headers["fly-force-instance-id"] = machine_id

# 2. Upload Chunk
res = requests.post(f"https://tradutor-pdf-servsolda.fly.dev/upload/chunk/{upload_id}", headers=headers, files={"file": ("chunk.pdf", pdf_10kb)})
print(f"Chunk: {res.status_code} - {res.text}")

# 3. Start Translate
res = requests.post(f"https://tradutor-pdf-servsolda.fly.dev/translate/start/{upload_id}", headers=headers)
print(f"Translate Start: {res.status_code} - {res.text}")
