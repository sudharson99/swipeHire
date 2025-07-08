#!/usr/bin/env python3
"""
SwipeHire Job Scraper - Production Background Worker
Scrapes jobs from Craigslist and other portals, stores in Supabase
"""

import os
import time
import schedule
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

from src.scrapers.simple_scraper import SimpleJobScraper
from src.database.supabase_client import SupabaseClient
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

class JobScraperWorker:
    def __init__(self):
        self.logger = setup_logger()
        self.db = SupabaseClient()
        self.scrapers = {
            'craigslist': SimpleJobScraper()
        }
        
        # Configuration
        self.cities = os.getenv('CITIES', 'vancouver,toronto,calgary').split(',')
        self.scrape_interval = int(os.getenv('SCRAPE_INTERVAL_HOURS', '6'))
        self.max_jobs_per_city = int(os.getenv('MAX_JOBS_PER_CITY', '50'))
        
        self.logger.info(f"🚀 SwipeHire Scraper initialized")
        self.logger.info(f"📍 Cities: {self.cities}")
        self.logger.info(f"⏰ Interval: {self.scrape_interval} hours")

    def scrape_all_portals(self) -> None:
        """Scrape jobs from all portals for all cities"""
        self.logger.info("🔍 Starting job scraping cycle...")
        
        total_jobs_added = 0
        scrape_start = datetime.now()
        
        for city in self.cities:
            city = city.strip().lower()
            self.logger.info(f"🏙️  Scraping jobs for {city}...")
            
            # Log scraping start
            log_id = self.db.log_scrape_start('craigslist', city)
            
            try:
                # Scrape from Craigslist
                jobs = self.scrapers['craigslist'].scrape_jobs(
                    city=city,
                    max_jobs=self.max_jobs_per_city
                )
                
                # Save jobs to database in batches to avoid connection issues
                jobs_added = 0
                batch_size = 5
                
                for i in range(0, len(jobs), batch_size):
                    batch = jobs[i:i + batch_size]
                    batch_saved = self._save_job_batch(batch)
                    jobs_added += batch_saved
                    
                    # Wait between batches to avoid overwhelming connection
                    if i + batch_size < len(jobs):
                        time.sleep(5)
                
                total_jobs_added += jobs_added
                
                # Log successful completion
                self.db.log_scrape_completion(
                    log_id=log_id,
                    jobs_found=len(jobs),
                    jobs_added=jobs_added,
                    status='completed'
                )
                
                self.logger.info(f"✅ {city}: {jobs_added}/{len(jobs)} jobs added")
                
            except Exception as e:
                self.logger.error(f"❌ Error scraping {city}: {str(e)}")
                self.db.log_scrape_completion(
                    log_id=log_id,
                    jobs_found=0,
                    jobs_added=0,
                    status='failed',
                    error_message=str(e)
                )
        
        scrape_duration = datetime.now() - scrape_start
        self.logger.info(f"🎉 Scraping cycle completed! {total_jobs_added} total jobs added in {scrape_duration}")
        
        # Clean up old jobs (older than 30 days)
        self.cleanup_old_jobs()

    def _save_job_batch(self, jobs: List[Dict]) -> int:
        """Save a batch of jobs with better error handling"""
        saved_count = 0
        
        for job in jobs:
            try:
                if self.db.save_job(job):
                    saved_count += 1
                    self.logger.info(f"✅ Saved: {job['title'][:30]}...")
                
                # Small delay between individual saves
                time.sleep(1)
                
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to save job: {job.get('title', 'Unknown')[:30]} - {str(e)}")
                continue
        
        return saved_count
    
    def cleanup_old_jobs(self) -> None:
        """Remove jobs older than 30 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            deleted_count = self.db.cleanup_old_jobs(cutoff_date)
            if deleted_count > 0:
                self.logger.info(f"🧹 Cleaned up {deleted_count} old jobs")
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old jobs: {str(e)}")

    def run_scheduler(self) -> None:
        """Run the scheduler for continuous scraping"""
        # Schedule scraping every N hours
        schedule.every(self.scrape_interval).hours.do(self.scrape_all_portals)
        
        # Run initial scrape
        self.logger.info("🔄 Running initial scrape...")
        self.scrape_all_portals()
        
        # Keep the scheduler running
        self.logger.info(f"⏰ Scheduler started - will scrape every {self.scrape_interval} hours")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def run_once(self) -> None:
        """Run scraping once and exit"""
        self.logger.info("🔄 Running one-time scrape...")
        self.scrape_all_portals()
        self.logger.info("✅ One-time scrape completed")

def main():
    """Main entry point"""
    scraper = JobScraperWorker()
    
    # Check if running in one-time mode
    if os.getenv('RUN_ONCE', 'false').lower() == 'true':
        scraper.run_once()
    else:
        scraper.run_scheduler()

if __name__ == "__main__":
    main()