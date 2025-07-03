-- SwipeHire Database Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(255) NOT NULL,
  company VARCHAR(255) NOT NULL,
  location VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  province VARCHAR(100) DEFAULT 'BC',
  salary VARCHAR(255),
  description TEXT NOT NULL,
  full_description TEXT,
  requirements TEXT,
  job_url TEXT,
  source_portal VARCHAR(100) NOT NULL, -- 'craigslist', 'indeed', etc.
  job_type VARCHAR(50), -- 'full-time', 'part-time', 'contract'
  experience_level VARCHAR(50), -- 'entry', 'mid', 'senior'
  contact_email VARCHAR(255),
  contact_phone VARCHAR(50),
  contact_company VARCHAR(255),
  posted_date TIMESTAMP,
  scraped_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  preferred_city VARCHAR(100) DEFAULT 'vancouver',
  resume_url TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- User swipes (after account creation)
CREATE TABLE IF NOT EXISTS user_swipes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  swipe_action VARCHAR(20) NOT NULL CHECK (swipe_action IN ('apply', 'pass', 'save')),
  swiped_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, job_id)
);

-- Anonymous swipes (before account creation)
CREATE TABLE IF NOT EXISTS anonymous_swipes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id VARCHAR(255) NOT NULL,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  swipe_action VARCHAR(20) NOT NULL CHECK (swipe_action IN ('apply', 'pass')),
  ip_address INET,
  swiped_at TIMESTAMP DEFAULT NOW()
);

-- Applications (when user applies to jobs)
CREATE TABLE IF NOT EXISTS applications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'viewed', 'rejected', 'interview')),
  resume_version TEXT,
  cover_letter TEXT,
  applied_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, job_id)
);

-- Scraping logs (monitor scraper health)
CREATE TABLE IF NOT EXISTS scraping_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  portal_name VARCHAR(100) NOT NULL,
  city VARCHAR(100) NOT NULL,
  jobs_found INTEGER DEFAULT 0,
  jobs_added INTEGER DEFAULT 0,
  scrape_started_at TIMESTAMP NOT NULL,
  scrape_completed_at TIMESTAMP,
  status VARCHAR(50) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source_portal);

CREATE INDEX IF NOT EXISTS idx_user_swipes_user_id ON user_swipes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_swipes_action ON user_swipes(swipe_action);

CREATE INDEX IF NOT EXISTS idx_anonymous_swipes_session ON anonymous_swipes(session_id);

CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_swipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

-- Users can only see their own swipes
CREATE POLICY "Users can view own swipes" ON user_swipes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own swipes" ON user_swipes FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only see their own applications
CREATE POLICY "Users can view own applications" ON applications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own applications" ON applications FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Jobs and anonymous swipes are public (no RLS needed)

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();