import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Universal Subject Variable
TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Universal")

# Define the exact execution order based on your cleaned directory structure
PIPELINE_SCRIPTS = [
    "01.0_scan_toc.py",
    "02.0_starter_ontology.py",
    "03.0_pdf_to_text_conversion.py",
    "04.0_extract_raw_indexes.py",
    "05.0_expert_term_extraction.py",
    "06.0_index_keyword_density.py",
    "07.0_data_dictionary_creation.py",
    "08.0_index_ontology_builder.py",
    "09.0_ontology_merger.py",
    "10.0_html_ontology_viewer.py"
]

def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("="*65)
    print(f" INITIATING {TARGET_SUBJECT.upper()} KNOWLEDGE GRAPH PIPELINE")
    print("="*65)
    
    for script_name in PIPELINE_SCRIPTS:
        script_path = os.path.join(base_dir, script_name)
        
        # Pre-execution check to ensure the file exists
        if not os.path.exists(script_path):
            print(f"\n[CRITICAL ERROR] Could not find '{script_name}' in {base_dir}")
            print("Pipeline HALTED.")
            sys.exit(1)
            
        print(f"\n{'='*40}")
        print(f" Executing: {script_name}")
        print(f"{'='*40}\n")
        
        try:
            # sys.executable ensures we use the exact same Python environment running this script
            # check=True forces it to throw an exception if the sub-script crashes
            subprocess.run([sys.executable, script_path], check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"\n[CRITICAL ERROR] Pipeline crashed during '{script_name}'.")
            print(f"Exit code: {e.returncode}")
            print("Pipeline HALTED. Please fix the error above before re-running.")
            sys.exit(1)
        except KeyboardInterrupt:
            print(f"\n[WARNING] Pipeline manually interrupted by user during '{script_name}'.")
            sys.exit(1)
            
    print("\n" + "="*65)
    print(f" MASTER {TARGET_SUBJECT.upper()} PIPELINE COMPLETE")
    print(" All scripts executed successfully. Your HTML Viewer is ready.")
    print("="*65)

if __name__ == "__main__":
    run_pipeline()