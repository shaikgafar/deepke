import os
import re
import fitz  # PyMuPDF
import json

# Define relative paths for GitHub portability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_material")
OUTPUT_JSON = os.path.join(BASE_DIR, "extracted_tocs.json")

def detect_headings_as_toc(doc):
    """Heuristically extracts chapter/section headings if no embedded TOC exists."""
    headings_toc = []
    seen = set()
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        blocks = page.get_text("blocks")
        for b in blocks:
            block_text = b[4].strip() if len(b) > 4 else ""
            lines = [l.strip() for l in block_text.splitlines() if l.strip()]
            if 1 <= len(lines) <= 2:
                line = lines[0]
                if 3 < len(line) < 80 and line.lower() not in seen:
                    if re.match(r'^(Chapter|Section|\d+(\.\d+)*|[A-Z][A-Za-z0-9\s]{3,50})$', line):
                        seen.add(line.lower())
                        headings_toc.append([1, line, page_idx + 1])
    return headings_toc

def scan_for_tocs():
    """Scans PDFs directly in the raw_material folder for embedded or auto-detected Tables of Contents."""
    
    if not os.path.exists(RAW_DIR):
        print(f"[ERROR] Directory not found: {RAW_DIR}")
        return

    toc_master_dict = {}
    success_count = 0
    total_pdfs = 0

    print(f"Scanning '{RAW_DIR}' for PDFs with embedded Tables of Contents...\n")

    # Use os.listdir to strictly scan the top-level raw_material folder
    for filename in os.listdir(RAW_DIR):
        if not filename.lower().endswith(".pdf"):
            continue
            
        total_pdfs += 1
        pdf_path = os.path.join(RAW_DIR, filename)
        
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()
            
            if toc:
                print(f"[SUCCESS] Embedded TOC found: {filename} ({len(toc)} hierarchical items)")
                toc_master_dict[filename] = toc
                success_count += 1
            else:
                # Fallback: Auto-detect headings from page content
                detected_toc = detect_headings_as_toc(doc)
                if detected_toc:
                    print(f"[AUTO-DETECT] Generated {len(detected_toc)} TOC items from headings for: {filename}")
                    toc_master_dict[filename] = detected_toc
                    success_count += 1
                else:
                    # Minimal placeholder TOC so pipeline does not drop the document
                    print(f"[FALLBACK] Generated root section TOC for: {filename}")
                    toc_master_dict[filename] = [[1, os.path.splitext(filename)[0], 1]]
                    success_count += 1
                
            doc.close()
            
        except Exception as e:
            print(f"[ERROR] Could not process {filename}: {e}")

    # Save the extracted TOCs to a JSON file for the next phase of the pipeline
    if toc_master_dict:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(toc_master_dict, f, indent=4)

    print(f"\n--- Scan Complete ---")
    print(f"Total PDFs Scanned: {total_pdfs}")
    print(f"PDFs Processed: {success_count}")
    print(f"Extracted hierarchical data saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    scan_for_tocs()
