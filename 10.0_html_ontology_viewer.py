import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Universal Subject Variable
TARGET_SUBJECT = os.getenv("TARGET_SUBJECT", "Subject")

# Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "09.0_unified_master_ontology.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "10.0_html_ontology_viewer.html")

def generate_html_viewer():
    if not os.path.exists(INPUT_JSON):
        print(f"[ERROR] Could not find '{INPUT_JSON}'.")
        return

    # Load the unified ontology
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        ontology_data = json.load(f)

    # Begin HTML structure with dynamic subject injection
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{TARGET_SUBJECT} Ontology</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background-color: #f4f7f6; 
                color: #333; 
                margin: 0; 
                padding: 40px 20px; 
            }}
            .header {{ 
                text-align: center; 
                padding: 40px 20px; 
                background-color: #2c3e50; 
                color: white; 
                border-radius: 8px; 
                margin-bottom: 30px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            }}
            .header h1 {{ margin: 0; font-size: 2.5em; letter-spacing: 1px; text-transform: capitalize; }}
            .header p {{ font-size: 1.2em; color: #ecf0f1; margin-top: 10px; }}
            .container {{ max-width: 1000px; margin: auto; }}
            
            /* Domain Level Buttons */
            .domain-btn {{ 
                background-color: #34495e; 
                color: white; 
                cursor: pointer; 
                padding: 18px; 
                width: 100%; 
                border: none; 
                text-align: left; 
                outline: none; 
                font-size: 18px; 
                border-radius: 5px; 
                margin-top: 10px; 
                transition: 0.3s; 
                font-weight: bold; 
            }}
            .domain-btn:hover {{ background-color: #2c3e50; }}
            .domain-content {{ 
                padding: 0 18px; 
                display: none; 
                background-color: transparent; 
                margin-bottom: 10px; 
            }}
            
            /* Sub-domain Level Buttons */
            .subdomain-btn {{ 
                background-color: #ffffff; 
                color: #2c3e50; 
                cursor: pointer; 
                padding: 15px; 
                width: 100%; 
                border: 1px solid #bdc3c7; 
                text-align: left; 
                outline: none; 
                font-size: 16px; 
                border-radius: 5px; 
                margin-top: 8px; 
                transition: 0.3s; 
                font-weight: 600; 
            }}
            .subdomain-btn:hover {{ background-color: #ecf0f1; }}
            .subdomain-content {{ 
                padding: 15px 0; 
                display: none; 
                background-color: transparent; 
                margin-bottom: 8px; 
            }}
            
            /* Term Cards */
            .term-card {{ 
                background: white; 
                padding: 18px; 
                margin-bottom: 10px; 
                border-radius: 5px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
                border-left: 4px solid #3498db; 
            }}
            .term-title {{ 
                margin: 0 0 8px 0; 
                font-size: 16px; 
                color: #2980b9; 
                text-transform: capitalize;
            }}
            .term-def {{ margin: 0; font-size: 14px; line-height: 1.6; color: #555; }}
            
            /* Accordion Icons */
            .icon {{ 
                float: right; 
                font-weight: bold; 
                transition: transform 0.3s ease; 
            }}
            .active .icon {{ transform: rotate(45deg); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{TARGET_SUBJECT} Ontology</h1>
                <p>Interactive Data Dictionary</p>
            </div>
    """

    # Dynamically inject JSON data into the HTML structure
    for domain, subdomains in ontology_data.items():
        html += f'        <button class="domain-btn accordion" data-level="1">{domain} <span class="icon">+</span></button>\n'
        html += '        <div class="domain-content">\n'
        for subdomain, terms in subdomains.items():
            html += f'            <button class="subdomain-btn accordion" data-level="2">{subdomain} <span class="icon">+</span></button>\n'
            html += '            <div class="subdomain-content">\n'
            for term, definition in terms.items():
                html += f'''                <div class="term-card">
                        <h4 class="term-title">{term}</h4>
                        <p class="term-def">{definition}</p>
                    </div>\n'''
            html += '            </div>\n'
        html += '        </div>\n'

    # Close HTML and add JavaScript logic
    html += """
        </div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {
                var accordions = document.querySelectorAll(".accordion");

                accordions.forEach(function(acc) {
                    acc.addEventListener("click", function() {
                        var level = this.getAttribute("data-level");
                        var content = this.nextElementSibling;
                        var isActive = this.classList.contains("active");

                        // Close all accordions at the same level in the same parent container
                        var siblings = level == "1" ? 
                            document.querySelectorAll('.domain-btn') : 
                            this.parentElement.querySelectorAll('.subdomain-btn');
                        
                        siblings.forEach(function(sib) {
                            sib.classList.remove("active");
                            sib.nextElementSibling.style.display = "none";
                            sib.querySelector(".icon").innerText = "+";
                        });

                        // If it wasn't active before, open it now
                        if (!isActive) {
                            this.classList.add("active");
                            content.style.display = "block";
                            this.querySelector(".icon").innerText = "\\u00d7"; // Unicode for 'x'
                        }
                    });
                });
            });
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as out_f:
        out_f.write(html)

    print(f"\n--- HTML Generation Complete ---")
    print(f"Interactive Viewer saved to: {OUTPUT_HTML}")

if __name__ == "__main__":
    generate_html_viewer()