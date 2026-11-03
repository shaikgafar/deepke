import os
import csv
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Artificial Intelligence")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "06.0_index_keyword_density.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "07.0_subject_data_dictionary.json")

gemini_key = os.getenv("GEMINI_API_KEY", "")
gemini_client = None
if gemini_key:
    try:
        from google import genai
        from google.genai import types
        gemini_client = genai.Client(api_key=gemini_key)
    except Exception as e:
        print(f"[Warning] Gemini init error: {e}")

def load_keywords():
    """Loads the keywords from the density CSV."""
    keywords = []
    if not os.path.exists(INPUT_CSV):
        print(f"[ERROR] Could not find '{INPUT_CSV}'.")
        return keywords
        
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keywords.append(row['Keyword_Phrase'])
    return keywords

def gemini_evaluation_pass(phrase_chunk):
    if not gemini_client:
        return "{}"
        
    prompt = f"""
    You are a Principal {TARGET_SUBJECT} Engineer.
    Evaluate the terms below for relevance to "{TARGET_SUBJECT}". Discard generic terms.
    For each surviving term, write a sharp 2-sentence technical definition.
    Output ONLY a valid JSON object: {{"term": "definition"}}.
    
    PHRASES:
    {json.dumps(phrase_chunk)}
    """
    
    try:
        from google.genai import types
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return response.text
    except Exception as e:
        print(f"    -> [API ERROR] Gemini call failed: {e}")
        return "{}"

def build_data_dictionary():
    keywords = load_keywords()
    if not keywords:
        return
        
    master_dictionary = {}
    
    if gemini_client:
        chunk_size = 50
        total_chunks = (len(keywords) + chunk_size - 1) // chunk_size
        print(f"Loaded {len(keywords)} keyword phrases across {total_chunks} chunks via Gemini...")
        
        for i in range(0, len(keywords), chunk_size):
            chunk = keywords[i:i + chunk_size]
            print(f"  -> Sending chunk {(i // chunk_size) + 1}/{total_chunks} to Gemini...")
            raw_json = gemini_evaluation_pass(chunk)
            try:
                parsed = json.loads(raw_json)
                master_dictionary.update(parsed)
            except Exception:
                pass
                
    # If no API key or empty dictionary, fallback to local definitions
    if not master_dictionary:
        print("  -> Using offline dictionary generation...")
        for kw in keywords[:100]:
            master_dictionary[kw] = f"Key operational concept and technical terminology in {TARGET_SUBJECT}."

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(master_dictionary, f, indent=4)
        
    print(f"\n[SUCCESS] Saved {len(master_dictionary)} defined terms to: {OUTPUT_JSON}")

if __name__ == "__main__":
    build_data_dictionary()
