"""Throwaway harness — test DeepSeek API connectivity"""
import sys
import time
import os

LOG = []

def log(msg):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    print(msg, flush=True)

log("=== API Connectivity Test ===")
log(f"Python: {sys.version}")
log(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'not set')}")
log(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'not set')}")

log("Step 1: import openai...")
try:
    from openai import OpenAI
    log("OK")
except Exception as e:
    log(f"FAIL: {e}")
    sys.exit(1)

log("Step 2: create client (timeout=10s)...")
try:
    client = OpenAI(api_key="sk-test-key", base_url="https://api.deepseek.com", timeout=10.0)
    log("OK")
except Exception as e:
    log(f"FAIL: {e}")
    sys.exit(1)

log("Step 3: call API (expecting auth error, not timeout)...")
try:
    t0 = time.time()
    client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=5,
    )
    elapsed = time.time() - t0
    log(f"UNEXPECTED SUCCESS in {elapsed:.1f}s")
except Exception as e:
    elapsed = time.time() - t0
    err_msg = str(e)
    log(f"Failed in {elapsed:.1f}s")
    log(f"Error: {err_msg}")

    if "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
        log("DIAGNOSIS: Network timeout — cannot reach api.deepseek.com")
        log("FIX: Set HTTP_PROXY/HTTPS_PROXY in start.bat")
    elif "401" in err_msg or "unauthorized" in err_msg.lower() or "authentication" in err_msg.lower():
        log("DIAGNOSIS: API reachable but auth failed (expected with test key)")
        log("GOOD: Network works! Use a real API key.")
    elif "connection" in err_msg.lower() or "refused" in err_msg.lower():
        log("DIAGNOSIS: Connection refused — network blocked")
        log("FIX: Set HTTP_PROXY/HTTPS_PROXY in start.bat")
    else:
        log("DIAGNOSIS: Unknown error")

log("=== Test complete ===")
log(f"\nFull log:\n" + "\n".join(LOG))
