"""
Supabase Database Client for SwipeHire Scraper
Handles all database operations for job scraping
"""

import os
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client

from ..utils.logger import setup_logger

class SupabaseClient:
    def __init__(self):
        self.logger = setup_logger()
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.logger.info("✅ Connected to Supabase database")

    def save_job(self, job_data: Dict) -> bool:
        """Save a job to the database, avoiding duplicates"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Check if job already exists (by URL)
                existing = self.supabase.table('jobs').select('id').eq('job_url', job_data['job_url']).execute()
                
                if existing.data:
                    # Job already exists, skip
                    return False
                
                # Add timestamp
                job_data['scraped_at'] = datetime.now().isoformat()
                job_data['created_at'] = datetime.now().isoformat()
                job_data['updated_at'] = datetime.now().isoformat()
                job_data['is_active'] = True
                
                # Insert new job
                result = self.supabase.table('jobs').insert(job_data).execute()
                
                if result.data:
                    self.logger.debug(f"✅ Saved job: {job_data['title']}")
                    return True
                else:
                    self.logger.warning(f"⚠️  Failed to save job: {job_data['title']}")
                    return False
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"⚠️  Retry {attempt + 1} for job: {job_data.get('title', 'Unknown')} - {str(e)}")
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    self.logger.error(f"❌ Failed to save job after {max_retries} attempts: {str(e)}")
                    return False
        
        return False

    def log_scrape_start(self, portal_name: str, city: str) -> str:
        """Log the start of a scraping session"""
        try:
            log_data = {
                'id': str(uuid.uuid4()),
                'portal_name': portal_name,
                'city': city,
                'scrape_started_at': datetime.now().isoformat(),
                'status': 'running',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('scraping_logs').insert(log_data).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                self.logger.warning(f"⚠️  Failed to log scrape start for {city}")
                return str(uuid.uuid4())  # Return a dummy ID
                
        except Exception as e:
            self.logger.error(f"❌ Error logging scrape start: {str(e)}")
            return str(uuid.uuid4())  # Return a dummy ID

    def log_scrape_completion(self, log_id: str, jobs_found: int, jobs_added: int, 
                            status: str = 'completed', error_message: str = None) -> bool:
        """Log the completion of a scraping session"""
        try:
            update_data = {
                'scrape_completed_at': datetime.now().isoformat(),
                'jobs_found': jobs_found,
                'jobs_added': jobs_added,
                'status': status
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            result = self.supabase.table('scraping_logs').update(update_data).eq('id', log_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            self.logger.error(f"❌ Error logging scrape completion: {str(e)}")
            return False

    def cleanup_old_jobs(self, cutoff_date: datetime) -> int:
        """Remove jobs older than cutoff_date"""
        try:
            # Mark old jobs as inactive instead of deleting
            result = self.supabase.table('jobs').update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).lt('scraped_at', cutoff_date.isoformat()).execute()
            
            if result.data:
                count = len(result.data)
                self.logger.info(f"🧹 Marked {count} old jobs as inactive")
                return count
            else:
                return 0
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old jobs: {str(e)}")
            return 0

    def get_scraping_stats(self) -> Dict:
        """Get scraping statistics"""
        try:
            # Get total active jobs
            jobs_result = self.supabase.table('jobs').select('id').eq('is_active', True).execute()
            total_jobs = len(jobs_result.data) if jobs_result.data else 0
            
            # Get jobs by city
            cities = ['vancouver', 'toronto', 'calgary']
            city_stats = {}
            
            for city in cities:
                city_result = self.supabase.table('jobs').select('id').eq('city', city).eq('is_active', True).execute()
                city_stats[city] = len(city_result.data) if city_result.data else 0
            
            # Get recent scraping logs
            logs_result = self.supabase.table('scraping_logs').select('*').order('created_at', desc=True).limit(5).execute()
            recent_logs = logs_result.data if logs_result.data else []
            
            return {
                'total_active_jobs': total_jobs,
                'jobs_by_city': city_stats,
                'recent_scrapes': recent_logs,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting scraping stats: {str(e)}")
            return {
                'total_active_jobs': 0,
                'jobs_by_city': {},
                'recent_scrapes': [],
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            }