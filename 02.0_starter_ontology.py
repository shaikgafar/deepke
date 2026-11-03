import os
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Universal Subject Variable
# Defaults to "Artificial Intelligence" if TARGET_SUBJECT is missing from the .env file
TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Artificial Intelligence")

# Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "extracted_tocs.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "02.0_subject_ontology_master.json")

openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
gemini_key = os.getenv("GEMINI_API_KEY", "")

# Initialize Clients safely
openrouter_client = None
if openrouter_key:
    try:
        from openai import OpenAI
        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
    except Exception as e:
        print(f"[Warning] OpenRouter client init error: {e}")

gemini_client = None
if gemini_key:
    try:
        from google import genai
        from google.genai import types
        gemini_client = genai.Client(api_key=gemini_key)
    except Exception as e:
        print(f"[Warning] Gemini client init error: {e}")

def load_and_filter_toc_data():
    if not os.path.exists(INPUT_JSON):
        print(f"[ERROR] Could not find {INPUT_JSON}")
        return {}
        
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        toc_data = json.load(f)
        
    EXCLUDE_KEYWORDS = ["biology", "history", "anatomy", "philosophy", "poetry"]
    filtered_data = {}
    
    for file_key, toc_list in toc_data.items():
        flat_toc = " ".join([str(item) for item in toc_list]).lower()
        # Keep everything if only 1 book or if subject specifically matches
        if not any(keyword in flat_toc for keyword in EXCLUDE_KEYWORDS) or len(toc_data) <= 1:
            filtered_data[file_key] = toc_list
            
    print(f"Loaded {len(filtered_data)} books for skeleton extraction.")
    return filtered_data

def local_toc_skeleton_builder(filtered_data):
    """Constructs high-level ontology skeleton directly from TOC items without needing API keys."""
    print(f"\n[LOCAL SKELETON BUILDER] Synthesizing {TARGET_SUBJECT} ontology skeleton from document structure...")
    skeleton = {}
    for filename, toc_list in filtered_data.items():
        current_domain = None
        for item in toc_list:
            lvl = item[0] if len(item) > 0 else 1
            title = str(item[1]).strip() if len(item) > 1 else ""
            if not title or len(title) < 2:
                continue
            if lvl == 1:
                current_domain = title
                if current_domain not in skeleton:
                    skeleton[current_domain] = {}
            elif lvl == 2:
                if not current_domain:
                    current_domain = f"{TARGET_SUBJECT} Foundations"
                    if current_domain not in skeleton:
                        skeleton[current_domain] = {}
                skeleton[current_domain][title] = []
                
    if not skeleton:
        skeleton = {
            f"{TARGET_SUBJECT} Core": {
                "Foundational Concepts": [],
                "Architectures & Methods": [],
                "Applications & Systems": []
            }
        }
    return skeleton

def gemini_stage1_architect(toc_data_string):
    if not gemini_client:
        return {}
        
    print(f"\n[STAGE 1] Gemini (Lead Architect) is designing the {TARGET_SUBJECT} master skeleton...")
    temp_path = os.path.join(BASE_DIR, "temp_toc_payload.txt")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(toc_data_string)
        
    try:
        from google.genai import types
        gemini_file = gemini_client.files.upload(
            file=temp_path,
            config=types.UploadFileConfig(mime_type="text/plain")
        )
        
        file_info = gemini_client.files.get(name=gemini_file.name)
        while file_info.state.name == "PROCESSING":
            time.sleep(2)
            file_info = gemini_client.files.get(name=gemini_file.name)
        
        prompt = f"""
        You are the Principal Systems Architect for {TARGET_SUBJECT}. Review the attached textbook TOC data and establish the high-level skeleton of our {TARGET_SUBJECT} Ontology.
        Output ONLY valid JSON in this structure:
        {{
            "Domain Name": {{
                "Category Name 1": {{}},
                "Category Name 2": {{}}
            }}
        }}
        """
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[gemini_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1 
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"    [API ERROR] Gemini call failed: {e}")
        return {}

def build_ontology():
    toc_data = load_and_filter_toc_data()
    if not toc_data:
        print("[ERROR] No Table of Contents data found to build ontology.")
        return

    skeleton = {}
    if gemini_client:
        skeleton = gemini_stage1_architect(json.dumps(toc_data))
        
    if not skeleton:
        print("  -> Using offline document structural analysis for ontology skeleton.")
        skeleton = local_toc_skeleton_builder(toc_data)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(skeleton, f, indent=4)
        
    print(f"\n[SUCCESS] Starter ontology skeleton saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    build_ontology()
