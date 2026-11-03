# Universal Subject Ontology Builder

An automated Extract, Transform, Validate, and Load (ETVL) pipeline that ingests raw textbooks and uses multiple LLMs (Gemini 3.5/3.1 Pro & DeepSeek) to autonomously construct a highly structured, interactive Knowledge Graph and Data Dictionary for **any** subject.

---

## ⚠️ CRITICAL FIRST STEP: Human Action Required

Before you do anything else, **you must prep your environment**. 

This pipeline does not search the web. It builds its intelligence strictly from the expert materials you provide and requires API access to function.

1. **Set Up Your Folders:** Create a folder named `raw_material` in the root directory and drop your PDF textbooks inside. *(Note: Ensure the PDFs are high-quality technical books that contain both an embedded Table of Contents (TOC) and a structured Index at the back).*

2. **Configure Your `.env` File:** Create a `.env` file in the root directory and add your API keys and your **target subject** so the pipeline knows what to focus on:
   ```env
   GEMINI_API_KEY="your_google_gemini_api_key_here"
   OPENROUTER_API_KEY="your_openrouter_api_key_here"
   TARGET_SUBJECT="Data Engineering and Applied Data Science"
   ```

3. **Sweep the Floor (If running a NEW subject):** If you have previously run this pipeline and are switching to a brand new subject, you **must** clear the staging areas to prevent data contamination. Delete the `processed_text/` and `raw_indexes/` folders entirely, and delete all generated `.json` and `.csv` files from your root directory before hitting run.

---

## 🌟 Features

* **100% Subject-Agnostic:** Want to build an ontology for Quantum Physics? Oil & Gas Engineering? Artificial Intelligence? Just change one variable in your `.env` file, and the LLMs will dynamically adapt their personas and filtering logic.
* **Dual-Extraction Engine:** Extracts the high-level theoretical architecture from PDF Tables of Contents, and the boots-on-the-ground granular terminology from PDF Indexes.
* **Multi-Agent Collaboration:** Leverages **DeepSeek** for aggressive, high-volume data extraction and semantic filtering, while utilizing **Gemini 3.1 Pro / 3.5 Flash** for structural merging, taxonomy design, and expert definition generation.
* **Automated Master Runner:** A single `00.0_run_master_pipeline.py` script orchestrates all 10 steps sequentially, with built-in error handling and safe early-exits.
* **Interactive HTML Output:** Converts the final massive JSON Knowledge Graph into a clean, collapsible, and interactive HTML web viewer.

---

## ⚙️ Prerequisites

### Install Dependencies
You will need Python 3.8+ and the following libraries:
```bash
pip install PyMuPDF python-dotenv openai google-genai
```

---

## 🚀 How to Run

Once your PDFs are in the `raw_material/` folder and your `.env` file is configured, simply run the master pipeline script:

```bash
python 00.0_run_master_pipeline.py
```
Sit back and watch the terminal. The orchestrator will automatically execute the 10-step pipeline.

---

## 🧠 Pipeline Architecture (The 10 Steps)

The pipeline is entirely decoupled, meaning ingestion scripts never talk directly to the LLM scripts, preventing memory leaks and allowing for safe restarts.

1. **`01.0_scan_toc.py`**: Scans the `raw_material/` PDFs and extracts the hierarchical Table of Contents into JSON.
2. **`02.0_starter_ontology.py`**: Gemini and DeepSeek collaborate to build a high-level "Skeleton Ontology" based purely on the textbook TOCs.
3. **`03.0_pdf_to_text_conversion.py`**: Mechanically rips the raw text from every page of the PDFs.
4. **`04.0_extract_raw_indexes.py`**: Isolates and extracts the raw Index pages from the back of the textbooks.
5. **`05.0_expert_term_extraction.py`**: DeepSeek processes the raw index text, aggressively filtering out generic words and keeping only elite, subject-specific technical phrases.
6. **`06.0_index_keyword_density.py`**: A local Python script calculates N-gram density and frequencies to cross-validate term importance.
7. **`07.0_data_dictionary_creation.py`**: Gemini evaluates the surviving terms, drops anything below a 50% subject-relevance threshold, and writes a sharp, 2-sentence technical definition for the survivors.
8. **`08.0_index_ontology_builder.py`**: Gemini acts as an Information Architect, clustering the granular index terms into their own "Peer Taxonomy".
9. **`09.0_ontology_merger.py`**: Gemini 3.1 Pro executes a "Master Merge", intelligently folding the granular index taxonomy (`08.0`) into the high-level theoretical TOC skeleton (`02.0`), deduplicating terms along the way.
10. **`10.0_html_ontology_viewer.py`**: Converts the final JSON graph into a highly readable, interactive HTML web page.

---

## 📂 Final Outputs

After a successful run, your primary outputs will be located in the root directory:
* `09.0_unified_master_ontology.json`: The complete machine-readable Knowledge Graph.
* `10.0_html_ontology_viewer.html`: The human-readable, click-to-expand data dictionary. Double-click this file to open it in any web browser!
