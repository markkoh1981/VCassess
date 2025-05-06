import os
import ollama
import json
import datetime
import re
from pdfreader import SimplePDFViewer
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
    """Extracts cofounder names from text content or returns a placeholder."""
    # Search for keywords like "Founders:", "Team:", "Point of Contact:"
    # This is a simplistic approach and might need refinement based on actual document structures.
    text_lower = text_content.lower()
    keywords = ["founders:", "founder:", "team:", "point of contact:", "contact person:"]
    found_names = []

    for keyword in keywords:
        if keyword in text_lower:
            # Try to extract text following the keyword (e.g., up to the next sentence or a certain length)
            try:
                start_index = text_lower.find(keyword) + len(keyword)
                # Look for a sentence or a reasonable chunk of text after the keyword.
                # This is a heuristic and might need to be more robust.
                potential_names_section = text_content[start_index : start_index + 200] # Look in the next 200 chars
                
                # A very basic attempt to identify names - this likely needs a more sophisticated NLP approach
                # or clearer patterns in the documents.
                # For now, let's assume the line after the keyword might contain names.
                lines = potential_names_section.splitlines()
                if lines:
                    first_line_after_keyword = lines[0].strip()
                    if first_line_after_keyword and len(first_line_after_keyword) < 100: # Avoid very long lines
                         # Simplistic: assume the first line after keyword contains names
                        # This is a placeholder for a more robust extraction logic
                        if len(first_line_after_keyword.split()) > 1 and len(first_line_after_keyword.split()) < 7: # Heuristic for names
                            found_names.append(first_line_after_keyword)
                            # For now, take the first finding. More sophisticated logic could find multiple.
                            break 
            except Exception as e:
                print(f"Error during cofounder name extraction: {e}")
                continue
    
    if found_names:
        # Join multiple found names if any, or return the first one found
        return ", ".join(found_names)
    else:
        return f"the Team at {company_name_a}" # Placeholder

# --- Core Synergy Analysis Function ---
def analyze_synergy(pitch_company_name, pitch_content, portfolio_company_name, portfolio_content, synergy_criteria_text):
    """Analyzes synergy between a pitch and a portfolio company using LLM."""
    print(f"Analyzing synergy between {pitch_company_name} and {portfolio_company_name}...")
    
    prompt = f"""
    You are a VC Analyst. Your task is to identify and evaluate potential synergies between a new pitch (Folder A company) and an existing portfolio company (Folder B company).

    **Portfolio Company (Folder B):** {portfolio_company_name}
    **Portfolio Company Details:** {portfolio_content}

    **New Pitch Company (Folder A):** {pitch_company_name}
    **New Pitch Company Details:** {pitch_content}

    **Synergy Evaluation Framework:**
    {synergy_criteria_text}

    **Instructions:**
    1.  Based on the details of both companies and the Synergy Evaluation Framework, provide an insightful explanation of potential synergies. Consider if the Folder B company could be a client, partner, etc., of the Folder A company, or vice-versa.
    2.  For each identified potential synergy, assess it based on the following categories (from the framework):
        *   **Synergy Type:** (e.g., Client Relationship, Channel Expansion, Technology Integration, etc. - pick from the provided list in the framework)
        *   **Feasibility:** (How easily can it be executed? Consider integration complexity, legal barriers, cultural fit.)
        *   **Scalability:** (Is this a one-off opportunity or a repeatable growth lever?)
        *   **Defensibility:** (Does the synergy create a moat? e.g., exclusive partnership, unique tech integration)
        *   **Alignment with Goals:** (Does this help the portfolio company hit its KPIs? e.g., revenue, market share, product roadmap)
    3.  Identify any **Red Flags (False Synergies):** (e.g., One-Sided Value, High Execution Cost, Strategic Misalignment - pick from the provided list in the framework if applicable).
    4.  Classify the overall synergy potential as: **Immediate Opportunity**, **Strategic Long-Term Play**, or **Low Priority**.
    5.  Provide a concise **Explanation for Introduction:** This explanation will be used in an email introducing the two companies. It should be compelling and clearly state the core reason for the introduction based on the most promising synergy.

    **Output Format:**
    Please structure your response clearly. For example:

    **Synergy Analysis for {pitch_company_name} with {portfolio_company_name}:**

    **1. Potential Synergy: [Describe the synergy, e.g., {portfolio_company_name} as a Client for {pitch_company_name}]**
       *   **Synergy Type:** [e.g., Client Relationship]
       *   **Feasibility:** [Your assessment]
       *   **Scalability:** [Your assessment]
       *   **Defensibility:** [Your assessment]
       *   **Alignment with Goals ({portfolio_company_name}):** [Your assessment]
       *   **Red Flags:** [e.g., None identified / or describe red flag]

    **2. Potential Synergy: [Describe another synergy, if any]**
       *   ...

    **Overall Synergy Classification:** [Immediate Opportunity / Strategic Long-Term Play / Low Priority]

    **Explanation for Introduction:** [Your concise explanation for the email introduction]
    """

    try:
        response = ollama.chat(
            model="llama3.2:latest", # As per user's existing setup
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
    """Generates a single report document for a portfolio company, containing all its synergy analyses."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # LLM to recommend report format - for now, let's use Markdown for better readability.
    report_filename = os.path.join(output_folder_c, f"{portfolio_company_name}_Synergy_Report_{timestamp}.md")
    
    report_content = f"# Synergy Report for {portfolio_company_name}\n\n"
    report_content += f"**Date Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_content += f"This report outlines potential synergies between {portfolio_company_name} and various new pitches evaluated.\n\n"
    report_content += "---\n"

    if not synergy_analyses:
        report_content += "No potential synergies identified with the evaluated pitches.\n"
    else:
        for analysis in synergy_analyses:
            pitch_company_name = analysis['pitch_company_name']
            pitch_cofounders = analysis['pitch_cofounders']
            introduction_explanation = analysis['introduction_explanation'] # This should be extracted from LLM output
            detailed_analysis = analysis['detailed_analysis'] # Full LLM output for this pair

            # Formal email style introduction
            report_content += f"## Potential Introduction: {portfolio_company_name} & {pitch_company_name}\n\n"
            report_content += f"**To:** {portfolio_cofounders} (Team at {portfolio_company_name})\n"
            report_content += f"**From:** [Your Name/VC Firm Name]\n"
            report_content += f"**Subject:** Introduction: {portfolio_company_name} & {pitch_company_name}\n\n"
            team_placeholder_greeting = f'the Team at {portfolio_company_name}'
            actual_greeting_recipient = portfolio_cofounders if portfolio_cofounders != team_placeholder_greeting else 'Team'
            report_content += f"Hi {actual_greeting_recipient},\n\n"
            report_content += f"I hope this email finds you well.\n\n"
            report_content += f"I'd like to introduce you to {pitch_cofounders} of {pitch_company_name}. "
            report_content += f"{introduction_explanation}\n\n"
            report_content += f"I believe there could be a valuable connection here. Please find a more detailed synergy analysis below.\n\n"
            report_content += f"Best regards,\n[Your Name]\n\n"
            report_content += f"### Detailed Synergy Analysis: {pitch_company_name} with {portfolio_company_name}\n\n"
            report_content += f"{detailed_analysis}\n\n"
            report_content += "---\n\n"

    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Synergy report saved to {report_filename}")
        return report_filename
    except Exception as e:
        print(f"Error saving report {report_filename}: {e}")
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
    # ... (original code from main.py)
    return "Risk assessed (mock)."

def project_scoring(text):
    if not RUN_ORIGINAL_ANALYSIS: return "Project scoring skipped."
    # ... (original code from main.py, ensure 'judging_criteria.txt' is accessible)
    return "Project scored (mock)."

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

    # Load synergy criteria (from analysis_criteria.txt)
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

