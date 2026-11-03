import os
import json
import re
import csv
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Universal Subject Variable
TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Artificial Intelligence")

# Define Paths (Updated to match the new generic naming convention)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "05.0_extracted_expert_terms.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "06.0_index_keyword_density.csv")

# Standard technical stop words to prevent junk n-grams
STOP_WORDS = set([
    "the", "and", "to", "of", "a", "in", "that", "is", "for", "it", "with", "as", 
    "on", "are", "be", "this", "by", "an", "or", "at", "from", "which", "but", 
    "not", "we", "can", "use", "using", "used", "via", "based", "their", "its",
    "how", "when", "out", "then", "into", "through", "very", "much", "many", "most"
])

def extract_ngrams(text):
    """Tokenizes text and returns 1, 2, and 3-word combinations, ignoring stop words."""
    words = re.findall(r'\b[a-z0-9\-]+\b', text)
    clean_words = [w for w in words if w not in STOP_WORDS]
    
    ngrams = []
    
    # 1-word (Unigrams)
    ngrams.extend(clean_words)
    
    # 2-word (Bigrams)
    for i in range(len(clean_words) - 1):
        ngrams.append(f"{clean_words[i]} {clean_words[i+1]}")
        
    # 3-word (Trigrams)
    for i in range(len(clean_words) - 2):
        ngrams.append(f"{clean_words[i]} {clean_words[i+1]} {clean_words[i+2]}")
        
    return ngrams

def process_expert_terms():
    if not os.path.exists(INPUT_JSON):
        print(f"[ERROR] Could not find '{INPUT_JSON}'.")
        return

    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        master_dict = json.load(f)

    print(f"Loaded curated {TARGET_SUBJECT} index data for {len(master_dict)} books. Processing phrases...")

    global_ngram_counts = Counter()

    for book, phrases in master_dict.items():
        for phrase in phrases:
            # Lowercase the phrase for uniformity
            phrase = phrase.lower()
            
            # Step 1: Hunt for Acronyms in parentheses
            acronym_match = re.search(r'\((.*?)\)', phrase)
            if acronym_match:
                acronym = acronym_match.group(1).strip()
                # Count the standalone acronym
                if len(acronym) > 1 and acronym not in STOP_WORDS:
                    global_ngram_counts[acronym] += 1
                    
            # Step 2: Strip out the parentheses completely to clean the base string
            clean_phrase = re.sub(r'\(.*?\)', '', phrase).strip()
            
            # Step 3: Run the N-Gram generator on the clean phrase
            extracted_ngrams = extract_ngrams(clean_phrase)
            global_ngram_counts.update(extracted_ngrams)

    # LOWERED THRESHOLD: Keep any phrase that appears at least 2 times
    ranked_ngrams = [
        (term, count) for term, count in global_ngram_counts.items() if count >= 2
    ]
    
    # Sort by frequency (highest first)
    ranked_ngrams.sort(key=lambda x: x[1], reverse=True)

    # Export to CSV
    print(f"Extracted {len(ranked_ngrams):,} highly dense, cross-validated {TARGET_SUBJECT} N-Grams.")
    print(f"Writing to CSV...")
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Keyword_Phrase', 'Word_Count', 'Frequency_Density'])
        
        for term, count in ranked_ngrams:
            word_count = len(term.split())
            writer.writerow([term, word_count, count])

    print(f"\n--- Density Analysis Complete ---")
    print(f"Results safely saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    process_expert_terms()