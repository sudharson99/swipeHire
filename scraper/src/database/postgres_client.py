"""
PostgreSQL Database Client for SwipeHire Scraper
Direct database connection - no API issues
"""

import os
import uuid
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..utils.logger import setup_logger

class PostgresClient:
    def __init__(self):
        self.logger = setup_logger()
        
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL must be set")
        
        # Connect to PostgreSQL
        self.conn = psycopg2.connect(database_url)
        self.conn.autocommit = True
        
        self.logger.info("✅ Connected to PostgreSQL database")
        
        # Create tables if they don't exist
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables"""
        try:
            with self.conn.cursor() as cur:
                # Jobs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(500) NOT NULL,
                        company VARCHAR(200),
                        location VARCHAR(200),
                        city VARCHAR(100),
                        province VARCHAR(10),
                        description TEXT,
                        full_description TEXT,
                        job_url VARCHAR(1000) UNIQUE NOT NULL,
                        source_portal VARCHAR(50),
                        contact_email VARCHAR(200),
                        contact_phone VARCHAR(50),
                        posted_date TIMESTAMP,
                        job_type VARCHAR(50),
                        experience_level VARCHAR(50),
                        salary VARCHAR(200),
                        is_active BOOLEAN DEFAULT TRUE,
                        scraped_at TIMESTAMP DEFAULT NOW(),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Scraping logs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_logs (
                        id UUID PRIMARY KEY,
                        portal_name VARCHAR(100),
                        city VARCHAR(100),
                        scrape_started_at TIMESTAMP,
                        scrape_completed_at TIMESTAMP,
                        jobs_found INTEGER,
                        jobs_added INTEGER,
                        status VARCHAR(50),
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                self.logger.info("✅ Database tables ready")
                
        except Exception as e:
            self.logger.error(f"❌ Error creating tables: {str(e)}")

    def save_job(self, job_data: Dict) -> bool:
        """Save a job to the database"""
        try:
            with self.conn.cursor() as cur:
                # Check if job already exists
                cur.execute("SELECT id FROM jobs WHERE job_url = %s", (job_data['job_url'],))
                if cur.fetchone():
                    return False  # Job already exists
                
                # Insert new job
                insert_sql = """
                    INSERT INTO jobs (
                        title, company, location, city, province, description, 
                        full_description, job_url, source_portal, contact_email, 
                        contact_phone, posted_date, job_type, experience_level, salary
                    ) VALUES (
                        %(title)s, %(company)s, %(location)s, %(city)s, %(province)s, 
                        %(description)s, %(full_description)s, %(job_url)s, %(source_portal)s, 
                        %(contact_email)s, %(contact_phone)s, %(posted_date)s, %(job_type)s, 
                        %(experience_level)s, %(salary)s
                    )
                """
                
                cur.execute(insert_sql, job_data)
                self.logger.debug(f"✅ Saved job: {job_data['title']}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error saving job: {str(e)}")
            return False

    def log_scrape_start(self, portal_name: str, city: str) -> str:
        """Log the start of a scraping session"""
        try:
            log_id = str(uuid.uuid4())
            
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO scraping_logs (id, portal_name, city, scrape_started_at, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (log_id, portal_name, city, datetime.now(), 'running'))
            
            return log_id
            
        except Exception as e:
            self.logger.error(f"❌ Error logging scrape start: {str(e)}")
            return str(uuid.uuid4())

    def log_scrape_completion(self, log_id: str, jobs_found: int, jobs_added: int, 
                            status: str = 'completed', error_message: str = None) -> bool:
        """Log the completion of a scraping session"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE scraping_logs 
                    SET scrape_completed_at = %s, jobs_found = %s, jobs_added = %s, 
                        status = %s, error_message = %s
                    WHERE id = %s
                """, (datetime.now(), jobs_found, jobs_added, status, error_message, log_id))
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error logging scrape completion: {str(e)}")
            return False

    def cleanup_old_jobs(self, cutoff_date: datetime) -> int:
        """Mark old jobs as inactive"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs 
                    SET is_active = FALSE, updated_at = %s 
                    WHERE scraped_at < %s AND is_active = TRUE
                """, (datetime.now(), cutoff_date))
                
                count = cur.rowcount
                self.logger.info(f"🧹 Marked {count} old jobs as inactive")
                return count
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old jobs: {str(e)}")
            return 0

    def get_job_count(self) -> int:
        """Get total number of active jobs"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = TRUE")
                return cur.fetchone()[0]
        except:
            return 0

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()