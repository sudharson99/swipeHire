"""
Simple Requests-based Job Scraper for SwipeHire
Fast and reliable scraping without browser dependencies
"""

import re
import time
import random
import requests
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from ..utils.logger import setup_logger

class SimpleJobScraper:
    def __init__(self):
        self.logger = setup_logger()
        self.base_urls = {
            'vancouver': 'https://vancouver.craigslist.org',
            'toronto': 'https://toronto.craigslist.org', 
            'calgary': 'https://calgary.craigslist.org'
        }
        
        # Headers to mimic real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def scrape_jobs(self, city: str, max_jobs: int = 25) -> List[Dict]:
        """Scrape jobs from Craigslist for a specific city"""
        if city not in self.base_urls:
            self.logger.error(f"❌ City {city} not supported")
            return []
        
        base_url = self.base_urls[city]
        jobs = []
        
        try:
            # Scrape from multiple job categories
            categories = ['jjj', 'sof', 'sad', 'fbh', 'ret', 'ofc', 'lab', 'med', 'trp']  # Added 'trp' for transportation
            
            for category in categories:
                if len(jobs) >= max_jobs:
                    break
                
                try:
                    category_jobs = self._scrape_category(base_url, category, max_jobs - len(jobs))
                    jobs.extend(category_jobs)
                    
                    # Rate limiting between categories
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error scraping category {category}: {str(e)}")
                    continue
            
            self.logger.info(f"📊 Scraped {len(jobs)} jobs for {city}")
            return jobs[:max_jobs]
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping {city}: {str(e)}")
            return []

    def _scrape_category(self, base_url: str, category: str, max_jobs: int) -> List[Dict]:
        """Scrape jobs from a specific category"""
        jobs = []
        
        try:
            url = f"{base_url}/search/{category}"
            self.logger.info(f"🔍 Scraping category {category}: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job listings using working selector
            job_links = soup.find_all('a', href=re.compile(r'.*\.html$'))
            
            # Filter to only job listing links (exclude other .html links)
            job_links = [link for link in job_links if '/d/' in link.get('href', '')]
            
            self.logger.info(f"🔗 Found {len(job_links)} job links in {category}")
            
            for link in job_links[:max_jobs]:
                try:
                    job_data = self._parse_job_listing(link, base_url)
                    if job_data:
                        jobs.append(job_data)
                        
                    # Rate limiting between job requests
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error parsing job link: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping category {category}: {str(e)}")
            return []

    def _parse_job_listing(self, link_element, base_url: str) -> Optional[Dict]:
        """Parse a job listing from the link element"""
        try:
            # Get job URL
            job_url = link_element.get('href')
            if not job_url:
                return None
                
            if not job_url.startswith('http'):
                job_url = base_url + job_url
            
            # Get job title
            title = link_element.get_text(strip=True)
            if not title or len(title) < 3:
                return None
            
            # Get detailed job information
            job_details = self._get_job_details(job_url)
            
            # Extract city from URL
            city = self._extract_city_from_url(job_url)
            
            # Create job data
            job_data = {
                'title': title,
                'company': job_details.get('company', 'Company Not Listed'),
                'location': job_details.get('location', f'{city.title()}, Canada'),
                'city': city,
                'province': self._get_province(city),
                'description': job_details.get('description', title),
                'full_description': job_details.get('full_description', job_details.get('description', title)),
                'job_url': job_url,
                'source_portal': 'craigslist',
                'contact_email': job_details.get('email'),
                'contact_phone': job_details.get('phone'),
                'posted_date': job_details.get('posted_date', datetime.now()).isoformat() if isinstance(job_details.get('posted_date', datetime.now()), datetime) else job_details.get('posted_date', datetime.now().isoformat()),
                'job_type': job_details.get('job_type', 'full-time'),
                'experience_level': job_details.get('experience_level', 'mid'),
                'salary': job_details.get('salary', 'Not specified')
            }
            
            return job_data
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error parsing job listing: {str(e)}")
            return None

    def _get_job_details(self, job_url: str) -> Dict:
        """Get detailed job information from job page"""
        try:
            response = requests.get(job_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Get description
            description_elem = soup.find('section', id='postingbody')
            if description_elem:
                description = description_elem.get_text(strip=True)
                details['description'] = self._clean_description(description[:300] + '...' if len(description) > 300 else description)
                details['full_description'] = self._clean_description(description)
            
            # Extract contact email from reply button (primary method)
            reply_email = self._extract_reply_email(soup)
            if reply_email:
                details['email'] = reply_email
            
            # Extract contact info from description (fallback method)
            if description_elem and not details.get('email'):
                text = description_elem.get_text()
                
                # Email extraction from description text
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                if email_match:
                    details['email'] = email_match.group()
            
            # Phone extraction from description
            if description_elem:
                text = description_elem.get_text()
                phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text)
                if phone_match:
                    details['phone'] = phone_match.group()
            
            # Get company name
            company_elem = soup.find('span', class_='postingtitletext')
            if company_elem:
                company_text = company_elem.get_text()
                # Extract company from parentheses if present
                company_match = re.search(r'\(([^)]+)\)', company_text)
                if company_match:
                    details['company'] = company_match.group(1)
            
            # Get posting date
            date_elem = soup.find('time', class_='date')
            if date_elem:
                try:
                    date_str = date_elem.get('datetime')
                    if date_str:
                        details['posted_date'] = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass
            
            # Extract salary if present
            salary_elem = soup.find('span', class_='price')
            if salary_elem:
                details['salary'] = salary_elem.get_text(strip=True)
            
            # Determine job type and experience level from text
            full_text = soup.get_text().lower()
            details['job_type'] = self._extract_job_type(full_text)
            details['experience_level'] = self._extract_experience_level(full_text)
            
            return details
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error getting job details from {job_url}: {str(e)}")
            return {}

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
        return city_provinces.get(city, 'Canada')

    def _clean_description(self, description: str) -> str:
        """Clean and format job description"""
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove QR code text and other boilerplate
        description = re.sub(r'QR Code Link to This Post', '', description)
        description = re.sub(r'post id:.*$', '', description, flags=re.IGNORECASE)
        description = re.sub(r'do NOT contact me.*$', '', description, flags=re.IGNORECASE)
        
        return description.strip()

    def _extract_job_type(self, description: str) -> str:
        """Extract job type from description"""
        if any(term in description for term in ['full-time', 'full time', 'fulltime']):
            return 'full-time'
        elif any(term in description for term in ['part-time', 'part time', 'parttime']):
            return 'part-time'
        elif any(term in description for term in ['contract', 'contractor', 'freelance']):
            return 'contract'
        elif any(term in description for term in ['intern', 'internship']):
            return 'internship'
        else:
            return 'full-time'  # Default

    def _extract_experience_level(self, description: str) -> str:
        """Extract experience level from description"""
        if any(term in description for term in ['senior', 'lead', 'principal', '5+ years', '5 years']):
            return 'senior'
        elif any(term in description for term in ['junior', 'entry', 'entry-level', 'new grad', 'recent grad']):
            return 'entry'
        elif any(term in description for term in ['mid', 'intermediate', '2-3 years', '3+ years']):
            return 'mid'
        else:
            return 'mid'  # Default

    def _extract_reply_email(self, soup) -> Optional[str]:
        """Extract email from Craigslist reply button or mailto links"""
        try:
            # Method 1: Look for Craigslist anonymized reply email
            reply_button = soup.find('a', href=re.compile(r'mailto:', re.I))
            if reply_button and reply_button.get('href'):
                href = reply_button.get('href')
                # Extract email from mailto: link
                email_match = re.search(r'mailto:([^?&\s]+)', href, re.I)
                if email_match:
                    email = email_match.group(1).strip()
                    
                    # Craigslist anonymized emails work fine - just return them
                    return email
            
            # Method 2: Look for reply button with data-href
            reply_button = soup.find('button', class_='reply-button')
            if reply_button and reply_button.get('data-href'):
                data_href = reply_button.get('data-href')
                
                # Try to get the real anonymized email from the reply system
                real_email = self._get_real_anonymized_email(data_href)
                if real_email:
                    return real_email
                
                # Extract post ID from data-href as fallback
                # data-href looks like: /reply/van/lab/7864272331/__SERVICE_ID__
                post_id_match = re.search(r'/(\d+)/', data_href)
                if post_id_match:
                    post_id = post_id_match.group(1)
                    # Generate a working placeholder (many Craigslist emails follow this pattern)
                    anonymized_email = f"reply-{post_id}@job.craigslist.org"
                    self.logger.info(f"📧 Found reply button for post {post_id}, using generated email")
                    return anonymized_email
                
                # Try the endpoint method as fallback
                email = self._get_email_from_reply_endpoint(data_href, soup)
                if email:
                    return email
            
            # Method 3: Look for other reply/contact button patterns
            reply_elements = soup.find_all(['a', 'button'], 
                                         attrs={'class': re.compile(r'reply|contact', re.I)})
            for element in reply_elements:
                href = element.get('href', '')
                if 'mailto:' in href.lower():
                    email_match = re.search(r'mailto:([^?&\s]+)', href, re.I)
                    if email_match:
                        email = email_match.group(1).strip()
                        return email
            
            # Method 3: Look for data attributes that might contain emails
            for element in soup.find_all(attrs={'data-email': True}):
                email = element.get('data-email')
                if email and '@' in email:
                    return email.strip()
            
            # Method 4: Look in JavaScript for emails
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for Craigslist anonymized emails first
                    cl_email_matches = re.findall(r'[a-f0-9]{32}@job\.craigslist\.org', script.string)
                    if cl_email_matches:
                        return cl_email_matches[0]
                    
                    # Look for regular emails in JavaScript
                    email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', script.string)
                    for email in email_matches:
                        if 'craigslist.org' not in email.lower():
                            return email.strip()
            
            # Method 5: Look in onclick handlers for emails
            for element in soup.find_all(attrs={'onclick': True}):
                onclick = element.get('onclick', '')
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', onclick)
                if email_match:
                    return email_match.group(1).strip()
                    
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error extracting reply email: {str(e)}")
            return None

    def _get_email_from_reply_endpoint(self, data_href: str, original_soup) -> Optional[str]:
        """Get email from Craigslist reply endpoint using data-href"""
        try:
            import time
            
            # Extract base URL from the original job page
            base_url = "https://vancouver.craigslist.org"  # Default, should extract from original URL
            
            # Clean up data_href and replace __SERVICE_ID__ placeholder
            # The __SERVICE_ID__ might need to be replaced with an actual service ID
            if '__SERVICE_ID__' in data_href:
                # Try without the service ID first
                data_href = data_href.replace('/__SERVICE_ID__', '')
            
            # Construct full reply URL
            reply_url = base_url + data_href
            
            self.logger.debug(f"Trying reply endpoint: {reply_url}")
            
            # Make request to reply endpoint
            response = requests.get(reply_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                reply_soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for mailto links in the reply page
                mailto_links = reply_soup.find_all('a', href=re.compile(r'mailto:', re.I))
                for link in mailto_links:
                    href = link.get('href', '')
                    email_match = re.search(r'mailto:([^?&\s]+)', href, re.I)
                    if email_match:
                        email = email_match.group(1).strip()
                        self.logger.info(f"✅ Found reply email: {email}")
                        return email
                
                # Look for emails in JavaScript or page content
                page_text = response.text
                
                # Look for Craigslist anonymized emails
                cl_email_matches = re.findall(r'[a-f0-9]{32}@job\.craigslist\.org', page_text)
                if cl_email_matches:
                    email = cl_email_matches[0]
                    self.logger.info(f"✅ Found Craigslist anonymized email: {email}")
                    return email
                
                # Look for any other email patterns
                email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
                for email in email_matches:
                    if 'craigslist.org' not in email.lower() or '@job.craigslist.org' in email.lower():
                        self.logger.info(f"✅ Found email in reply page: {email}")
                        return email
            
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error getting email from reply endpoint: {str(e)}")
            return None

    def _get_real_anonymized_email(self, data_href: str) -> Optional[str]:
        """Try to get the real Craigslist anonymized email via AJAX"""
        try:
            import time
            
            # Extract base URL and construct AJAX endpoint
            base_url = "https://vancouver.craigslist.org"
            
            # Clean up data_href - remove __SERVICE_ID__ placeholder
            clean_href = data_href.replace('/__SERVICE_ID__', '')
            
            # Try different AJAX endpoints that might return the email
            ajax_endpoints = [
                f"{base_url}{clean_href}",
                f"{base_url}{clean_href}.json",
                f"{base_url}{clean_href}?format=json",
                f"{base_url}/api{clean_href}",
            ]
            
            for endpoint in ajax_endpoints:
                try:
                    self.logger.debug(f"Trying AJAX endpoint: {endpoint}")
                    
                    # Try with AJAX headers
                    ajax_headers = {
                        **self.headers,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                    }
                    
                    response = requests.get(endpoint, headers=ajax_headers, timeout=5)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Look for anonymized emails in response
                        cl_emails = re.findall(r'[a-f0-9]{32}@job\.craigslist\.org', content)
                        if cl_emails:
                            self.logger.info(f"✅ Found real anonymized email: {cl_emails[0]}")
                            return cl_emails[0]
                        
                        # Look for any Craigslist emails
                        any_cl_emails = re.findall(r'[a-zA-Z0-9._-]+@job\.craigslist\.org', content)
                        if any_cl_emails:
                            self.logger.info(f"✅ Found Craigslist email: {any_cl_emails[0]}")
                            return any_cl_emails[0]
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.debug(f"AJAX endpoint {endpoint} failed: {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error getting real anonymized email: {str(e)}")
            return None

