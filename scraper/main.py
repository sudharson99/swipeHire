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
                
                # For now, save jobs to file and try database as backup
                jobs_added = 0
                
                # Save to JSON file as backup
                self._save_jobs_to_file(jobs, city)
                
                # Try to save to database (may fail on Render)
                for job in jobs:
                    try:
                        if self.db.save_job(job):
                            jobs_added += 1
                        time.sleep(0.5)  # Slower saves
                    except:
                        continue  # Skip failed saves silently
                
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

    def _save_jobs_to_file(self, jobs: List[Dict], city: str) -> None:
        """Save jobs to JSON file as backup"""
        try:
            import json
            filename = f"jobs_{city}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            
            with open(filename, 'w') as f:
                json.dump(jobs, f, indent=2, default=str)
            
            self.logger.info(f"📁 Saved {len(jobs)} jobs to {filename}")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to save jobs to file: {str(e)}")
    
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