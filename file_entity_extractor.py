"""
file_entity_extractor.py
Autonomous entity and ontology extraction engine from documents.
Supports:
1. LLM-powered extraction (Gemini 2.5/3.5 Flash or DeepSeek via OpenRouter)
2. Robust local statistical & pattern-based NLP extraction (100% offline, zero-API fallback)
"""

import os
import re
import json
import csv
from collections import Counter
from typing import Dict, Any, List, Optional

STOP_WORDS = set([
    "the", "and", "to", "of", "a", "in", "that", "is", "for", "it", "with", "as", 
    "on", "are", "be", "this", "by", "an", "or", "at", "from", "which", "but", 
    "not", "we", "can", "use", "using", "used", "via", "based", "their", "its",
    "how", "when", "out", "then", "into", "through", "very", "much", "many", "most",
    "also", "such", "these", "there", "has", "have", "had", "been", "will", "would",
    "could", "should", "each", "all", "any", "both", "more", "other", "about", "above",
    "after", "again", "against", "between", "during", "under", "where", "why", "while"
])

def extract_acronym_definitions(text: str) -> Dict[str, str]:
    """Finds acronyms defined in parentheses, e.g. Natural Language Processing (NLP)."""
    pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,5})\s*\(([A-Z]{2,10})\)'
    matches = re.findall(pattern, text)
    acronym_map = {}
    for expansion, acronym in matches:
        acronym_map[acronym] = expansion.strip()
        acronym_map[expansion.strip()] = f"Also known as {acronym}."
    return acronym_map

def extract_sentences_with_term(text: str, term: str) -> str:
    """Finds the best sentence defining or describing the term."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    term_lower = term.lower()
    
    definition_markers = ["is a", "is an", "is the", "refers to", "defined as", "consists of", "represents", "used for", "enables"]
    
    best_def = ""
    for s in sentences:
        s_clean = s.strip().replace("\n", " ")
        if len(s_clean) < 25 or len(s_clean) > 300:
            continue
        if re.search(rf'\b{re.escape(term_lower)}\b', s_clean.lower()):
            for marker in definition_markers:
                if marker in s_clean.lower():
                    return s_clean
            if not best_def:
                best_def = s_clean
                
    return best_def or f"Key entity extracted from the document in the context of {term}."

def local_nlp_entity_extraction(text: str, subject: str = "General", max_entities: int = 60) -> Dict[str, Any]:
    """
    100% offline, deterministic entity extraction engine.
    Extracts high-value multi-word phrases, capitalized technical entities, and acronyms.
    """
    acronyms = extract_acronym_definitions(text)
    
    capitalized_phrases = re.findall(r'\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){1,4}\b', text)
    
    words = re.findall(r'\b[a-zA-Z0-9\-_]{3,}\b', text.lower())
    clean_words = [w for w in words if w not in STOP_WORDS and not w.isdigit()]
    
    bigrams = [f"{clean_words[i]} {clean_words[i+1]}" for i in range(len(clean_words) - 1)]
    trigrams = [f"{clean_words[i]} {clean_words[i+1]} {clean_words[i+2]}" for i in range(len(clean_words) - 2)]
    
    cap_counts = Counter(capitalized_phrases)
    bigram_counts = Counter(bigrams)
    trigram_counts = Counter(trigrams)
    
    candidates = {}
    
    for phrase, count in cap_counts.items():
        p_clean = phrase.strip()
        if len(p_clean) > 4 and count >= 1 and not p_clean.lower().startswith(("the ", "this ", "these ")):
            candidates[p_clean] = count * 3
            
    for phrase, count in bigram_counts.most_common(100):
        title_p = phrase.title()
        if count >= 2:
            candidates[title_p] = candidates.get(title_p, 0) + count * 2
            
    for phrase, count in trigram_counts.most_common(80):
        title_p = phrase.title()
        if count >= 2:
            candidates[title_p] = candidates.get(title_p, 0) + count * 2.5
            
    for acr in acronyms.keys():
        if acr.isupper() and len(acr) >= 2:
            candidates[acr] = candidates.get(acr, 0) + 15

    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    
    entities = []
    seen_names = set()
    
    def classify_entity(name: str) -> str:
        name_lower = name.lower()
        if any(w in name_lower for w in ["algorithm", "method", "technique", "regression", "descent", "clustering", "propagation"]):
            return "Method / Algorithm"
        elif any(w in name_lower for w in ["system", "framework", "platform", "server", "database", "api", "software", "tool", "library", "spark", "sql", "python"]):
            return "Technology / Tool"
        elif any(w in name_lower for w in ["rate", "error", "loss", "accuracy", "score", "precision", "recall", "f1", "index", "metric", "density"]):
            return "Metric / Formula"
        elif any(w in name_lower for w in ["model", "network", "theory", "architecture", "structure", "layer", "space", "representation"]):
            return "Architecture / Model"
        elif any(w in name_lower for w in ["dataset", "data", "corpus", "feature", "vector", "matrix", "tensor", "token"]):
            return "Data / Representation"
        else:
            return "Core Concept"

    for name, score in sorted_candidates:
        clean_name = name.strip()
        lower = clean_name.lower()
        if lower in seen_names or len(clean_name) < 3:
            continue
        if any(lower in s for s in seen_names if len(s) > len(lower) + 3):
            continue
            
        seen_names.add(lower)
        
        definition = acronyms.get(clean_name, "")
        if not definition:
            definition = extract_sentences_with_term(text, clean_name)
            
        entity_type = classify_entity(clean_name)
        
        entities.append({
            "name": clean_name,
            "type": entity_type,
            "frequency": int(score),
            "definition": definition,
            "confidence": 0.85
        })
        
        if len(entities) >= max_entities:
            break

    relations = extract_heuristic_relations(text, [e["name"] for e in entities])
    
    categories = {}
    for e in entities:
        cat = e["type"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(e["name"])

    return {
        "engine": "Local Pattern & Frequency NLP",
        "subject": subject,
        "total_entities": len(entities),
        "entities": entities,
        "relations": relations,
        "ontology": categories
    }

def extract_heuristic_relations(text: str, entity_names: List[str]) -> List[Dict[str, str]]:
    """Discovers relationships between extracted entities based on syntactic co-occurrence patterns."""
    relations = []
    entity_set = {e.lower(): e for e in entity_names}
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    relation_patterns = [
        (r'\buses\b|\butilizes\b|\bemploys\b', "uses"),
        (r'\bis a type of\b|\bis a form of\b|\bis a variant of\b', "is a type of"),
        (r'\bconsists of\b|\bcontains\b|\bincludes\b', "contains"),
        (r'\bproduces\b|\bgenerates\b|\boutputs\b', "produces"),
        (r'\btrains on\b|\btrained with\b|\blearns from\b', "trains on"),
        (r'\bdepends on\b|\brequires\b|\bneeds\b', "depends on"),
        (r'\bapplied to\b|\bdesigned for\b', "applied to")
    ]
    
    seen_triples = set()
    
    for s in sentences:
        s_lower = s.lower()
        matched_entities = [orig for low, orig in entity_set.items() if low in s_lower]
        if len(matched_entities) >= 2:
            for i in range(len(matched_entities)):
                for j in range(i + 1, min(len(matched_entities), i + 3)):
                    e1 = matched_entities[i]
                    e2 = matched_entities[j]
                    
                    found_rel = "related to"
                    for pattern, rel_name in relation_patterns:
                        if re.search(pattern, s_lower):
                            found_rel = rel_name
                            break
                            
                    triple_key = (e1, found_rel, e2)
                    if triple_key not in seen_triples and len(relations) < 40:
                        seen_triples.add(triple_key)
                        relations.append({
                            "source": e1,
                            "relation": found_rel,
                            "target": e2
                        })
    return relations

def llm_entity_extraction_gemini(text: str, subject: str = "General", max_entities: int = 60, api_key: str = "") -> Optional[Dict[str, Any]]:
    """Uses Google Gemini API to extract high-accuracy technical entities and relationships."""
    from google import genai
    from google.genai import types
    
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return None
        
    client = genai.Client(api_key=key)
    sample_text = text[:35000] if len(text) > 35000 else text
    
    prompt = f"""
    You are an expert Ontology Engineer and Principal Knowledge Architect.
    Analyze the provided document text focusing on the target subject: "{subject}".
    
    Extract up to {max_entities} core entities and concepts.
    
    Return a strictly valid JSON object with:
    1. "entities": List of objects with:
       - "name": Formal entity name
       - "type": One of ["Core Concept", "Method / Algorithm", "Technology / Tool", "Architecture / Model", "Metric / Formula", "Data / Representation", "Organization"]
       - "definition": Clear, precise 2-sentence technical definition based on document context
       - "confidence": Float between 0.0 and 1.0
    2. "relations": List of knowledge graph triples:
       - "source": Entity A
       - "relation": Short predicate (e.g., "uses", "type of", "produces", "depends on")
       - "target": Entity B
    3. "ontology": Object mapping top-level Category -> List of Entity Names
    
    DOCUMENT TEXT:
    {sample_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        data = json.loads(response.text)
        data["engine"] = "Google Gemini 2.5 Flash"
        data["subject"] = subject
        data["total_entities"] = len(data.get("entities", []))
        return data
    except Exception as e:
        print(f"[Gemini API Warning] {e}. Falling back to local NLP extraction.")
        return None

def llm_entity_extraction_openrouter(text: str, subject: str = "General", max_entities: int = 60, api_key: str = "") -> Optional[Dict[str, Any]]:
    """Uses OpenRouter / DeepSeek to extract entities."""
    from openai import OpenAI
    
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        return None
        
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
    sample_text = text[:30000] if len(text) > 30000 else text
    
    prompt = f"""
    You are a Knowledge Graph Architect. Analyze this text for subject "{subject}".
    Extract up to {max_entities} entities and their relationships.
    Output ONLY a valid JSON object matching:
    {{
      "entities": [
        {{"name": "...", "type": "Core Concept | Method / Algorithm | Technology / Tool | Metric / Formula", "definition": "...", "confidence": 0.95}}
      ],
      "relations": [
        {{"source": "...", "relation": "...", "target": "..."}}
      ],
      "ontology": {{
        "Category Name": ["Entity 1", "Entity 2"]
      }}
    }}
    
    TEXT:
    {sample_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        data = json.loads(content)
        data["engine"] = "DeepSeek (OpenRouter)"
        data["subject"] = subject
        data["total_entities"] = len(data.get("entities", []))
        return data
    except Exception as e:
        print(f"[OpenRouter API Warning] {e}. Falling back to local NLP extraction.")
        return None

def extract_entities_from_document(
    text: str, 
    subject: str = "Auto-detect", 
    mode: str = "auto",
    max_entities: int = 60,
    api_key_gemini: str = "",
    api_key_openrouter: str = ""
) -> Dict[str, Any]:
    """Unified extraction pipeline with automatic fallback."""
    if not text.strip():
        return {
            "engine": "None",
            "subject": subject,
            "total_entities": 0,
            "entities": [],
            "relations": [],
            "ontology": {}
        }
        
    if subject in ("Auto-detect", "General", ""):
        words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()) if w not in STOP_WORDS]
        top_words = [w.title() for w, _ in Counter(words).most_common(3)]
        subject = " / ".join(top_words) if top_words else "General Subject"
        
    if mode in ("auto", "gemini"):
        res = llm_entity_extraction_gemini(text, subject, max_entities, api_key_gemini)
        if res:
            return res
            
    if mode in ("auto", "openrouter"):
        res = llm_entity_extraction_openrouter(text, subject, max_entities, api_key_openrouter)
        if res:
            return res
            
    return local_nlp_entity_extraction(text, subject, max_entities)

def generate_interactive_graph_html(result: Dict[str, Any]) -> str:
    """Generates an embedded interactive visual network graph with a high-end UI."""
    entities = result.get("entities", [])
    relations = result.get("relations", [])
    subject = result.get("subject", "Knowledge Graph")
    
    color_map = {
        "Core Concept": {"bg": "#38bdf8", "border": "#0284c7"},
        "Method / Algorithm": {"bg": "#f43f5e", "border": "#be123c"},
        "Technology / Tool": {"bg": "#10b981", "border": "#059669"},
        "Architecture / Model": {"bg": "#a855f7", "border": "#7e22ce"},
        "Metric / Formula": {"bg": "#f59e0b", "border": "#d97706"},
        "Data / Representation": {"bg": "#06b6d4", "border": "#0891b2"},
        "Organization": {"bg": "#64748b", "border": "#475569"}
    }
    
    nodes = []
    node_id_map = {}
    
    for idx, e in enumerate(entities):
        nid = idx + 1
        name = e["name"]
        etype = e.get("type", "Core Concept")
        definition = e.get("definition", "").replace('"', '&quot;').replace("'", "&#39;")
        c = color_map.get(etype, {"bg": "#38bdf8", "border": "#0284c7"})
        
        node_id_map[name] = nid
        nodes.append({
            "id": nid,
            "label": name,
            "title": f"<div style='font-family:sans-serif;padding:6px;max-width:240px;line-height:1.4;'><span style='color:{c['bg']};font-weight:700;font-size:13px;'>{name}</span><br><span style='font-size:10px;text-transform:uppercase;color:#94a3b8;letter-spacing:0.5px;'>{etype}</span><p style='margin:6px 0 0;font-size:11px;color:#e2e8f0;'>{definition}</p></div>",
            "color": {
                "background": c["bg"],
                "border": c["border"],
                "highlight": {"background": "#ffffff", "border": c["bg"]}
            },
            "group": etype
        })
        
    edges = []
    for r in relations:
        src = r.get("source")
        tgt = r.get("target")
        rel = r.get("relation", "connected")
        if src in node_id_map and tgt in node_id_map:
            edges.append({
                "from": node_id_map[src],
                "to": node_id_map[tgt],
                "label": rel,
                "arrows": {"to": {"enabled": True, "scaleFactor": 0.6}}
            })
            
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      margin: 0;
      padding: 12px;
      background: #090d16;
      color: #f1f5f9;
      overflow: hidden;
    }}
    .hud {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 10px;
      padding: 10px 14px;
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      backdrop-filter: blur(12px);
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 500;
      background: rgba(255, 255, 255, 0.04);
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .legend-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    .controls {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .btn {{
      background: #1e293b;
      color: #cbd5e1;
      border: 1px solid #334155;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .btn:hover {{
      background: #334155;
      color: #ffffff;
      border-color: #475569;
    }}
    #network {{
      width: 100%;
      height: 560px;
      background: radial-gradient(circle at 50% 50%, #111827 0%, #090d16 100%);
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
    }}
    div.vis-tooltip {{
      position: absolute;
      background: rgba(15, 23, 42, 0.95) !important;
      border: 1px solid rgba(56, 189, 248, 0.3) !important;
      border-radius: 10px !important;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5) !important;
      backdrop-filter: blur(8px) !important;
      padding: 4px !important;
    }}
  </style>
</head>
<body>
  <div class="hud">
    <div class="legend">
      {''.join([f'<div class="legend-item"><div class="legend-dot" style="background:{c["bg"]};box-shadow:0 0 8px {c["bg"]}66;"></div><span>{t}</span></div>' for t, c in color_map.items()])}
    </div>
    <div class="controls">
      <button class="btn" onclick="network.fit({{animation: true}})">Fit Graph</button>
      <button class="btn" onclick="togglePhysics()">Toggle Physics</button>
    </div>
  </div>
  <div id="network"></div>
  <script>
    const nodes = new vis.DataSet({nodes_json});
    const edges = new vis.DataSet({edges_json});
    const container = document.getElementById('network');
    const data = {{ nodes: nodes, edges: edges }};
    const options = {{
      nodes: {{
        shape: 'dot',
        size: 18,
        font: {{ size: 12, face: 'Plus Jakarta Sans', color: '#f8fafc', strokeWidth: 2, strokeColor: '#090d16' }},
        borderWidth: 2,
        shadow: {{ enabled: true, color: 'rgba(0,0,0,0.4)', size: 8, x: 0, y: 3 }}
      }},
      edges: {{
        font: {{ size: 10, face: 'Plus Jakarta Sans', align: 'middle', color: '#94a3b8', strokeWidth: 0 }},
        color: {{ color: 'rgba(100, 116, 139, 0.4)', highlight: '#38bdf8', hover: '#38bdf8' }},
        smooth: {{ type: 'curvedCW', roundness: 0.15 }},
        arrows: {{ to: {{ enabled: true, scaleFactor: 0.6 }} }}
      }},
      physics: {{
        stabilization: {{ iterations: 120 }},
        barnesHut: {{ gravitationalConstant: -3500, centralGravity: 0.3, springLength: 110, springConstant: 0.04, damping: 0.09 }}
      }},
      interaction: {{ hover: true, tooltipDelay: 80, zoomView: true, dragView: true }}
    }};
    const network = new vis.Network(container, data, options);
    let physicsEnabled = true;
    function togglePhysics() {{
      physicsEnabled = !physicsEnabled;
      network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
    }}
  </script>
</body>
</html>"""
    return html
