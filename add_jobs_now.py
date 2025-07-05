#!/usr/bin/env python3
"""
Add test jobs to SwipeHire using the admin API endpoint
"""

import requests
import json
from datetime import datetime, timedelta

API_URL = "https://swipehire-api.onrender.com/api/jobs"
ADMIN_KEY = "swipehire-admin-2025"

# Realistic test jobs
jobs = [
    # Vancouver Jobs
    {
        "title": "Frontend Developer",
        "company": "TechVan Solutions",
        "location": "Downtown Vancouver",
        "city": "vancouver",
        "province": "BC",
        "description": "Build modern web applications using React, TypeScript, and Next.js. Join our growing team and work on exciting projects.",
        "full_description": "We're seeking a talented Frontend Developer to join our Vancouver team. You'll work with React, TypeScript, Next.js, and Tailwind CSS to create amazing user experiences. 2+ years experience required.",
        "job_url": "https://techvan.example.com/careers/frontend-dev",
        "source_portal": "manual",
        "job_type": "full-time",
        "experience_level": "mid",
        "salary": "$70,000 - $85,000",
        "contact_email": "careers@techvan.com"
    },
    {
        "title": "Coffee Shop Manager",
        "company": "Roast & Grind Cafe",
        "location": "Gastown, Vancouver",
        "city": "vancouver",
        "province": "BC",
        "description": "Manage daily operations of our busy coffee shop. Lead a team, handle inventory, and ensure exceptional customer service.",
        "full_description": "Looking for an experienced manager for our popular Gastown location. You'll oversee staff, manage inventory, handle scheduling, and maintain our high standards of coffee quality and customer service.",
        "job_url": "https://roastgrind.example.com/jobs/manager",
        "source_portal": "manual",
        "job_type": "full-time",
        "experience_level": "mid",
        "salary": "$45,000 - $55,000",
        "contact_phone": "(604) 555-0123"
    },
    {
        "title": "Marketing Assistant",
        "company": "Digital Wave Agency",
        "location": "Yaletown, Vancouver",
        "city": "vancouver",
        "province": "BC",
        "description": "Support our marketing team with social media, content creation, and campaign coordination. Perfect entry-level opportunity.",
        "full_description": "Join our creative marketing team! You'll help with social media management, content creation, email campaigns, and event coordination. Great for recent graduates looking to start their marketing career.",
        "job_url": "https://digitalwave.example.com/careers/marketing-assistant",
        "source_portal": "manual",
        "job_type": "full-time",
        "experience_level": "entry",
        "salary": "$40,000 - $50,000",
        "contact_email": "hr@digitalwave.com"
    },
    
    # Toronto Jobs
    {
        "title": "Data Analyst",
        "company": "FinTech Toronto",
        "location": "Financial District, Toronto",
        "city": "toronto",
        "province": "ON",
        "description": "Analyze financial data and create insights for investment decisions. Work with SQL, Python, and modern BI tools.",
        "full_description": "We're looking for a Data Analyst to join our fintech team. You'll work with large datasets, create reports and dashboards, and support investment decision-making. Strong SQL and Python skills required.",
        "job_url": "https://fintechto.example.com/jobs/data-analyst",
        "source_portal": "manual",
        "job_type": "full-time",
        "experience_level": "mid",
        "salary": "$65,000 - $80,000",
        "contact_email": "careers@fintechto.com"
    },
    {
        "title": "Graphic Designer",
        "company": "Creative Studio TO",
        "location": "King Street, Toronto",
        "city": "toronto",
        "province": "ON",
        "description": "Design visual content for diverse clients including branding, web design, and print materials. Adobe Creative Suite expertise required.",
        "full_description": "Join our award-winning design studio! You'll work on branding projects, website designs, and marketing materials for a variety of clients. Strong portfolio and Adobe Creative Suite skills essential.",
        "job_url": "https://creativestudioto.example.com/careers/designer",
        "source_portal": "manual",
        "job_type": "full-time",
        "experience_level": "mid",
        "salary": "$50,000 - $65,000",
        "contact_email": "jobs@creativestudioto.com"
    },
    
    # Calgary Jobs
    {
        "title": "Project Coordinator",
        "company": "Energy Solutions Inc",
        "location": "Downtown Calgary",
        "city": "calgary",
        "province": "AB",
        "description": "Coordinate engineering projects in the energy sector. Support project managers and ensure timely delivery of deliverables.",
        "full_description": "Support our project management team on energy infrastructure projects. You'll coordinate schedules, track progress, and communicate with stakeholders. Engineering background preferred but not required.",
        "job_url": "https://energysolutions.example.com/careers/coordinator",
        "source_portal": "manual",
        "job_type": "full-time",
        "experience_level": "entry",
        "salary": "$55,000 - $65,000",
        "contact_email": "hr@energysolutions.com"
    },
    {
        "title": "Restaurant Server",
        "company": "Prairie Steakhouse",
        "location": "Kensington, Calgary",
        "city": "calgary",
        "province": "AB",
        "description": "Provide excellent service in our upscale steakhouse. Evening shifts, great tips, and flexible scheduling available.",
        "full_description": "Join our team at Calgary's premier steakhouse! We're looking for friendly, professional servers who can provide exceptional dining experiences. Previous restaurant experience preferred. Great tip potential!",
        "job_url": "https://prairiesteakhouse.example.com/jobs/server",
        "source_portal": "manual",
        "job_type": "part-time",
        "experience_level": "entry",
        "salary": "$15/hour + tips",
        "contact_phone": "(403) 555-0456"
    }
]

def add_job(job_data):
    """Add a single job via API"""
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Key": ADMIN_KEY
    }
    
    try:
        response = requests.post(API_URL, json=job_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            result = response.json()
            return True, result.get('job', {}).get('id', 'unknown')
        else:
            return False, response.text
            
    except Exception as e:
        return False, str(e)

def main():
    """Add all test jobs"""
    print("🚀 Adding test jobs to SwipeHire database...")
    print(f"📡 API: {API_URL}")
    print(f"🔑 Using admin key: {ADMIN_KEY[:20]}...")
    print()
    
    success_count = 0
    
    for i, job in enumerate(jobs, 1):
        print(f"Adding {i}/{len(jobs)}: {job['title']} at {job['company']} ({job['city']})...")
        
        success, result = add_job(job)
        
        if success:
            print(f"  ✅ Added successfully (ID: {result})")
            success_count += 1
        else:
            print(f"  ❌ Failed: {result}")
        
        print()
    
    print(f"🎉 Complete! Added {success_count}/{len(jobs)} jobs")
    print()
    print("🔍 Test your API now:")
    print("  Vancouver: https://swipehire-api.onrender.com/api/jobs?city=vancouver")
    print("  Toronto:   https://swipehire-api.onrender.com/api/jobs?city=toronto")
    print("  Calgary:   https://swipehire-api.onrender.com/api/jobs?city=calgary")

if __name__ == "__main__":
    main()