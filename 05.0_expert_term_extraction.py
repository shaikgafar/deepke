import os
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Artificial Intelligence")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "raw_indexes")
OUTPUT_JSON = os.path.join(BASE_DIR, "05.0_extracted_expert_terms.json")

openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
openrouter_client = None
if openrouter_key:
    try:
        from openai import OpenAI
        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
    except Exception as e:
        print(f"[Warning] OpenRouter init error: {e}")

def chunk_list(lst, chunk_size):
    """Yields successive chunks from a list."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def local_semantic_filter(lines):
    """Extracts technical terms from raw index text using local NLP regex."""
    terms = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("---") or line.lower().startswith(("see ", "see also", "page ")):
            continue
        # Strip trailing page numbers, e.g. "Gradient Descent, 45, 52-54"
        clean = re.sub(r',?\s*(page\s*)?\d+.*$', '', line, flags=re.IGNORECASE).strip()
        clean = re.sub(r'^\W+|\W+$', '', clean)
        # Avoid generic short single words
        if len(clean) >= 3 and not clean.isdigit():
            terms.append(clean)
    return list(dict.fromkeys(terms))

def deepseek_semantic_filter(filename, chunk_text):
    if not openrouter_client:
        return []
        
    prompt = f"""
    You are a Principal {TARGET_SUBJECT} Architect performing data extraction on a raw text dump from the back of a technical book.
    Extract the core technical phrases. Output ONLY a valid JSON array of strings.
    Example Output: ["Concept Alpha", "Methodology Beta", "Advanced Theorem Gamma"]
    
    RAW TEXT CHUNK TO PROCESS:
    {chunk_text}
    """
    
    try:
        response = openrouter_client.chat.completions.create(
            model="deepseek/deepseek-chat", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            return json.loads(content)
        return []
    except Exception as e:
        print(f"    -> [API WARNING] DeepSeek call failed: {e}")
        return []

def extract_expert_terms():
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Could not find '{INPUT_DIR}'.")
        return

    extracted_master_list = {}
    total_phrases_found = 0

    index_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.txt')]
    print(f"Found {len(index_files)} raw index files for term extraction.\n")

    for filename in index_files:
        filepath = os.path.join(INPUT_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            continue
            
        print(f"Processing '{filename}' ({len(lines)} lines)...")
        book_terms = []
        
        if openrouter_client:
            chunks = list(chunk_list(lines, 150))
            for i, chunk in enumerate(chunks):
                chunk_string = "".join(chunk)
                valid_phrases = deepseek_semantic_filter(filename, chunk_string)
                if valid_phrases:
                    book_terms.extend(valid_phrases)
                    
        # If no terms extracted via API (or no API key), use local NLP extraction
        if not book_terms:
            print("  -> Using local NLP phrase extraction...")
            book_terms = local_semantic_filter(lines)
            
        book_terms = sorted(list(set(book_terms)))
        if book_terms:
            extracted_master_list[filename] = book_terms
            total_phrases_found += len(book_terms)
            print(f"  [SUCCESS] Extracted {len(book_terms)} {TARGET_SUBJECT} phrases from {filename}.\n")

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as out_f:
        json.dump(extracted_master_list, out_f, indent=4)

    print(f"--- Extraction Complete ---")
    print(f"Total Phrases Extracted: {total_phrases_found}")
    print(f"Data saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    extract_expert_terms()
