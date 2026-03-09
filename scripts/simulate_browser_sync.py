import requests
import json
import time

API_BASE = "http://localhost:8000/api"

# 1. Login to get token (Change these if you registered different credentials)
def get_token():
    try:
        resp = requests.post(f"{API_BASE}/auth/login", data={
            "username": "testuser@devbrain.dev",
            "password": "password123"
        })
        return resp.json().get("access_token")
    except:
        print("Error: Make sure the server is running on localhost:8000")
        return None

# 2. Simulate browser history entries
HISTORY_ENTRIES = [
    {"url": "https://react.dev/learn/hooks", "title": "React Hooks - Intro to State"},
    {"url": "https://fastapi.tiangolo.com/tutorial/bigger-applications/", "title": "FastAPI Bigger Applications"},
    {"url": "https://docs.docker.com/engine/reference/builder/", "title": "Docker - Dockerfile Advanced Reference"},
    {"url": "https://www.typescriptlang.org/docs/handbook/2/generics.html", "title": "TypeScript Generics Guide"},
    {"url": "https://pytorch.org/tutorials/beginner/blitz/tensor_tutorial.html", "title": "PyTorch Tensors Deep Dive"}
]

def simulate_extension():
    token = get_token()
    if not token: return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"🚀 Simulating Browser History Sync for 5 entries...")
    
    for entry in HISTORY_ENTRIES:
        print(f"  → Syncing: {entry['title']}")
        resp = requests.post(f"{API_BASE}/events/browser", json=entry, headers=headers)
        if resp.status_code == 200:
            result = resp.json()
            analysis = result["detected"]
            print(f"    ✅ Classified as: {analysis['tech']} ({analysis['domain']}) | Confidence: {analysis['confidence']}")
        else:
            print(f"    ❌ Failed: {resp.text}")
        time.sleep(0.5)

    print("\n✨ Done! Check your Dashboard Skill Graph now.")

if __name__ == "__main__":
    simulate_extension()
