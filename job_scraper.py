#!/usr/bin/env python3
"""
Job Scraper - Python script to scrape jobs from multiple sources
Uses requests, beautifulsoup4, and selenium for robust scraping
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.driver = None
        
    def init_selenium(self):
        """Initialize Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Selenium WebDriver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Selenium: {e}")
                return False
        return True
    
    def close_selenium(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Selenium WebDriver closed")
    
    def scrape_indeed(self, search_term="software developer", location="vancouver"):
        """Scrape jobs from Indeed"""
        jobs = []
        try:
            logger.info(f"Scraping Indeed for: {search_term} in {location}")
            
            if not self.init_selenium():
                return jobs
            
            url = f"https://ca.indeed.com/jobs?q={search_term.replace(' ', '+')}&l={location.replace(' ', '+')}"
            self.driver.get(url)
            
            # Wait for job listings to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk], .job_seen_beacon, .tapItem"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for Indeed job listings")
                return jobs
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find job listings
            job_elements = soup.select("[data-jk], .job_seen_beacon, .tapItem")
            
            for element in job_elements[:25]:  # Limit to 25 jobs
                try:
                    # Extract title and link
                    title_elem = element.select_one("h2 a, .jobTitle a, .title a")
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href')
                    if link and not link.startswith('http'):
                        link = f"https://ca.indeed.com{link}"
                    
                    if not title or not link:
                        continue
                    
                    # Extract company name
                    company_elem = element.select_one('[data-testid="company-name"], .companyName, .company')
                    company = company_elem.get_text(strip=True) if company_elem else "Company not listed"
                    
                    # Extract location
                    location_elem = element.select_one('[data-testid="job-location"], .companyLocation, .location')
                    job_location = location_elem.get_text(strip=True) if location_elem else f"{location}, BC"
                    
                    # Extract salary
                    salary_elem = element.select_one('[data-testid="attribute_snippet_testid"], .salary-snippet, .metadata')
                    salary = "Salary not listed"
                    if salary_elem:
                        salary_text = salary_elem.get_text(strip=True)
                        if '$' in salary_text:
                            salary = salary_text
                    
                    # Extract description/snippet
                    snippet_elem = element.select_one('[data-testid="job-snippet"], .summary, .snippet')
                    description = snippet_elem.get_text(strip=True) if snippet_elem else "No description available"
                    
                    # Generate tags
                    tags = self.generate_tags(title, description)
                    
                    job = {
                        'id': f"indeed_{len(jobs) + 1}",
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'salary': salary,
                        'description': description[:300] + "..." if len(description) > 300 else description,
                        'tags': tags,
                        'source': 'Indeed',
                        'datePosted': datetime.now().isoformat(),
                        'link': link
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.error(f"Error parsing Indeed job: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from Indeed")
            
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
        
        return jobs
    
    def scrape_glassdoor(self, search_term="software developer", location="vancouver"):
        """Scrape jobs from Glassdoor"""
        jobs = []
        try:
            logger.info(f"Scraping Glassdoor for: {search_term} in {location}")
            
            if not self.init_selenium():
                return jobs
            
            # Glassdoor URL
            url = f"https://www.glassdoor.ca/Job/canada-{search_term.replace(' ', '-')}-jobs-SRCH_IL.0,6_IN3_KO7,{search_term.replace(' ', '%20')}.htm"
            self.driver.get(url)
            
            # Wait for job listings to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".react-job-listing, .job-listing, [data-test='jobListing']"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for Glassdoor job listings")
                return jobs
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find job listings
            job_elements = soup.select(".react-job-listing, .job-listing, [data-test='jobListing']")
            
            for element in job_elements[:25]:  # Limit to 25 jobs
                try:
                    # Extract title and link
                    title_elem = element.select_one("a[data-test='job-link'], .jobLink, h3 a")
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href')
                    if link and not link.startswith('http'):
                        link = f"https://www.glassdoor.ca{link}"
                    
                    if not title or not link:
                        continue
                    
                    # Extract company name
                    company_elem = element.select_one('[data-test="employer-name"], .employerName, .company')
                    company = company_elem.get_text(strip=True) if company_elem else "Company not listed"
                    
                    # Extract location
                    location_elem = element.select_one('[data-test="location"], .location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else f"{location}, BC"
                    
                    # Extract salary
                    salary_elem = element.select_one('[data-test="salary-estimate"], .salary, .compensation')
                    salary = "Salary not listed"
                    if salary_elem:
                        salary_text = salary_elem.get_text(strip=True)
                        if '$' in salary_text or 'CAD' in salary_text:
                            salary = salary_text
                    
                    # Extract description/snippet
                    snippet_elem = element.select_one('.job-description, .snippet, .description')
                    description = snippet_elem.get_text(strip=True) if snippet_elem else "No description available"
                    
                    # Generate tags
                    tags = self.generate_tags(title, description)
                    
                    job = {
                        'id': f"glassdoor_{len(jobs) + 1}",
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'salary': salary,
                        'description': description[:300] + "..." if len(description) > 300 else description,
                        'tags': tags,
                        'source': 'Glassdoor',
                        'datePosted': datetime.now().isoformat(),
                        'link': link
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.error(f"Error parsing Glassdoor job: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from Glassdoor")
            
        except Exception as e:
            logger.error(f"Error scraping Glassdoor: {e}")
        
        return jobs

    def is_valid_job(self, title, description):
        """Check if the scraped content looks like a real job posting"""
        if not title or not description:
            return False
            
        # Convert to lowercase for easier checking
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Skip common non-job entries
        skip_keywords = [
            'fair housing', 'safety tips', 'prohibited items', 'product recalls',
            'avoiding scams', 'terms of use', 'privacy policy', 'help', 
            'about', 'contact', 'advertise', 'posting guidelines', 
            'community guidelines', 'cl help', 'craigslist', 'safety'
        ]
        
        for keyword in skip_keywords:
            if keyword in title_lower and len(title_lower) < 30:
                return False
        
        # Skip very short titles that are likely navigation elements
        if len(title.strip()) < 3:
            return False
            
        # Skip titles that are just single words like "CL", "help", etc.
        words = title.strip().split()
        if len(words) == 1 and len(words[0]) < 4:
            return False
        
        # Check for job-related keywords (more lenient now)
        job_keywords = [
            'job', 'position', 'opening', 'opportunity', 'career', 'work',
            'developer', 'engineer', 'analyst', 'specialist', 'manager',
            'coordinator', 'assistant', 'associate', 'senior', 'junior',
            'lead', 'principal', 'architect', 'consultant', 'advisor',
            'programmer', 'coder', 'designer', 'administrator', 'technician',
            'sales', 'marketing', 'accountant', 'clerk', 'receptionist',
            'driver', 'cook', 'server', 'bartender', 'cashier', 'retail',
            'nurse', 'teacher', 'instructor', 'trainer', 'mechanic',
            'electrician', 'plumber', 'carpenter', 'contractor', 'freelance'
        ]
        
        has_job_keyword = any(keyword in title_lower or keyword in desc_lower for keyword in job_keywords)
        
        # Check for reasonable length
        reasonable_length = len(title) > 3 and len(description) > 10
        
        # If it has job keywords OR reasonable length, consider it valid
        return (has_job_keyword or reasonable_length) and len(title) < 200
    
    def scrape_craigslist(self, search_term="jobs", location="vancouver"):
        """Scrape jobs from Craigslist Vancouver - last 2 days only"""
        jobs = []
        try:
            logger.info(f"Scraping Craigslist Vancouver for: {search_term} (last 2 days)")
            
            if not self.init_selenium():
                return jobs
            
            # Craigslist Vancouver jobs URL with date filter for last 2 days
            # postedToday=1 gets last 2 days, max_auto_miles=0 for exact location
            url = f"https://vancouver.craigslist.org/search/jjj?query={search_term.replace(' ', '+')}&postedToday=1&max_auto_miles=0"
            logger.info(f"Accessing URL: {url}")
            
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Take a screenshot for debugging with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"craigslist_jobs_{timestamp}.png"
            self.driver.save_screenshot(screenshot_name)
            logger.info(f"Screenshot saved as {screenshot_name}")
            print(f"📸 Screenshot saved: {screenshot_name}")
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try multiple selectors for job listings
            selectors = [
                '.cl-app-anchor',
                '.result-row',
                '.posting',
                '.result',
                'a[href*="/jjj/"]',
                '.search-results .cl-app-anchor',
                '[data-testid="search-results"] .cl-app-anchor'
            ]
            
            job_elements = []
            for selector in selectors:
                job_elements = soup.select(selector)
                if job_elements:
                    logger.info(f"Found {len(job_elements)} jobs with selector: {selector}")
                    break
            
            # Process job elements found with selectors - get more jobs
            for element in job_elements[:100]:
                try:
                    # Extract title and link - try multiple approaches
                    title_elem = None
                    link = None
                    
                    # First try to find the link directly in the element
                    if element.name == 'a' and element.get('href'):
                        title_elem = element
                        link = element.get('href')
                    else:
                        # Look for links within the element
                        title_elem = element.select_one('a[href*="/jjj/"], a[href*="craigslist"], h3 a, .posting-title a, .title a')
                        if title_elem:
                            link = title_elem.get('href')
                    
                    if not title_elem or not link:
                        # Try to find any link in the element
                        all_links = element.find_all('a', href=True)
                        for a_link in all_links:
                            href = a_link.get('href', '')
                            if '/jjj/' in href or 'craigslist' in href:
                                title_elem = a_link
                                link = href
                                break
                    
                    if not title_elem or not link:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue
                    
                    # Make URL absolute
                    if link.startswith('/'):
                        link = f"https://vancouver.craigslist.org{link}"
                    elif not link.startswith('http'):
                        link = f"https://vancouver.craigslist.org{link}"
                    
                    # Extract company name - try multiple selectors
                    company = "Company not listed"
                    company_selectors = ['.company', '.employer', '.posting-company', '.meta', '.result-meta']
                    for selector in company_selectors:
                        company_elem = element.select_one(selector)
                        if company_elem:
                            company_text = company_elem.get_text(strip=True)
                            if company_text and len(company_text) < 100:
                                company = company_text
                                break
                    
                    # Extract location
                    location = "Vancouver, BC"
                    location_selectors = ['.location', '.posting-neighborhood', '.result-hood', '.meta']
                    for selector in location_selectors:
                        location_elem = element.select_one(selector)
                        if location_elem:
                            location_text = location_elem.get_text(strip=True)
                            if location_text and len(location_text) < 100:
                                location = location_text
                                break
                    
                    # Extract salary
                    salary = "Salary not listed"
                    salary_selectors = ['.price', '.salary', '.compensation', '.result-price']
                    for selector in salary_selectors:
                        salary_elem = element.select_one(selector)
                        if salary_elem:
                            salary_text = salary_elem.get_text(strip=True)
                            if salary_text:
                                salary = salary_text
                                break
                    
                    # Extract description/snippet
                    description = f"Job posting for {title}. Click the link for more details."
                    desc_selectors = ['.description', '.snippet', '.summary', '.result-snippet']
                    for selector in desc_selectors:
                        snippet_elem = element.select_one(selector)
                        if snippet_elem:
                            desc_text = snippet_elem.get_text(strip=True)
                            if desc_text and len(desc_text) > 10:
                                description = desc_text
                                break
                    
                    # Try to get more detailed description from the job page
                    try:
                        if link and '/jjj/' in link:
                            logger.info(f"Fetching detailed info for: {title}")
                            # Visit the job page to get more details
                            self.driver.get(link)
                            time.sleep(3)  # Give more time for page to load
                            
                            job_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                            
                            # Try to get full description - Craigslist specific selectors
                            desc_selectors = [
                                '#postingbody',
                                '.posting-body',
                                '.description',
                                '.job-description',
                                '.content',
                                '.posting-content',
                                '.attrgroup + .posting-body',
                                '.posting-bodytext',
                                '.userbody'
                            ]
                            
                            for desc_selector in desc_selectors:
                                desc_elem = job_soup.select_one(desc_selector)
                                if desc_elem:
                                    full_desc = desc_elem.get_text(strip=True)
                                    if len(full_desc) > 50:  # Make sure we got meaningful content
                                        description = full_desc
                                        logger.info(f"Found detailed description ({len(full_desc)} chars) with selector: {desc_selector}")
                                        break
                            
                            # Try to get more company info
                            company_selectors = [
                                '.company-name',
                                '.employer-name',
                                '.posting-company',
                                '.company',
                                '.attrgroup .attrgroup',
                                '.meta .posting-company'
                            ]
                            
                            for comp_selector in company_selectors:
                                comp_elem = job_soup.select_one(comp_selector)
                                if comp_elem:
                                    comp_text = comp_elem.get_text(strip=True)
                                    if comp_text and len(comp_text) < 100 and comp_text.lower() not in ['company not listed', 'anonymous']:
                                        company = comp_text
                                        logger.info(f"Found company: {company}")
                                        break
                            
                            # Try to get salary information
                            salary_selectors = [
                                '.price',
                                '.salary',
                                '.compensation',
                                '.attrgroup .price',
                                '.posting-price'
                            ]
                            
                            for salary_selector in salary_selectors:
                                salary_elem = job_soup.select_one(salary_selector)
                                if salary_elem:
                                    salary_text = salary_elem.get_text(strip=True)
                                    if salary_text and len(salary_text) < 50:
                                        salary = salary_text
                                        logger.info(f"Found salary: {salary}")
                                        break
                            
                            # Go back to search results
                            self.driver.get(url)
                            time.sleep(2)
                            
                    except Exception as e:
                        logger.warning(f"Could not fetch detailed job info for {title}: {e}")
                        # Continue with basic info
                    
                    # Generate tags
                    tags = self.generate_tags(title, description)
                    
                    job = {
                        'id': f"craigslist_{len(jobs) + 1}",
                        'title': title,
                        'company': company,
                        'location': location,
                        'salary': salary,
                        'description': description,
                        'tags': tags,
                        'source': 'Craigslist Vancouver',
                        'datePosted': datetime.now().isoformat(),
                        'link': link
                    }
                    
                    # Verify this looks like a real job before adding
                    if self.is_valid_job(title, description):
                        jobs.append(job)
                        logger.info(f"Added job: {title}")
                    else:
                        logger.info(f"Skipped non-job: {title}")
                    
                except Exception as e:
                    logger.error(f"Error parsing Craigslist job: {e}")
                    continue
            
            # If no jobs found with selectors, try fallback approach
            if not jobs:
                logger.info("No jobs found with selectors, trying fallback approach...")
                all_links = soup.find_all('a', href=True)
                job_links = [link for link in all_links if '/jjj/' in link.get('href', '')]
                logger.info(f"Found {len(job_links)} job links in fallback")
                
                for link in job_links[:100]:
                    try:
                        title = link.get_text(strip=True)
                        href = link.get('href')
                        
                        if not title or not href:
                            continue
                        
                        # Make URL absolute
                        if href.startswith('/'):
                            href = f"https://vancouver.craigslist.org{href}"
                        elif not href.startswith('http'):
                            href = f"https://vancouver.craigslist.org{href}"
                        
                        # Try to extract more info from the parent element
                        parent = link.parent
                        company = "Company not listed"
                        location = "Vancouver, BC"
                        salary = "Salary not listed"
                        
                        # Look for company name in nearby elements
                        company_elem = parent.find_previous_sibling() or parent.find_next_sibling()
                        if company_elem:
                            company_text = company_elem.get_text(strip=True)
                            if company_text and len(company_text) < 100:
                                company = company_text
                        
                        # Generate description
                        description = f"Job posting for {title}. Click the link for more details."
                        
                        # Generate tags
                        tags = self.generate_tags(title, description)
                        
                        job = {
                            'id': f"craigslist_{len(jobs) + 1}",
                            'title': title,
                            'company': company,
                            'location': location,
                            'salary': salary,
                            'description': description,
                            'tags': tags,
                            'source': 'Craigslist Vancouver',
                            'datePosted': datetime.now().isoformat(),
                            'link': href
                        }
                        
                        jobs.append(job)
                        logger.info(f"Added job (fallback): {title}")
                        
                    except Exception as e:
                        logger.error(f"Error parsing Craigslist job (fallback): {e}")
                        continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from Craigslist Vancouver")
            
        except Exception as e:
            logger.error(f"Error scraping Craigslist: {e}")
        
        return jobs
    
    def generate_tags(self, title, description):
        """Generate tags based on job title and description"""
        content = f"{title} {description}".lower()
        tags = []
        
        # Technology keywords
        tech_keywords = {
            'JavaScript': ['javascript', 'js', 'node.js', 'nodejs'],
            'Python': ['python', 'django', 'flask'],
            'React': ['react', 'reactjs'],
            'Java': ['java', 'spring'],
            'PHP': ['php', 'wordpress'],
            'Ruby': ['ruby', 'rails'],
            'C#': ['c#', 'csharp', '.net'],
            'Go': ['go', 'golang'],
            'Rust': ['rust'],
            'TypeScript': ['typescript', 'ts'],
            'Vue.js': ['vue', 'vue.js'],
            'Angular': ['angular'],
            'MongoDB': ['mongodb', 'mongo'],
            'PostgreSQL': ['postgresql', 'postgres'],
            'MySQL': ['mysql'],
            'AWS': ['aws', 'amazon web services'],
            'Docker': ['docker'],
            'Kubernetes': ['kubernetes', 'k8s'],
            'DevOps': ['devops', 'ci/cd'],
            'Mobile': ['ios', 'android', 'mobile', 'react native'],
            'Remote': ['remote', 'work from home', 'wfh'],
            'Full-time': ['full time', 'full-time', 'fulltime'],
            'Part-time': ['part time', 'part-time', 'parttime'],
            'Contract': ['contract', 'contractor', 'freelance'],
            'Entry Level': ['entry level', 'junior', 'entry-level'],
            'Senior': ['senior', 'lead', 'principal'],
            'Frontend': ['frontend', 'front-end', 'front end', 'ui', 'ux'],
            'Backend': ['backend', 'back-end', 'back end', 'api'],
            'Full Stack': ['full stack', 'fullstack', 'full-stack']
        }
        
        for tag, keywords in tech_keywords.items():
            if any(keyword in content for keyword in keywords):
                tags.append(tag)
        
        return tags[:6]  # Limit to 6 tags
    
    def scrape_all_sources(self, search_term="", location="vancouver"):
        """Scrape jobs from Craigslist only (last 2 days)"""
        all_jobs = []
        
        # Just scrape all jobs from Craigslist
        try:
            logger.info(f"Scraping all jobs from Craigslist Vancouver")
            jobs = self.scrape_craigslist("", location)  # Empty search gets all jobs
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error scraping Craigslist: {e}")
        
        
        # Remove duplicates based on title and company
        unique_jobs = []
        seen = set()
        
        for job in all_jobs:
            key = (job['title'].lower(), job['company'].lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        logger.info(f"Total unique jobs scraped: {len(unique_jobs)}")
        return unique_jobs
    
    def get_job_details(self, job_url):
        """Get full job details including contact information from job URL"""
        try:
            if not self.init_selenium():
                return None
            
            logger.info(f"Fetching detailed job info from: {job_url}")
            self.driver.get(job_url)
            
            # Wait for page to load
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            details = {
                'fullDescription': '',
                'contactInfo': {},
                'postingDate': '',
                'compensation': '',
                'employmentType': ''
            }
            
            # Get full description
            desc_selectors = [
                '#postingbody',
                '.posting-body',
                '.userbody',
                '.posting-bodytext',
                '.section-content'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    # Clean up the description text
                    description_text = desc_elem.get_text(separator='\n', strip=True)
                    # Remove common Craigslist footer text
                    description_text = re.sub(r'QR Code Link to This Post.*$', '', description_text, flags=re.DOTALL)
                    description_text = re.sub(r'post id:.*$', '', description_text, flags=re.IGNORECASE)
                    details['fullDescription'] = description_text.strip()
                    break
            
            # Get posting date
            date_selectors = [
                'time.timeago',
                '.postingtime',
                '.date',
                'time[datetime]'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    details['postingDate'] = date_elem.get_text(strip=True)
                    break
            
            # Get compensation/salary information
            comp_selectors = [
                '.attrgroup .attr:contains("compensation")',
                '.price',
                '.salary',
                '.compensation'
            ]
            
            for selector in comp_selectors:
                try:
                    comp_elem = soup.select_one(selector)
                    if comp_elem:
                        comp_text = comp_elem.get_text(strip=True)
                        if '$' in comp_text or 'salary' in comp_text.lower():
                            details['compensation'] = comp_text
                            break
                except:
                    continue
            
            # Get employment type
            type_selectors = [
                '.attrgroup .attr:contains("employment type")',
                '.employment-type',
                '.job-type'
            ]
            
            for selector in type_selectors:
                try:
                    type_elem = soup.select_one(selector)
                    if type_elem:
                        details['employmentType'] = type_elem.get_text(strip=True)
                        break
                except:
                    continue
            
            # Extract contact information
            contact_info = {}
            
            # Look for email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, details['fullDescription'])
            if emails:
                contact_info['email'] = emails[0]  # Take the first email found
            
            # Look for phone numbers
            phone_patterns = [
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                r'\b(\d{3})-(\d{3})-(\d{4})\b',
                r'\b(\d{3})\.(\d{3})\.(\d{4})\b',
                r'\b(\d{3})\s(\d{3})\s(\d{4})\b'
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, details['fullDescription'])
                if matches:
                    # Format the first phone number found
                    if len(matches[0]) == 3:  # Tuple of 3 groups
                        contact_info['phone'] = f"({matches[0][0]}) {matches[0][1]}-{matches[0][2]}"
                    break
            
            # Look for company name in posting
            company_indicators = [
                'company:', 'employer:', 'organization:', 'firm:', 'business:'
            ]
            
            for indicator in company_indicators:
                pattern = rf'{indicator}\s*([^\n\r.]+)'
                match = re.search(pattern, details['fullDescription'], re.IGNORECASE)
                if match:
                    contact_info['company'] = match.group(1).strip()
                    break
            
            # Look for website URLs
            url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
            urls = re.findall(url_pattern, details['fullDescription'])
            if urls:
                # Filter out common non-company URLs
                filtered_urls = [url for url in urls if not any(domain in url.lower() for domain in ['craigslist', 'google', 'facebook', 'linkedin', 'indeed'])]
                if filtered_urls:
                    contact_info['website'] = filtered_urls[0]
            
            details['contactInfo'] = contact_info
            
            logger.info(f"Successfully extracted job details: {len(details['fullDescription'])} chars description, {len(contact_info)} contact fields")
            return details
            
        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            return None
    
    def send_to_server(self, jobs, server_url="http://localhost:3001/api/jobs/import"):
        """Send scraped jobs to Node.js server"""
        try:
            payload = {
                'jobs': jobs,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(server_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully sent {len(jobs)} jobs to server")
                return True
            else:
                logger.error(f"Failed to send jobs to server. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending jobs to server: {e}")
            return False

def main():
    """Main function to run the scraper"""
    scraper = JobScraper()
    
    try:
        # Scrape jobs from all sources - get all types of jobs
        jobs = scraper.scrape_all_sources("", "vancouver")
        
        if jobs:
            # Send to server
            success = scraper.send_to_server(jobs)
            if success:
                print(f"✅ Successfully scraped and sent {len(jobs)} jobs to server")
            else:
                print("❌ Failed to send jobs to server")
        else:
            print("❌ No jobs scraped")
            
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        scraper.close_selenium()

if __name__ == "__main__":
    main() 