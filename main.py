import os
import ollama
import json
import datetime
import requests
from bs4 import BeautifulSoup
from pdfreader import SimplePDFViewer
# Removed Selenium imports



from playwright.sync_api import sync_playwright  # Import Playwright

def get_document_content(filename):
    """Get content of a document from Google Drive or website."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")



def extract_text(content):
    """Extract and clean text from the document."""
    try:
        extracted_text = content.replace('\n', ' ')
        extracted_text = extracted_text.lower().replace('—', ', ').replace('---', '.').replace('--', '-')
        #print("extracted text: "+extracted_text+"\n")
        return extracted_text
    except Exception as e:
        raise ValueError(f"Error extracting text: {e}")

def assess_risk(text):
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

def project_roi(text):
    """Project ROI multiplier based on deck analysis."""
    try:
        response = ollama.chat(  # Corrected to chat.completions.create
            model="llama3.2:latest",  # Replace with your actual model name
            messages=[
                {"role": "system", "content": "You are a financial advisor projecting ROI."},
                {"role": "user", "content": f"Project ROI multiplier and possible returns for this deck: {text}"}
            ]
        )
        return response['message']['content']
    except Exception as e:
        raise ValueError(f"Error in ROI projection: {e}")

def generate_recommendations(text):
    """Generate recommendations based on the analysis."""
    try:
        response = ollama.chat(  # Corrected to chat.completions.create
            model="llama3.2:latest",  # Replace with your actual model name
            messages=[
                {"role": "system", "content": "You are a financial advisor providing investment recommendations."},
                {"role": "user", "content": f"Based on this text extracted from a pdf deck, provide detailed investment recommendations: {text}"}
            ]
        )
        return response['message']['content']
    except Exception as e:
        raise ValueError(f"Error in recommendations: {e}")

def save_report(report_content, report_type, project_name):
    """Save the report content to a file with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_name}_{report_type}_{timestamp}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"{report_type.capitalize()} report saved to {filename}")

def get_website_content(url, email):
        """Scrape content from a website link using Playwright, handling no email input, and navigate through all pages."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)

                # Check if the email input field exists
                email_input = page.locator('input[name="email"]')
                if email_input.count() > 0:
                    email_input.wait_for(state="visible")
                    email_input.fill(email)
                    email_input.press("Enter")
                    page.wait_for_timeout(5000)

                else:
                    print("No email input field found. Proceeding to scrape directly.")
                    page.wait_for_timeout(2000)

                # Extract text from all pages
                all_text = ""
                while True:
                    text = page.evaluate('() => document.body.innerText')
                    all_text += text + "\n"
                    
                    # Check for next page button and click if exists
                    next_button = page.locator('button[aria-label="Next page"]')
                    if next_button.count() > 0 and next_button.is_enabled():
                        next_button.click()
                        page.wait_for_timeout(2000)
                    else:
                        break

                # Extract embedded links and their content up to 1 level down
                links = page.locator('a')
                for i in range(links.count()):
                    link = links.nth(i)
                    href = link.get_attribute('href')
                    if href:
                        page.goto(href)
                        page.wait_for_timeout(2000)
                        embedded_text = page.evaluate('() => document.body.innerText')
                        all_text += f"\nEmbedded link content from {href}:\n{embedded_text}\n"
                        page.go_back()
                        page.wait_for_timeout(2000)

                browser.close()
                return all_text

        except Exception as e:
            raise ValueError(f"Error scraping website content: {e}")

def get_pdf_content(file_path):
                """Extract text content from a PDF file or read directly if it's a .txt file."""
                try:
                    if file_path.lower().endswith('.txt'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return f.read()
                    else:
                        with open(file_path, 'rb') as f:
                            viewer = SimplePDFViewer(f)
                            text = ""
                            for canvas in viewer:
                                viewer.render()
                                text += " ".join(viewer.canvas.strings) + "\n"
                            return text
                except Exception as e:
                    raise ValueError(f"Error reading file: {e}")


def save_report_in_directory(report_content, report_type, directory):
            """Save the report content to a file in the specified directory with a timestamp."""
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(directory, f"{report_type}_{timestamp}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"{report_type.capitalize()} report saved to {filename}")

def create_report_directory(project_name):
            """Create a directory for saving reports."""
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            directory = os.path.join("reports", f"{project_name}_{timestamp}")
            os.makedirs(directory, exist_ok=True)
            return directory


def process_files_in_directory(directory):
                """Process all files in the input directory and generate reports for each."""
                processed_files = set()

                # Create a set of already processed files
                if os.path.exists("processed_files.txt"):
                    with open("processed_files.txt", 'r', encoding='utf-8') as f:
                        processed_files = set(f.read().splitlines())

                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if filename.endswith('.pdf') or filename.endswith('.txt'):
                        if filename not in processed_files:
                            try:
                                content = get_pdf_content(file_path)
                                text = extract_text(content)
                                project_name = os.path.splitext(filename)[0]
                                report_directory = create_report_directory(project_name)
                                risk_assessment = assess_risk(text)
                                roi_projection = project_roi(text)
                                recommendations = generate_recommendations(text)

                                save_report_in_directory(risk_assessment, "risk_assessment", report_directory)
                                save_report_in_directory(roi_projection, "roi_projection", report_directory)
                                save_report_in_directory(recommendations, "recommendations", report_directory)

                                # Mark the file as processed
                                with open("processed_files.txt", 'a', encoding='utf-8') as f:
                                    f.write(filename + "\n")

                                print(f"Reports for {filename} saved.")
                            except Exception as e:
                                print(f"An error occurred while processing {filename}: {e}")
                        else:
                            print(f"Reports for {filename} already exist. Skipping.")

def main():
                input_directory = "input"
                if not os.path.exists(input_directory):
                    print(f"Input directory '{input_directory}' does not exist.")
                    return

                process_files_in_directory(input_directory)
                print("All files processed.")



if __name__ == "__main__":
    main()