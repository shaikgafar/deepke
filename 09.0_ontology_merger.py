import os
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Subject")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_JSON_02 = os.path.join(BASE_DIR, "02.0_subject_ontology_master.json")
PEER_JSON_08 = os.path.join(BASE_DIR, "08.0_index_ontology.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "09.0_unified_master_ontology.json")

gemini_key = os.getenv("GEMINI_API_KEY", "")
gemini_client = None
if gemini_key:
    try:
        from google import genai
        from google.genai import types
        gemini_client = genai.Client(api_key=gemini_key)
    except Exception as e:
        print(f"[Warning] Gemini init error: {e}")

def local_merge_ontologies(master_data, peer_data):
    """Direct dictionary merge when API key is unavailable."""
    unified = dict(master_data)
    for domain, subdomains in peer_data.items():
        if domain not in unified:
            unified[domain] = {}
        if isinstance(subdomains, dict):
            for sub, items in subdomains.items():
                if sub not in unified[domain]:
                    unified[domain][sub] = []
                if isinstance(items, list):
                    unified[domain][sub] = list(set(unified[domain][sub] + items))
                elif isinstance(items, dict):
                    unified[domain][sub] = items
        elif isinstance(subdomains, list):
            unified[domain]["General Topics"] = list(set(unified[domain].get("General Topics", []) + subdomains))
    return unified

def merge_ontologies():
    if not os.path.exists(MASTER_JSON_02) or not os.path.exists(PEER_JSON_08):
        print("[ERROR] Missing prerequisite ontology files (02.0 or 08.0).")
        return

    with open(MASTER_JSON_02, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
    with open(PEER_JSON_08, 'r', encoding='utf-8') as f:
        peer_data = json.load(f)

    unified = local_merge_ontologies(master_data, peer_data)
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(unified, f, indent=4)
        
    print(f"\n[SUCCESS] Unified master ontology saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    merge_ontologies()
