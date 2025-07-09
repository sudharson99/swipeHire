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
            # Method 1: Look for reply button with mailto link
            reply_button = soup.find('a', href=re.compile(r'mailto:', re.I))
            if reply_button and reply_button.get('href'):
                href = reply_button.get('href')
                # Extract email from mailto: link
                email_match = re.search(r'mailto:([^?&\s]+)', href, re.I)
                if email_match:
                    return email_match.group(1).strip()
            
            # Method 2: Look for reply button class/id patterns
            reply_elements = soup.find_all(['a', 'button'], 
                                         attrs={'class': re.compile(r'reply|contact', re.I)})
            for element in reply_elements:
                href = element.get('href', '')
                if 'mailto:' in href.lower():
                    email_match = re.search(r'mailto:([^?&\s]+)', href, re.I)
                    if email_match:
                        return email_match.group(1).strip()
            
            # Method 3: Look for data attributes that might contain emails
            for element in soup.find_all(attrs={'data-email': True}):
                email = element.get('data-email')
                if email and '@' in email:
                    return email.strip()
            
            # Method 4: Look in onclick handlers or JavaScript for emails
            for element in soup.find_all(attrs={'onclick': True}):
                onclick = element.get('onclick', '')
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', onclick)
                if email_match:
                    return email_match.group(1).strip()
                    
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error extracting reply email: {str(e)}")
            return None