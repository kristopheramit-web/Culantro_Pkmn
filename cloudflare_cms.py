# cloudflare_cms.py
import os
import json
import subprocess
import urllib.request

CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
DOMAIN_NAME = "drft.stream"

def push_game_state_to_cloudflare(state_dict: dict) -> bool:
    """
    Synchronizes the live game state and session library to Cloudflare KV / Pages
    so visitors on drft.stream can view active lobbies and download binaries 24/7.
    """
    payload = json.dumps(state_dict).encode("utf-8")
    print(f"[Cloudflare CMS] Synchronizing game state to {DOMAIN_NAME}...")
    
    # If a Wrangler worker endpoint or custom KV binding is set, push data
    if not CF_API_TOKEN:
        print("[Cloudflare CMS] No CF_API_TOKEN configured. Saving locally to cloudflare_sync_cache.json")
        with open("cloudflare_sync_cache.json", "w", encoding="utf-8") as f:
            f.json = state_dict
            json.dump(state_dict, f, indent=2)
        return True
        
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/LENTAL_KV/values/active_game_state"
    req = urllib.request.Request(endpoint, data=payload, headers={
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }, method="PUT")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("success"):
                print(f"[Cloudflare CMS] Successfully pushed state to {DOMAIN_NAME}!")
                return True
    except Exception as e:
        print(f"[WARN] Cloudflare sync failed: {e}")
    return False

def deploy_to_cloudflare_pages():
    """
    Triggers Wrangler CLI to deploy static web frontend files (lental_ui.html, assets/)
    directly to global Cloudflare CDN edge servers for drft.stream.
    """
    print("[Wrangler] Deploying static assets to Cloudflare Pages for drft.stream...")
    try:
        result = subprocess.run(["npx", "wrangler", "pages", "deploy", ".", "--project-name=culantro-stream"], capture_output=True, text=True, timeout=45)
        print(result.stdout)
        if result.returncode == 0:
            print("[SUCCESS] drft.stream updated and deployed globally!")
        else:
            print(f"[ERROR] Wrangler deployment output: {result.stderr}")
    except FileNotFoundError:
        print("[INFO] Node/Wrangler CLI not installed locally (expected while laptop is at technician). Skipping auto-deploy.")
    except Exception as e:
        print(f"[WARN] Deployment exception: {e}")

if __name__ == "__main__":
    print("Testing Cloudflare CMS synchronization module for drft.stream...")
    deploy_to_cloudflare_pages()
  
