"""
extract_from_file.py
Command-line tool to extract entities and build an ontology from any single file.
Usage:
    python extract_from_file.py my_document.pdf
    python extract_from_file.py path/to/document.docx --subject "Data Science" --mode local
"""

import os
import sys
import argparse
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from file_processor import process_uploaded_file
from file_entity_extractor import (
    extract_entities_from_document,
    generate_interactive_graph_html
)

def main():
    parser = argparse.ArgumentParser(description="Extract entities and build knowledge graph from any single file.")
    parser.add_argument("file", help="Path to the file to process (.pdf, .docx, .txt, .md)")
    parser.add_argument("--subject", default=os.getenv("TARGET_SUBJECT", "Auto-detect"), help="Target subject/domain")
    parser.add_argument("--mode", default="auto", choices=["auto", "local", "gemini", "openrouter"], help="Extraction engine")
    parser.add_argument("--max-entities", type=int, default=60, help="Maximum number of entities to extract")
    parser.add_argument("--output-dir", default=".", help="Directory to save output files")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        sys.exit(1)
        
    print(f"\n{'='*60}")
    print(f" Processing File: {os.path.basename(args.file)}")
    print(f" Target Subject:  {args.subject}")
    print(f" Mode:            {args.mode}")
    print(f"{'='*60}\n")
    
    print("[1/3] Extracting text and metadata from file...")
    file_info = process_uploaded_file(args.file)
    print(f"  -> Extracted {file_info['word_count']:,} words across ~{file_info['total_pages']} pages.")
    
    print("\n[2/3] Extracting domain entities, definitions, and relationships...")
    result = extract_entities_from_document(
        text=file_info['full_text'],
        subject=args.subject,
        mode=args.mode,
        max_entities=args.max_entities
    )
    
    entities = result.get("entities", [])
    relations = result.get("relations", [])
    ontology = result.get("ontology", {})
    
    print(f"  -> Extracted {len(entities)} entities across {len(ontology)} categories.")
    print(f"  -> Discovered {len(relations)} relationship triples.")
    
    print("\n[3/3] Saving outputs...")
    base_name = os.path.splitext(os.path.basename(args.file))[0]
    
    json_path = os.path.join(args.output_dir, f"{base_name}_entities.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"  [SAVED] JSON knowledge graph: {json_path}")
    
    if entities:
        csv_path = os.path.join(args.output_dir, f"{base_name}_entities.csv")
        pd.DataFrame(entities).to_csv(csv_path, index=False)
        print(f"  [SAVED] CSV entity dictionary: {csv_path}")
        
    html_path = os.path.join(args.output_dir, f"{base_name}_viewer.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_interactive_graph_html(result))
    print(f"  [SAVED] Interactive HTML viewer: {html_path}")
    
    print("\n" + "="*60)
    print(" Extraction complete! Open the HTML file in any browser to explore the graph.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

