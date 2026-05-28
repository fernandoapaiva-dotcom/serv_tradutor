import requests
import io

print("Testing 4MB PDF...")
pdf_4mb = b"%PDF-1.4\n" + b"A" * (4 * 1024 * 1024)
try:
    res = requests.post("https://tradutor-pdf-servsolda.fly.dev/translate", files={"file": ("test.pdf", pdf_4mb, "application/pdf")})
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text}")
except Exception as e:
    print(f"Exception: {e}")
