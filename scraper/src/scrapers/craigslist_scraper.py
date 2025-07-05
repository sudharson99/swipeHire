"""
Craigslist Job Scraper for SwipeHire
Scrapes job listings from Craigslist for major Canadian cities
"""

import os
import re
import time
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from ..utils.logger import setup_logger

class CraigslistScraper:
    def __init__(self):
        self.logger = setup_logger()
        self.base_urls = {
            'vancouver': 'https://vancouver.craigslist.org',
            'toronto': 'https://toronto.craigslist.org', 
            'calgary': 'https://calgary.craigslist.org'
        }
        
        # Headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with proper options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
        
        # Use system Chrome in production, ChromeDriverManager locally
        try:
            if "/app" in os.getcwd():  # Production environment
                chrome_options.binary_location = "/usr/bin/google-chrome"
                service = Service("/usr/bin/chromedriver")
            else:  # Development environment
                service = Service(ChromeDriverManager().install())
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {str(e)}")
            raise

    def scrape_jobs(self, city: str, max_jobs: int = 50) -> List[Dict]:
        """Scrape jobs from Craigslist for a specific city"""
        if city not in self.base_urls:
            self.logger.error(f"❌ City {city} not supported")
            return []
        
        base_url = self.base_urls[city]
        jobs = []
        
        try:
            # Get job listings from multiple categories
            categories = ['jjj']  # All jobs category
            
            for category in categories:
                category_jobs = self._scrape_category(base_url, category, max_jobs)
                jobs.extend(category_jobs)
                
                if len(jobs) >= max_jobs:
                    break
            
            # Limit to max_jobs
            jobs = jobs[:max_jobs]
            
            self.logger.info(f"📊 Scraped {len(jobs)} jobs for {city}")
            return jobs
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping {city}: {str(e)}")
            return []

    def _scrape_category(self, base_url: str, category: str, max_jobs: int) -> List[Dict]:
        """Scrape jobs from a specific category"""
        jobs = []
        
        try:
            # Use requests for listing page (faster)
            url = f"{base_url}/search/{category}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_links = soup.find_all('a', class_='cl-app-anchor')
            
            self.logger.info(f"🔗 Found {len(job_links)} job links")
            
            # Use Selenium for detailed job pages
            driver = None
            try:
                driver = self.setup_driver()
                
                for i, link in enumerate(job_links[:max_jobs]):
                    if i >= max_jobs:
                        break
                    
                    try:
                        job_url = link.get('href')
                        if not job_url.startswith('http'):
                            job_url = base_url + job_url
                        
                        job_data = self._scrape_job_details(driver, job_url)
                        if job_data:
                            jobs.append(job_data)
                        
                        # Random delay to avoid blocking
                        time.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️  Error scraping job {i}: {str(e)}")
                        continue
            
            finally:
                if driver:
                    driver.quit()
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping category {category}: {str(e)}")
            return []

    def _scrape_job_details(self, driver: webdriver.Chrome, job_url: str) -> Optional[Dict]:
        """Scrape detailed information from a job posting"""
        try:
            driver.get(job_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "titletextonly"))
            )
            
            # Extract job details
            title_element = driver.find_element(By.ID, "titletextonly")
            title = title_element.text.strip()
            
            # Get posting body
            body_element = driver.find_element(By.ID, "postingbody")
            description = body_element.text.strip()
            
            # Extract location
            location = "Unknown"
            try:
                location_elements = driver.find_elements(By.CSS_SELECTOR, ".attrgroup span")
                for elem in location_elements:
                    if "(" in elem.text and ")" in elem.text:
                        location = elem.text.strip("()")
                        break
            except:
                pass
            
            # Extract posting date
            posted_date = None
            try:
                date_element = driver.find_element(By.CSS_SELECTOR, ".postinginfo .date")
                date_text = date_element.get_attribute("datetime")
                if date_text:
                    posted_date = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
            except:
                posted_date = datetime.now()
            
            # Extract contact info
            contact_email = None
            contact_phone = None
            
            # Look for email in description
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, description)
            if email_matches:
                contact_email = email_matches[0]
            
            # Look for phone in description
            phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
            phone_matches = re.findall(phone_pattern, description)
            if phone_matches:
                contact_phone = phone_matches[0]
            
            # Determine city from URL
            city = self._extract_city_from_url(job_url)
            
            # Clean and format description
            description_clean = self._clean_description(description)
            
            job_data = {
                'title': title,
                'company': self._extract_company(description_clean),
                'location': location,
                'city': city,
                'province': self._get_province(city),
                'description': description_clean[:500] + '...' if len(description_clean) > 500 else description_clean,
                'full_description': description_clean,
                'job_url': job_url,
                'source_portal': 'craigslist',
                'contact_email': contact_email,
                'contact_phone': contact_phone,
                'posted_date': posted_date,
                'job_type': self._extract_job_type(description_clean),
                'experience_level': self._extract_experience_level(description_clean)
            }
            
            return job_data
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error scraping job details from {job_url}: {str(e)}")
            return None

    def _extract_city_from_url(self, url: str) -> str:
        """Extract city from Craigslist URL"""
        if 'vancouver' in url:
            return 'vancouver'
        elif 'toronto' in url:
            return 'toronto'
        elif 'calgary' in url:
            return 'calgary'
        else:
            return 'unknown'

    def _get_province(self, city: str) -> str:
        """Get province for city"""
        city_provinces = {
            'vancouver': 'BC',
            'toronto': 'ON',
            'calgary': 'AB'
        }
        return city_provinces.get(city, 'Unknown')

    def _clean_description(self, description: str) -> str:
        """Clean and format job description"""
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove QR code text
        description = re.sub(r'QR Code Link to This Post', '', description)
        
        # Remove posting boilerplate
        description = re.sub(r'post id:.*$', '', description, flags=re.IGNORECASE)
        description = re.sub(r'do NOT contact me.*$', '', description, flags=re.IGNORECASE)
        
        return description.strip()

    def _extract_company(self, description: str) -> str:
        """Extract company name from description"""
        # Look for common company indicators
        lines = description.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if line and len(line) < 100:  # Reasonable company name length
                # Skip obvious non-company lines
                skip_patterns = ['job', 'position', 'we are', 'looking for', 'hiring']
                if not any(pattern in line.lower() for pattern in skip_patterns):
                    return line
        
        return "Company Not Listed"

    def _extract_job_type(self, description: str) -> str:
        """Extract job type from description"""
        description_lower = description.lower()
        
        if any(term in description_lower for term in ['full-time', 'full time', 'fulltime']):
            return 'full-time'
        elif any(term in description_lower for term in ['part-time', 'part time', 'parttime']):
            return 'part-time'
        elif any(term in description_lower for term in ['contract', 'contractor', 'freelance']):
            return 'contract'
        elif any(term in description_lower for term in ['intern', 'internship']):
            return 'internship'
        else:
            return 'full-time'  # Default

    def _extract_experience_level(self, description: str) -> str:
        """Extract experience level from description"""
        description_lower = description.lower()
        
        if any(term in description_lower for term in ['senior', 'lead', 'principal', '5+ years', '5 years']):
            return 'senior'
        elif any(term in description_lower for term in ['junior', 'entry', 'entry-level', 'new grad', 'recent grad']):
            return 'entry'
        elif any(term in description_lower for term in ['mid', 'intermediate', '2-3 years', '3+ years']):
            return 'mid'
        else:
            return 'mid'  # Default