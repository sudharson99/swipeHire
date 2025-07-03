#!/usr/bin/env python3
"""
Simple script to run the job scraper
Usage: python run_scraper.py [search_term] [location]
"""

import sys
from job_scraper import JobScraper

def main():
    # Get command line arguments
    search_term = sys.argv[1] if len(sys.argv) > 1 else ""  # Empty string to get all jobs
    location = sys.argv[2] if len(sys.argv) > 2 else "vancouver"
    
    search_display = search_term if search_term else "all jobs"
    print(f"🔍 Scraping jobs for: '{search_display}' in '{location}'")
    
    scraper = JobScraper()
    
    try:
        # Scrape jobs from all sources
        jobs = scraper.scrape_all_sources(search_term, location)
        
        if jobs:
            # Send to server 
            success = scraper.send_to_server(jobs)
            if success:
                print(f"✅ Successfully scraped and sent {len(jobs)} jobs to server")
                print(f"📊 Jobs by source:")
                sources = {}
                for job in jobs:
                    source = job['source']
                    sources[source] = sources.get(source, 0) + 1
                for source, count in sources.items():
                    print(f"   {source}: {count} jobs")
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