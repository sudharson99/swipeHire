import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime

class CraigslistJobScraper:
    def __init__(self, headless=True):
        self.setup_driver(headless)
        self.jobs_data = []
    
    def setup_driver(self, headless):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Set Chrome binary location for production vs local
        import os
        if "/app" in os.getcwd() or os.getenv('RENDER'):  # Production environment
            chrome_options.binary_location = "/usr/bin/google-chrome"
            service = Service("/usr/local/bin/chromedriver")
        else:  # Local development
            chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            try:
                service = Service(ChromeDriverManager().install())
            except:
                # Fallback to system chromedriver
                service = Service()
        
        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"Chrome setup failed: {e}")
            raise
        self.wait = WebDriverWait(self.driver, 10)
    
    def scrape_jobs(self, city="sfbay", category="jjj", max_pages=3):
        """
        Scrape job listings from Craigslist
        
        Args:
            city: Craigslist city subdomain (e.g., 'sfbay', 'newyork', 'losangeles')
            category: Job category code ('jjj' for all jobs)
            max_pages: Maximum number of pages to scrape
        """
        base_url = f"https://{city}.craigslist.org/search/{category}"
        
        try:
            for page in range(max_pages):
                page_url = f"{base_url}?s={page * 120}"  # Craigslist shows 120 results per page
                print(f"Scraping page {page + 1}: {page_url}")
                
                self.driver.get(page_url)
                time.sleep(2)  # Wait for page to load
                
                # Find all job listings - try multiple selectors
                job_listings = self.driver.find_elements(By.CSS_SELECTOR, "li.cl-search-result")
                
                if not job_listings:
                    # Try alternative selectors
                    job_listings = self.driver.find_elements(By.CSS_SELECTOR, "li.result-row")
                    
                if not job_listings:
                    # Try another alternative
                    job_listings = self.driver.find_elements(By.CSS_SELECTOR, ".result-info")
                    
                if not job_listings:
                    # Debug: show page source
                    print("DEBUG: Page title:", self.driver.title)
                    print("DEBUG: Current URL:", self.driver.current_url)
                    # Take a screenshot to see what's happening
                    self.driver.save_screenshot("debug_page.png")
                    print("DEBUG: Screenshot saved as debug_page.png")
                
                if not job_listings:
                    print("No job listings found on this page.")
                    break
                
                for job in job_listings:
                    job_data = self.extract_job_data(job)
                    if job_data:
                        self.jobs_data.append(job_data)
                
                print(f"Found {len(job_listings)} jobs on page {page + 1}")
                
        except Exception as e:
            print(f"Error scraping jobs: {str(e)}")
        
        return self.jobs_data
    
    def extract_job_data(self, job_element):
        """Extract job data from a job listing element"""
        try:
            # Job title and link
            title_element = job_element.find_element(By.CSS_SELECTOR, "a.cl-app-anchor")
            title = title_element.text.strip()
            link = title_element.get_attribute("href")
            
            # Location
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, ".cl-search-result-location")
                location = location_element.text.strip()
            except NoSuchElementException:
                location = "Not specified"
            
            # Date posted
            try:
                date_element = job_element.find_element(By.CSS_SELECTOR, ".cl-search-time")
                date_posted = date_element.get_attribute("datetime")
            except NoSuchElementException:
                date_posted = "Not specified"
            
            # Company/employer (if available)
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, ".cl-search-result-title-company")
                company = company_element.text.strip()
            except NoSuchElementException:
                company = "Not specified"
            
            # Price/salary (if available)
            try:
                price_element = job_element.find_element(By.CSS_SELECTOR, ".cl-search-result-price")
                salary = price_element.text.strip()
            except NoSuchElementException:
                salary = "Not specified"
            
            # Skip screenshots for production deployment
            screenshot_path = None
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted_date': date_posted,
                'job_url': link,
                'source_portal': 'craigslist',
                'city': city.lower(),
                'province': 'BC' if city == 'vancouver' else 'ON' if city == 'toronto' else 'AB',
                'description': title,  # Use title as basic description
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"Error extracting job data: {str(e)}")
            return None
    
    def get_job_details(self, job_url):
        """Get detailed job description from individual job page"""
        try:
            self.driver.get(job_url)
            time.sleep(2)
            
            # Get job description
            try:
                description_element = self.driver.find_element(By.CSS_SELECTOR, "#postingbody")
                description = description_element.text.strip()
            except NoSuchElementException:
                description = "Description not found"
            
            # Get additional details
            details = {}
            try:
                attrs = self.driver.find_elements(By.CSS_SELECTOR, ".attrgroup span")
                for attr in attrs:
                    text = attr.text.strip()
                    if ": " in text:
                        key, value = text.split(": ", 1)
                        details[key] = value
            except NoSuchElementException:
                pass
            
            return {
                'description': description,
                'details': details
            }
            
        except Exception as e:
            print(f"Error getting job details: {str(e)}")
            return None
    
    def save_to_csv(self, filename="craigslist_jobs.csv"):
        """Save scraped jobs to CSV file"""
        if not self.jobs_data:
            print("No jobs data to save.")
            return
        
        df = pd.DataFrame(self.jobs_data)
        df.to_csv(filename, index=False)
        print(f"Saved {len(self.jobs_data)} jobs to {filename}")
    
    def save_to_json(self, filename="craigslist_jobs.json"):
        """Save scraped jobs to JSON file"""
        if not self.jobs_data:
            print("No jobs data to save.")
            return
        
        df = pd.DataFrame(self.jobs_data)
        df.to_json(filename, orient='records', indent=2)
        print(f"Saved {len(self.jobs_data)} jobs to {filename}")
    
    
    def close(self):
        """Close the browser driver"""
        self.driver.quit()

def main():
    """Main function to run the scraper"""
    # Initialize scraper
    scraper = CraigslistJobScraper(headless=True)  # Set to False to see browser
    
    try:
        # Scrape jobs from Vancouver
        print("Starting to scrape Craigslist jobs...")
        jobs = scraper.scrape_jobs(
            city="vancouver",  # Change to your desired city
            category="jjj",  # 'jjj' for all jobs
            max_pages=1  # Number of pages to scrape
        )
        
        print(f"Total jobs scraped: {len(jobs)}")
        
        # Display first few jobs
        for i, job in enumerate(jobs[:5]):
            print(f"\n--- Job {i+1} ---")
            print(f"Title: {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Location: {job['location']}")
            print(f"Salary: {job['salary']}")
            print(f"Date Posted: {job['date_posted']}")
            print(f"Link: {job['link']}")
        
        # Save to files
        scraper.save_to_csv("craigslist_jobs.csv")
        scraper.save_to_json("craigslist_jobs.json")
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
    
    finally:
        # Clean up
        scraper.close()

if __name__ == "__main__":
    main()