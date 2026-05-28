import requests

pdf_10kb = b"%PDF-1.4\n" + b"A" * (10 * 1024)
res = requests.post("http://127.0.0.1:8005/upload/chunk/uuid", files={"file": ("blob", pdf_10kb, "application/octet-stream")})
print(res.status_code, res.text)
