import requests
import io
import time
import os

print("Testing chunked upload...")
pdf_4mb = b"%PDF-1.4\n" + b"A" * (4 * 1024 * 1024)

# 1. Start Upload
res = requests.post("http://127.0.0.1:8005/upload/start", json={"filename": "test.pdf"})
print(f"Start: {res.status_code} - {res.text}")
data = res.json()
upload_id = data["upload_id"]

# 2. Upload Chunks
chunk_size = 1024 * 1024
total_chunks = (len(pdf_4mb) + chunk_size - 1) // chunk_size

for i in range(total_chunks):
    start = i * chunk_size
    end = min(start + chunk_size, len(pdf_4mb))
    chunk = pdf_4mb[start:end]
    
    res = requests.post(f"http://127.0.0.1:8005/upload/chunk/{upload_id}", files={"file": ("chunk", chunk)})
    print(f"Chunk {i}: {res.status_code}")

# 3. Start Translate
res = requests.post(f"http://127.0.0.1:8005/translate/start/{upload_id}")
print(f"Translate Start: {res.status_code} - {res.text}")
