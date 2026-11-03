import os
import re
import fitz  # PyMuPDF

# Silence non-fatal graphical/color profile warnings in the terminal
fitz.TOOLS.mupdf_display_errors(False) 

# Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_material")
INDEX_OUTPUT_DIR = os.path.join(BASE_DIR, "raw_indexes")

def extract_index_pages():
    if not os.path.exists(RAW_DIR):
        print(f"[ERROR] Directory not found: {RAW_DIR}")
        return

    os.makedirs(INDEX_OUTPUT_DIR, exist_ok=True)
    
    # Strictly scan the top-level raw_material folder
    pdf_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith('.pdf')]
    print(f"Found {len(pdf_files)} textbooks to scan for index pages.\n")

    for filename in pdf_files:
        pdf_path = os.path.join(RAW_DIR, filename)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(INDEX_OUTPUT_DIR, f"{base_name}_index_raw.txt")

        if os.path.exists(output_file):
            print(f"  [SKIP] Index already extracted for: {filename}")
            continue

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Indexes are always at the back. We'll look at the last 8% of the book.
            scan_start_page = max(0, int(total_pages * 0.92))
            
            index_text = []
            found_index_heading = False
            
            for page_num in range(scan_start_page, total_pages):
                page = doc[page_num]
                text = page.get_text("text")
                
                # Catch where the index actually starts so we don't grab preceding chapters
                if "index" in text.lower() and not found_index_heading:
                    found_index_heading = True
                
                if found_index_heading:
                    index_text.append(f"--- PAGE {page_num + 1} ---\n{text}")
            
            # If no back index was found (common for papers, single chapters, or non-indexed PDFs):
            if not index_text:
                print(f"  [AUTO-FALLBACK] No index section found in back of: {filename}")
                print(f"  -> Extracting candidate technical terms directly from body text...")
                
                body_phrases = []
                for p_idx in range(min(total_pages, 50)): # Scan first 50 pages
                    p_text = doc[p_idx].get_text("text")
                    # Extract capitalized noun sequences
                    caps = re.findall(r'\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){1,3}\b', p_text)
                    for c in caps:
                        if len(c) > 4:
                            body_phrases.append(f"{c}, page {p_idx + 1}")
                            
                doc.close()
                
                if body_phrases:
                    # Deduplicate while preserving order
                    unique_phrases = list(dict.fromkeys(body_phrases))
                    with open(output_file, 'w', encoding='utf-8') as out_f:
                        out_f.write("\n".join(unique_phrases[:1500]))
                    print(f"  [SUCCESS] Generated candidate index from body text for: {filename} ({len(unique_phrases[:1500])} terms)")
                else:
                    print(f"  [WARNING] Could not extract text terms from: {filename}")
            else:
                doc.close()
                with open(output_file, 'w', encoding='utf-8') as out_f:
                    out_f.write("\n".join(index_text))
                print(f"  [SUCCESS] Extracted index pages for: {filename}")

        except Exception as e:
            print(f"  [ERROR] Failed to process {filename}. Reason: {e}")

if __name__ == "__main__":
    extract_index_pages()
