import requests
import io
import time

print("Testing 4MB PDF and polling...")
pdf_4mb = b"%PDF-1.4\n" + b"A" * (4 * 1024 * 1024)
res = requests.post("https://tradutor-pdf-servsolda.fly.dev/translate", files={"file": ("test.pdf", pdf_4mb, "application/pdf")})
print(f"Status: {res.status_code}")
data = res.json()
print(f"Data: {data}")

job_id = data["job_id"]
machine_id = data["machine_id"]

for _ in range(5):
    time.sleep(3)
    headers = {"fly-force-instance-id": machine_id}
    status_res = requests.get(f"https://tradutor-pdf-servsolda.fly.dev/translate/status/{job_id}", headers=headers)
    print(f"Poll Status: {status_res.status_code}")
    print(f"Poll Body: {status_res.text}")
