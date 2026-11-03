import os
import fitz  # PyMuPDF

# Silence non-fatal graphical/color profile warnings in the terminal
fitz.TOOLS.mupdf_display_errors(False) 

# Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_material")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed_text")

def convert_pdfs_to_text():
    if not os.path.exists(RAW_DIR):
        print(f"[ERROR] Directory not found: {RAW_DIR}")
        return
        
    # Ensure the staging directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Strictly scan the top-level raw_material folder
    pdf_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith('.pdf')]
            
    print(f"Found {len(pdf_files)} PDFs for extraction. Initiating text conversion...\n")
    
    success_count = 0
    
    for filename in pdf_files:
        pdf_path = os.path.join(RAW_DIR, filename)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
        
        # Idempotent skip: Do not re-process if the text file already exists
        if os.path.exists(output_file):
            print(f"  [SKIP] Text already extracted for: {filename}")
            continue
            
        try:
            # Open the document and extract text page by page
            doc = fitz.open(pdf_path)
            full_text = []
            for page in doc:
                full_text.append(page.get_text("text"))
            doc.close()
            
            # Join the pages together into a massive string
            raw_text = "\n".join(full_text)
            
            # Write to the staging folder
            with open(output_file, 'w', encoding='utf-8') as out_f:
                out_f.write(raw_text)
                
            print(f"  [SUCCESS] Converted: {filename} ({len(raw_text):,} characters)")
            success_count += 1
            
        except Exception as e:
            print(f"  [ERROR] Failed to convert {filename}. Reason: {e}")
            
    print(f"\n--- Conversion Complete ---")
    print(f"Successfully converted {success_count} new PDFs into {OUTPUT_DIR}")

if __name__ == "__main__":
    convert_pdfs_to_text()