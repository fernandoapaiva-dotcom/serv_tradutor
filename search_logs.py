import sys

log_path = r"C:\Users\comer\.gemini\antigravity\brain\c26aedfe-4990-454c-9242-6d1180666bc0\.system_generated\tasks\task-778.log"
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        if "upload" in line.lower() or "chunk" in line.lower():
            print(line.strip())
