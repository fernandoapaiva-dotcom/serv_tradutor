import sys
import requests

try:
    print("Testing 60MB PDF...")
    pdf = b"%PDF-1.4\n" + b"A" * (60 * 1024 * 1024)
    res = requests.post("https://tradutor-pdf-servsolda.fly.dev/translate", files={"file": ("test60.pdf", pdf, "application/pdf")})
    print("Status:", res.status_code)
    print("Body:", res.text[:200])
except Exception as e:
    import traceback
    traceback.print_exc(file=sys.stdout)
