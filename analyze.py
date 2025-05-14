import os
import ollama
import json
import datetime
import re
from pdfreader import SimplePDFViewer
import markdown2
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
# from playwright.sync_api import sync_playwright # Playwright might be needed if website scraping is still a requirement for pitches, let's keep it commented for now.

# --- Configuration ---
FOLDER_A_DEFAULT = "input"  # New pitches
FOLDER_B_DEFAULT = "portfolio"  # Portfolio companies
FOLDER_C_DEFAULT = "reports"  # Output reports

# Toggle for original analysis functions (initially False as requested)
RUN_ORIGINAL_ANALYSIS = False

# --- Helper Functions (Adapted from user's main.py and new requirements) ---

def get_document_content(file_path):
    """Get content of a document (.txt or .pdf)."""
    try:
        if file_path.lower().endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.lower().endswith(".pdf"):
            with open(file_path, 'rb') as f:
                viewer = SimplePDFViewer(f)
                text_content = ""
                for canvas in viewer:
                    viewer.render()
                    text_content += " ".join(viewer.canvas.strings) + "\n"
                return text_content
        else:
            print(f"Unsupported file type: {file_path}")
            return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def extract_text_from_content(content):
    """Extract and clean text from the document content."""
    try:
        if not content:
            return ""
        extracted_text = content.replace('\n', ' ')
        extracted_text = extracted_text.lower().replace('—', ', ').replace('---', '.').replace('--', '-')
        # Add more cleaning steps if necessary
        return extracted_text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def get_company_name_from_filename(filename):
    """Extracts company name from filename (removes extension)."""
    return os.path.splitext(filename)[0]

def extract_cofounder_names(text_content, company_name_a):
    """Extracts cofounder names using the Ollama LLM or returns a placeholder."""
    prompt = f"""
    You are an expert in extracting key information from text. Your task is to identify the names of cofounders or key team members from the provided text. If no cofounder names are explicitly mentioned, return 'the Team at {company_name_a}'.

    **Text Content:**
    {text_content}

    **Output Format:**
    - If cofounder names are found: "Cofounders: [Name1, Name2, ...]"
    - If no names are found: "Cofounders: the Team at {company_name_a}"
    """

    try:
        response = ollama.chat(
            model="qwen3:0.6b", # using the smallest qwen parameter model for speed
            messages=[
                {"role": "system", "content": "You are an expert in extracting cofounder names from text."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response['message']['content']
        if "Cofounders:" in result:
            return result.replace("Cofounders:", "").strip()
        else:
            return f"the Team at {company_name_a}"
    except Exception as e:
        print(f"Error during cofounder name extraction using LLM: {e}")
        return f"the Team at {company_name_a}"  # Fallback placeholder

# --- Core Synergy Analysis Function ---
def analyze_synergy(pitch_company_name, pitch_content, portfolio_company_name, portfolio_content, synergy_criteria_text):
    """Analyzes synergy between a pitch and a portfolio company using LLM."""
    print(f"Analyzing synergy between {pitch_company_name} and {portfolio_company_name}...")
    
    prompt = f"""
    You are a highly critical VC Analyst. Your primary task is to identify and rigorously evaluate *genuinely relevant and actionable* potential synergies between a new pitch (Folder A company) and an existing portfolio company (Folder B company). Your analysis must be grounded in the core business activities and strategic goals of both entities. Avoid superficial or impractical suggestions.

    **Portfolio Company (Folder B):** {portfolio_company_name}
    **Portfolio Company Details:** {portfolio_content}

    **New Pitch Company (Folder A):** {pitch_company_name}
    **New Pitch Company Details:** {pitch_content}

    **Synergy Evaluation Framework (Strictly Adhere to This):**
    {synergy_criteria_text}

    **Critical Instructions:**
    1.  **Relevance First:** Based on the detailed descriptions of both companies and the Synergy Evaluation Framework, provide an insightful explanation ONLY for potential synergies that are *highly relevant and strategically sound* for the **Portfolio Company (Folder B)**. Consider if the Folder B company could realistically become a client, partner, etc., of the Folder A company, or vice-versa, in a way that significantly benefits Folder B's objectives.
    2.  **Critical Assessment:** For each *genuinely relevant* synergy identified, assess it meticulously based on ALL the following categories from the framework:
        *   **Synergy Type:** (e.g., Client Relationship, Channel Expansion, Technology Integration, etc. - pick from the provided list in the framework. Be specific.)
        *   **Feasibility:** (How easily can it be executed? Critically assess integration complexity, legal/regulatory hurdles, cultural fit, and resource requirements.)
        *   **Scalability:** (Is this a one-off, limited opportunity, or a repeatable, significant growth lever for Folder B?)
        *   **Defensibility:** (Does the synergy create a *strong, sustainable* competitive advantage or moat for Folder B?)
        *   **Alignment with {portfolio_company_name}'s (Folder B) Goals:** (Does this synergy *directly and significantly* help {portfolio_company_name} achieve its stated KPIs or strategic objectives? Be specific.)
    3.  **Identify Red Flags:** For each proposed synergy, actively look for and clearly state any **Red Flags (False Synergies)** as defined in the framework (e.g., One-Sided Value, High Execution Cost, Strategic Misalignment for Folder B).
    4.  **Overall Synergy Classification (Be Decisive):**
        *   Classify the *overall synergy potential for {portfolio_company_name} (Folder B)* with {pitch_company_name} (Folder A) as: **Immediate Opportunity**, **Strategic Long-Term Play**, or **Low Priority**.
        *   **If no significant, actionable, or relevant synergy is identified after critical evaluation, or if red flags outweigh potential benefits for Folder B, you MUST classify it as 'Low Priority' and explicitly state 'No significant actionable synergy identified at this time.' or a similar clear statement indicating a lack of strong fit.**
    5.  **Explanation for Introduction (Only if a viable synergy exists):**
        *   If, and ONLY IF, you identify an 'Immediate Opportunity' or a strong 'Strategic Long-Term Play' with clear benefits for {portfolio_company_name} (Folder B), provide a concise **Explanation for Introduction**. This explanation will be used in an email. It must be compelling, specific, and clearly state the *single most promising and relevant reason* for the introduction from {portfolio_company_name}'s perspective.
        *   **If the classification is 'Low Priority' or no significant synergy is found, state 'No introduction recommended at this time due to lack of strong, actionable synergy.'**

    **Output Format (Strictly Adhere to This):**
    Please structure your response clearly. If no relevant synergy is found, state it clearly under the Overall Synergy Classification and for the Explanation for Introduction.

    **Synergy Analysis for {pitch_company_name} with {portfolio_company_name}:**

    **1. Potential Synergy: [Describe the *most relevant* synergy, e.g., {portfolio_company_name} as a Client for {pitch_company_name}]** (Only if a relevant synergy exists)
       *   **Synergy Type:** [e.g., Client Relationship]
       *   **Feasibility:** [Your critical assessment]
       *   **Scalability:** [Your critical assessment]
       *   **Defensibility:** [Your critical assessment]
       *   **Alignment with Goals ({portfolio_company_name}):** [Your critical assessment related to Folder B]
       *   **Red Flags:** [e.g., None identified / or describe red flag(s) clearly]

    **(Optional) 2. Potential Synergy: [Describe another *highly relevant* synergy, if any]**
       *   ...

    **Overall Synergy Classification:** [Immediate Opportunity / Strategic Long-Term Play / Low Priority - If Low Priority due to no strong synergy, add: 'No significant actionable synergy identified at this time.']

    **Explanation for Introduction:** [Your concise explanation for the email introduction, or 'No introduction recommended at this time due to lack of strong, actionable synergy.']
    """

    try:
        response = ollama.chat(
            model="gemma3:12b-it-qat", # As per user's existing setup
            messages=[
                {"role": "system", "content": "You are a VC Analyst specializing in synergy identification between startups."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        print(f"Error during LLM synergy analysis: {e}")
        return "Error: Could not perform synergy analysis."

# --- Report Generation ---
def generate_report_for_portfolio_company(portfolio_company_name, portfolio_cofounders, synergy_analyses, output_folder_c):
    """Generates a single PDF report document for a portfolio company, containing all its synergy analyses."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename_pdf = os.path.join(output_folder_c, f"{portfolio_company_name}_Synergy_Report_{timestamp}.pdf")
    
    # 1. Assemble Markdown content (as before)
    report_content_md = f"# Synergy Report for {portfolio_company_name}\n\n"
    report_content_md += f"**Date Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_content_md += f"This report outlines potential synergies between {portfolio_company_name} and various new pitches evaluated.\n\n"
    report_content_md += "---\n"

    if not synergy_analyses:
        report_content_md += "No potential synergies identified with the evaluated pitches.\n"
    else:
        for analysis in synergy_analyses:
            pitch_company_name = analysis['pitch_company_name']
            pitch_cofounders = analysis['pitch_cofounders']
            introduction_explanation = analysis['introduction_explanation'] # This should be extracted from LLM output
            detailed_analysis = analysis['detailed_analysis'] # Full LLM output for this pair

            report_content_md += f"## Potential Introduction: {portfolio_company_name} & {pitch_company_name}\n\n"
            report_content_md += f"**To:** {portfolio_cofounders} (Team at {portfolio_company_name})\n"
            report_content_md += f"**From:** [Your Name/VC Firm Name]\n"
            report_content_md += f"**Subject:** Introduction: {portfolio_company_name} & {pitch_company_name}\n\n"
            team_placeholder_greeting = f'the Team at {portfolio_company_name}'
            actual_greeting_recipient = portfolio_cofounders if portfolio_cofounders != team_placeholder_greeting else 'Team'
            report_content_md += f"Hi {actual_greeting_recipient},\n\n"
            report_content_md += f"I hope this email finds you well.\n\n"
            report_content_md += f"I'd like to introduce you to {pitch_cofounders} of {pitch_company_name}. "
            report_content_md += f"{introduction_explanation}\n\n"
            report_content_md += f"I believe there could be a valuable connection here. Please find a more detailed synergy analysis below.\n\n"
            report_content_md += f"Best regards,\n[Your Name]\n\n"
            report_content_md += f"### Detailed Synergy Analysis: {pitch_company_name} with {portfolio_company_name}\n\n"
            # Ensure the detailed_analysis (LLM output) is treated as pre-formatted text if it contains Markdown-like structures
            # or ensure it's clean text that markdown2 can process.
            # For now, assuming detailed_analysis is mostly plain text or simple markdown that will be converted.
            report_content_md += f"{detailed_analysis}\n\n"
            report_content_md += "---\n\n"

    # 2. Convert Markdown to HTML
    html_content = markdown2.markdown(report_content_md, extras=["tables", "fenced-code-blocks", "break-on-newline"])

    # 3. Define CSS for professional formatting
    # Using NotoSansCJK for potential CJK characters as per best practice, and a generic sans-serif fallback.
    css_styles = """
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: "Noto Sans CJK SC", "WenQuanYi Zen Hei", sans-serif;
        line-height: 1.6;
        color: #333;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: "Noto Sans CJK SC", "WenQuanYi Zen Hei", sans-serif;
        color: #111;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        line-height: 1.3;
    }
    h1 {
        font-size: 24pt;
        border-bottom: 2px solid #333;
        padding-bottom: 0.3em;
    }
    h2 {
        font-size: 18pt;
        border-bottom: 1px solid #ccc;
        padding-bottom: 0.2em;
    }
    h3 {
        font-size: 14pt;
    }
    p {
        margin-bottom: 1em;
    }
    strong, b {
        font-weight: bold;
    }
    em, i {
        font-style: italic;
    }
    ul, ol {
        margin-left: 20px;
        margin-bottom: 1em;
    }
    li {
        margin-bottom: 0.5em;
    }
    hr {
        border: 0;
        height: 1px;
        background: #ccc;
        margin: 2em 0;
    }
    pre {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
        white-space: pre-wrap;       /* CSS3 */
        white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
        white-space: -pre-wrap;      /* Opera 4-6 */
        white-space: -o-pre-wrap;    /* Opera 7 */
        word-wrap: break-word;       /* Internet Explorer 5.5+ */
    }
    code {
        font-family: monospace;
        background-color: #f0f0f0;
        padding: 0.2em 0.4em;
        border-radius: 3px;
    }
    """
    font_config = FontConfiguration()
    css = CSS(string=css_styles, font_config=font_config)

    # 4. Generate PDF
    try:
        HTML(string=html_content).write_pdf(report_filename_pdf, stylesheets=[css], font_config=font_config)
        print(f"Synergy PDF report saved to {report_filename_pdf}")
        return report_filename_pdf
    except Exception as e:
        print(f"Error saving PDF report {report_filename_pdf}: {e}")
        # Fallback to saving as MD if PDF fails, or handle error differently
        md_fallback_filename = report_filename_pdf.replace(".pdf", "_fallback.md")
        try:
            with open(md_fallback_filename, 'w', encoding='utf-8') as f:
                f.write("Error generating PDF. Markdown content fallback:\n\n" + report_content_md)
            print(f"PDF generation failed. Markdown fallback saved to {md_fallback_filename}")
        except Exception as e_md:
            print(f"Error saving Markdown fallback: {e_md}")
        return None


# --- Original Analysis Functions (from main.py, with toggle) ---
# These are placeholders and would need advisory_considerations.txt and judging_criteria.txt
# if RUN_ORIGINAL_ANALYSIS is True.

def advisory_potential(text):
    if not RUN_ORIGINAL_ANALYSIS: return "Advisory potential analysis skipped."
    # ... (original code from main.py, ensure 'advisory_considerations.txt' is accessible)
    return "Advisory potential assessed (mock)."

def assess_risk(text):
    if not RUN_ORIGINAL_ANALYSIS: return "Risk assessment skipped."
    """Assess the investibility and risk of the deck."""
    try:
        response = ollama.chat(  
            model="llama3.2:latest",  # Replace with your actual model name
            messages=[
                {"role": "system", "content": "You are a financial analyst assessing risk."},
                {"role": "user", "content": f"Analyze this text extracted from a pdf deck. Return a report on the investibility potential returns: {text}"}
            ]
        )
        return response['message']['content']
    except Exception as e:
        raise ValueError(f"Error in risk assessment: {e}")

def project_scoring(text):
    if not RUN_ORIGINAL_ANALYSIS: return "Project scoring skipped."
    """Score the project based on criteria."""
    try:
        with open('judging_criteria.txt', 'r', encoding='utf-8') as f:
                    scoring = f.read()
        
        response = ollama.chat(  # Corrected to chat.completions.create
            model="llama3.2:latest",  # Replace with your actual model name
            messages=[
                {"role": "system", "content": "You are a expert startup and business judge."},
                {"role": "user", "content": f"assess the startup with their data here {text} based strictly on the following criteria: \n{scoring}\n\n use assumptions if necessary."}
            ]
        )
        return response['message']['content']
    except Exception as e:
        raise ValueError(f"Error in ROI projection: {e}")

def generate_recommendations(text):
    if not RUN_ORIGINAL_ANALYSIS: return "Recommendations generation skipped."
    # ... (original code from main.py)
    return "Recommendations generated (mock)."

def save_original_report_in_directory(report_content, report_type, directory, project_name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"{project_name}_{report_type}_{timestamp}.txt")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"{report_type.capitalize()} report saved to {filename}")
    except Exception as e:
        print(f"Error saving original report {filename}: {e}")

# --- Main Orchestration ---
def main():
    # Configurable folder paths
    folder_a_path = input(f"Enter path for Folder A (new pitches) or press Enter for default '{FOLDER_A_DEFAULT}': ") or FOLDER_A_DEFAULT
    folder_b_path = input(f"Enter path for Folder B (portfolio companies) or press Enter for default '{FOLDER_B_DEFAULT}': ") or FOLDER_B_DEFAULT
    folder_c_path = input(f"Enter path for Folder C (reports) or press Enter for default '{FOLDER_C_DEFAULT}': ") or FOLDER_C_DEFAULT

    # Create output directory if it doesn't exist
    os.makedirs(folder_c_path, exist_ok=True)

    # Load synergy criteria (from pasted_content.txt)
    # This file should be in the same directory as the script or provide a path.
    synergy_criteria_file = "analysis_criteria.txt"
    synergy_criteria_text = ""
    try:
        with open(synergy_criteria_file, 'r', encoding='utf-8') as f:
            synergy_criteria_text = f.read()
    except FileNotFoundError:
        print(f"Error: Synergy criteria file '{synergy_criteria_file}' not found. Please create it.")
        print("This file should contain the content you provided regarding: A. Revenue/Customer Synergies, B. Strategic/Operational Synergies, etc., AND the Feasibility/Scalability/Defensibility/Alignment questions, Red Flags, and Actionable Output classifications.")
        return
    except Exception as e:
        print(f"Error reading synergy criteria file: {e}")
        return

    # 1. Process Portfolio Companies (Folder B)
    portfolio_companies_data = []
    if not os.path.exists(folder_b_path):
        print(f"Error: Folder B '{folder_b_path}' does not exist.")
        return
        
    for filename_b in os.listdir(folder_b_path):
        file_path_b = os.path.join(folder_b_path, filename_b)
        if os.path.isfile(file_path_b) and (filename_b.lower().endswith(".txt") or filename_b.lower().endswith(".pdf")):
            print(f"Processing portfolio company file: {filename_b}")
            company_name_b = get_company_name_from_filename(filename_b)
            raw_content_b = get_document_content(file_path_b)
            if raw_content_b:
                text_content_b = extract_text_from_content(raw_content_b)
                cofounders_b = extract_cofounder_names(text_content_b, company_name_b) # Pass company name for placeholder
                portfolio_companies_data.append({
                    "name": company_name_b,
                    "cofounders": cofounders_b,
                    "content": text_content_b,
                    "original_filename": filename_b
                })
            else:
                print(f"Could not read content for {filename_b}")
        else:
            print(f"Skipping non-txt/pdf file in Folder B: {filename_b}")

    if not portfolio_companies_data:
        print(f"No processable files found in Folder B ('{folder_b_path}').")
        return

    # 2. Process New Pitches (Folder A) and Generate Reports for each Portfolio Company
    if not os.path.exists(folder_a_path):
        print(f"Error: Folder A '{folder_a_path}' does not exist.")
        return

    for portfolio_company in portfolio_companies_data:
        print(f"\n--- Generating Synergy Report for Portfolio Company: {portfolio_company['name']} ---")
        current_portfolio_synergies = []

        for filename_a in os.listdir(folder_a_path):
            file_path_a = os.path.join(folder_a_path, filename_a)
            if os.path.isfile(file_path_a) and (filename_a.lower().endswith(".txt") or filename_a.lower().endswith(".pdf")):
                print(f"  Comparing with new pitch: {filename_a}")
                company_name_a = get_company_name_from_filename(filename_a)
                raw_content_a = get_document_content(file_path_a)
                if raw_content_a:
                    text_content_a = extract_text_from_content(raw_content_a)
                    cofounders_a = extract_cofounder_names(text_content_a, company_name_a)

                    # Perform synergy analysis
                    synergy_analysis_result = analyze_synergy(
                        pitch_company_name=company_name_a,
                        pitch_content=text_content_a,
                        portfolio_company_name=portfolio_company['name'],
                        portfolio_content=portfolio_company['content'],
                        synergy_criteria_text=synergy_criteria_text
                    )
                    
                    # Extract the 'Explanation for Introduction' from the LLM's response.
                    # This requires parsing the LLM output. A more robust way would be to ask LLM for JSON or structured output.
                    # For now, a simple regex or string search.
                    intro_explanation_match = re.search(r"Explanation for Introduction:\s*(.*?)(?:\n\n|\Z)", synergy_analysis_result, re.DOTALL | re.IGNORECASE)
                    intro_explanation = intro_explanation_match.group(1).strip() if intro_explanation_match else "A potential synergy was identified that warrants a discussion."

                    current_portfolio_synergies.append({
                        "pitch_company_name": company_name_a,
                        "pitch_cofounders": cofounders_a,
                        "introduction_explanation": intro_explanation,
                        "detailed_analysis": synergy_analysis_result
                    })

                    # Optionally run original analysis functions if toggled
                    if RUN_ORIGINAL_ANALYSIS:
                        print(f"  Running original analysis for {company_name_a} (related to {portfolio_company['name']})...")
                        # Original reports were per-project. How to handle this in new structure?
                        # For now, let's assume we might save them in a sub-folder or with combined names.
                        # This part needs more thought if original reports are a priority.
                        # original_report_dir = os.path.join(folder_c_path, portfolio_company['name'] + "_OriginalAnalyses")
                        # os.makedirs(original_report_dir, exist_ok=True)
                        # adv = advisory_potential(text_content_a)
                        # risk = assess_risk(text_content_a)
                        # score = project_scoring(text_content_a)
                        # rec = generate_recommendations(text_content_a)
                        # save_original_report_in_directory(adv, "advisory", original_report_dir, company_name_a)
                        # save_original_report_in_directory(risk, "risk_assessment", original_report_dir, company_name_a)
                        # save_original_report_in_directory(score, "project_score", original_report_dir, company_name_a)
                        # save_original_report_in_directory(rec, "recommendations", original_report_dir, company_name_a)
                        pass # Placeholder for now
                else:
                    print(f"  Could not read content for pitch file {filename_a}")
            else:
                print(f"  Skipping non-txt/pdf file in Folder A: {filename_a}")
        
        # Generate and save the consolidated report for the current portfolio company
        if current_portfolio_synergies:
            generate_report_for_portfolio_company(
                portfolio_company_name=portfolio_company['name'],
                portfolio_cofounders=portfolio_company['cofounders'],
                synergy_analyses=current_portfolio_synergies,
                output_folder_c=folder_c_path
            )
        else:
            print(f"No suitable pitches found in Folder A to analyze against {portfolio_company['name']}. No report generated.")

    print("\nProcessing complete.")

if __name__ == "__main__":
    main()

