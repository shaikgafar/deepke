import os
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Artificial Intelligence")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "07.0_subject_data_dictionary.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "08.0_index_ontology.json")

gemini_key = os.getenv("GEMINI_API_KEY", "")
gemini_client = None
if gemini_key:
    try:
        from google import genai
        from google.genai import types
        gemini_client = genai.Client(api_key=gemini_key)
    except Exception as e:
        print(f"[Warning] Gemini init error: {e}")

def local_index_ontology(terms):
    """Fallback local taxonomy clustering."""
    ontology = {
        f"{TARGET_SUBJECT} Core Concepts": {
            "Foundations": [],
            "Techniques": []
        },
        f"{TARGET_SUBJECT} Applied Systems": {
            "Tools & Frameworks": [],
            "Architectures": []
        }
    }
    for idx, term in enumerate(terms):
        t_low = term.lower()
        if any(w in t_low for w in ["tool", "system", "sql", "data", "spark", "python"]):
            ontology[f"{TARGET_SUBJECT} Applied Systems"]["Tools & Frameworks"].append(term)
        elif any(w in t_low for w in ["architecture", "model", "network"]):
            ontology[f"{TARGET_SUBJECT} Applied Systems"]["Architectures"].append(term)
        elif any(w in t_low for w in ["algorithm", "method", "descent", "regression"]):
            ontology[f"{TARGET_SUBJECT} Core Concepts"]["Techniques"].append(term)
        else:
            ontology[f"{TARGET_SUBJECT} Core Concepts"]["Foundations"].append(term)
    return ontology

def build_index_ontology():
    if not os.path.exists(INPUT_JSON):
        print(f"[ERROR] Could not find '{INPUT_JSON}'.")
        return

    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data_dictionary = json.load(f)
        
    terms = list(data_dictionary.keys())
    if not terms:
        print("[ERROR] No terms found in data dictionary.")
        return

    final_ontology = {}
    if gemini_client:
        try:
            from google.genai import types
            prompt = f"""
            You are an expert {TARGET_SUBJECT} Ontology Architect.
            Group these terms into 3-4 top-level Domains and Sub-Domains.
            Output ONLY valid JSON: {{"Domain": {{"SubDomain": ["term1", "term2"]}}}}.
            TERMS: {json.dumps(terms[:100])}
            """
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            final_ontology = json.loads(response.text)
        except Exception as e:
            print(f"    [API WARNING] Gemini call failed: {e}")

    if not final_ontology:
        print("  -> Using offline taxonomy classification...")
        final_ontology = local_index_ontology(terms)

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(final_ontology, f, indent=4)
        
    print(f"\n[SUCCESS] Saved index ontology to: {OUTPUT_JSON}")

if __name__ == "__main__":
    build_index_ontology()
