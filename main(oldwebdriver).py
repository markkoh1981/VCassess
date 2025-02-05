import os
import ollama
import json
import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.chrome import ChromeType  # Import ChromeType



def get_document_content(filename):
    """Get content of a document from Google Drive or DocSend."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

def extract_text(content):
    """Extract and clean text from the document."""
    try:
        # Perform additional text extraction if needed
        extracted_text = content.replace('\n', ' ')
        extracted_text = extracted_text.lower().replace('—', ', ').replace('---', '.').replace('--', '-')
        return extracted_text
    except Exception as e:
        raise ValueError(f"Error extracting text: {e}")

def assess_risk(text):
    """Assess the investibility and risk of the deck."""
    try:
        # Use Ollama to analyze the text
        response = Ollama.chat(
            model="your-risk-assessment-model",
            messages=[
                {"role": "system", "content": "You are a financial analyst assessing risk."},
                {"role": "user", "content": f"Analyze this text for investment risk and potential returns: {text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Error in risk assessment: {e}")

def project_roi(text):
    """Project ROI multiplier based on deck analysis."""
    try:
        # Use Ollama to generate ROI projection
        response = ollama.chat.completions.create(
            model="llama3.2:latest",
            messages=[
                {"role": "system", "content": "You are a financial advisor projecting ROI."},
                {"role": "user", "content": f"Project ROI multiplier and possible returns for this deck: {text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Error in ROI projection: {e}")

def generate_recommendations(text):
    """Generate recommendations based on the analysis."""
    try:
        # Use Ollama to generate recommendations
        response = ollama.chat.completions.create(
            model="your-recommendation-model",
            messages=[
                {"role": "system", "content": "You are a financial advisor providing investment recommendations."},
                {"role": "user", "content": f"Based on this deck analysis, provide detailed investment recommendations: {text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Error in recommendations: {e}")

def save_report(report_content, report_type, project_name):
    """Save the report content to a file with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_name}_{report_type}_{timestamp}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
         f.write(report_content)
    print(f"{report_type.capitalize()} report saved to {filename}")



def get_docsend_content(url, email):
    """Scrape content from a DocSend link."""
    try:
            
        # Set up Selenium WebDriver:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Use chrome_type to get the latest compatible driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROME).install()), options=options)

                      
         # Open the DocSend link
        driver.get(url)
            
        # Enter email address
        email_input = driver.find_element_by_name('email')
        email_input.send_keys(email)
        email_input.send_keys(Keys.RETURN)
            
        # Wait for the page to load
        driver.implicitly_wait(10)
            
        # Extract the content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        content = soup.get_text()
            
        driver.quit()
        return content
    except Exception as e:
        raise ValueError(f"Error scraping DocSend content: {e}")

def main():
        # Get the DocSend link and email address
        docsend_url = "https://docsend.com/view/zgkukn7wsgimvf2w"  # Replace with actual DocSend link
        email = "mark@vxglobal.sg"  # Replace with actual email address
        project_name = "Chainsatlas"  # Replace with actual project name
        
        try:
            content = get_docsend_content(docsend_url, email)
            text = extract_text(content)
            
            risk_assessment = assess_risk(text)
            roi_projection = project_roi(text)
            recommendations = generate_recommendations(text)
            
            # Save each report to a separate file
            save_report(risk_assessment, "risk_assessment", project_name)
            save_report(roi_projection, "roi_projection", project_name)
            save_report(recommendations, "recommendations", project_name)
            
            print("Analysis complete. Reports saved.")
            
        except Exception as e:
            print(f"An error occurred: {e}")

   


if __name__ == "__main__":
            main()

