// server.js - Simplified Node.js Backend for Job Management
const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// In-memory job storage (use database in production)
let jobsDatabase = [];
let seenJobIds = new Set(); // Track jobs that have been shown to user
let swipedJobIds = new Set(); // Track jobs that have been swiped (applied/passed)

// Job management functions
class JobManager {
    constructor() {
        this.jobs = [];
    }

    // Get mock jobs for testing
    getMockJobs(searchTerm = 'software developer', location = 'vancouver') {
        return [
            {
                id: 'mock_001',
                title: 'Senior Software Engineer',
                company: 'TechCorp Solutions',
                location: location || 'Vancouver, BC',
                salary: '$120,000 - $150,000 CAD',
                description: 'We are seeking a Senior Software Engineer to join our dynamic team. You will be responsible for developing scalable web applications and mentoring junior developers.',
                tags: ['JavaScript', 'React', 'Node.js', 'Remote', 'Full-time'],
                source: 'Mock Data',
                datePosted: new Date().toISOString()
            },
            {
                id: 'mock_002',
                title: 'Frontend Developer',
                company: 'Digital Innovations',
                location: location || 'Vancouver, BC',
                salary: '$90,000 - $120,000 CAD',
                description: 'Join our creative team as a Frontend Developer. Work with modern frameworks and create beautiful user experiences.',
                tags: ['React', 'Vue.js', 'CSS', 'UI/UX'],
                source: 'Mock Data',
                datePosted: new Date().toISOString()
            }
        ];
    }

    generateTags(title, description) {
        const content = `${title} ${description}`.toLowerCase();
        const tags = [];
        
        // Technology keywords
        const techKeywords = {
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
        };
        
        for (const [tag, keywords] of Object.entries(techKeywords)) {
            if (keywords.some(keyword => content.includes(keyword))) {
                tags.push(tag);
            }
        }
        
        return tags.slice(0, 6); // Limit to 6 tags
    }
}

const jobManager = new JobManager();

// API Routes
app.get('/api/jobs', async (req, res) => {
    try {
        const { search, location, source } = req.query;
        
        // Return ALL jobs but mark their swipe status
        // New jobs first, then swiped jobs
        const newJobs = jobsDatabase.filter(job => !swipedJobIds.has(job.id))
            .map(job => ({ ...job, swipeStatus: 'new' }));
        
        const swipedJobs = jobsDatabase.filter(job => swipedJobIds.has(job.id))
            .map(job => ({ ...job, swipeStatus: 'swiped' }));
        
        // Combine: new jobs first, then swiped jobs
        const allJobs = [...newJobs, ...swipedJobs];
        
        if (allJobs.length > 0) {
            console.log(`Returning ${allJobs.length} total jobs (${newJobs.length} new, ${swipedJobs.length} swiped)`);
            return res.json({
                success: true,
                jobs: allJobs,
                total: allJobs.length,
                newCount: newJobs.length,
                swipedCount: swipedJobs.length,
                source: 'all_with_status'
            });
        }
        
        // If no jobs in database, return empty
        console.log('No jobs in database');
        res.json({
            success: true,
            jobs: [],
            total: 0,
            source: 'empty',
            message: 'No jobs available. Click refresh to get fresh listings.'
        });
        
    } catch (error) {
        console.error('Error fetching jobs:', error);
        res.json({
            success: false,
            error: 'Failed to fetch jobs'
        });
    }
});

// Get jobs from database
app.get('/api/jobs/cached', (req, res) => {
    res.json({
        success: true,
        jobs: jobsDatabase,
        total: jobsDatabase.length
    });
});

// Apply to job endpoint
app.post('/api/jobs/:id/apply', (req, res) => {
    const { id } = req.params;
    const { userEmail, coverLetter } = req.body;
    
    // Mark job as swiped (applied)
    swipedJobIds.add(id);
    
    // In a real app, this would handle the application process
    console.log(`Application received for job ${id} from ${userEmail}`);
    
    res.json({
        success: true,
        message: 'Application submitted successfully!',
        applicationId: Math.random().toString(36).substr(2, 9)
    });
});

// Track swiped jobs endpoint
app.post('/api/jobs/:id/swipe', (req, res) => {
    const { id } = req.params;
    const { action } = req.body; // 'apply' or 'pass'
    
    // Mark job as swiped
    swipedJobIds.add(id);
    
    console.log(`Job ${id} swiped: ${action}`);
    
    res.json({
        success: true,
        message: `Job ${action === 'apply' ? 'applied to' : 'passed'} successfully`
    });
});

// Import jobs from Python scraper
app.post('/api/jobs/import', (req, res) => {
    try {
        const { jobs, timestamp } = req.body;
        
        if (!jobs || !Array.isArray(jobs)) {
            return res.status(400).json({
                success: false,
                error: 'Invalid jobs data'
            });
        }
        
        // Process and store the jobs
        const processedJobs = jobs.map(job => ({
            ...job,
            id: job.id || Math.random().toString(36).substr(2, 9),
            datePosted: job.datePosted || new Date().toISOString()
        }));
        
        // Replace the current job database with new jobs
        jobsDatabase = processedJobs;
        
        // Don't clear any tracking - let users see all new jobs
        // Swiped jobs will still be filtered out to avoid showing duplicates
        
        console.log(`✅ Imported ${processedJobs.length} jobs from Python scraper at ${timestamp}`);
        
        res.json({
            success: true,
            message: `Successfully imported ${processedJobs.length} jobs`,
            total: processedJobs.length,
            timestamp: timestamp
        });
        
    } catch (error) {
        console.error('Error importing jobs:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to import jobs'
        });
    }
});

// Search jobs endpoint
app.get('/api/jobs/search', async (req, res) => {
    const { query, location, salary_min, salary_max } = req.query;
    
    try {
        // This would typically query a database
        let filteredJobs = jobsDatabase;
        
        if (query) {
            filteredJobs = filteredJobs.filter(job => 
                job.title.toLowerCase().includes(query.toLowerCase()) ||
                job.description.toLowerCase().includes(query.toLowerCase()) ||
                job.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
            );
        }
        
        if (location) {
            filteredJobs = filteredJobs.filter(job => 
                job.location.toLowerCase().includes(location.toLowerCase())
            );
        }
        
        res.json({
            success: true,
            jobs: filteredJobs,
            total: filteredJobs.length
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: 'Search failed'
        });
    }
});

// Get detailed job information
app.get('/api/jobs/:id/details', async (req, res) => {
    try {
        const { id } = req.params;
        
        // Import child_process for running Python script
        const { spawn } = require('child_process');
        
        // Find the job in our database
        const job = jobsDatabase.find(j => j.id === id);
        
        if (!job || !job.link) {
            return res.status(404).json({
                success: false,
                error: 'Job not found or no link available'
            });
        }
        
        console.log(`Fetching detailed info for job: ${job.title}`);
        
        // Create a temporary Python script to get job details
        const pythonScript = `
import sys
sys.path.append('.')
from job_scraper import JobScraper

scraper = JobScraper()
try:
    details = scraper.get_job_details('${job.link}')
    if details:
        import json
        print(json.dumps(details))
    else:
        print('{}')
finally:
    scraper.close_selenium()
`;
        
        const pythonProcess = spawn('python3', ['-c', pythonScript], {
            stdio: ['pipe', 'pipe', 'pipe'],
            cwd: process.cwd()
        });
        
        let output = '';
        let errorOutput = '';
        
        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0 && output.trim()) {
                try {
                    const details = JSON.parse(output.trim());
                    res.json({
                        success: true,
                        job: {
                            ...job,
                            ...details
                        }
                    });
                } catch (e) {
                    console.error('Error parsing Python output:', e);
                    res.json({
                        success: true,
                        job: job,
                        error: 'Could not parse detailed information'
                    });
                }
            } else {
                console.error('Python script error:', errorOutput);
                res.json({
                    success: true,
                    job: job,
                    error: 'Could not fetch detailed information'
                });
            }
        });
        
        // Set a timeout
        setTimeout(() => {
            if (!pythonProcess.killed) {
                pythonProcess.kill();
                res.json({
                    success: true,
                    job: job,
                    error: 'Timeout fetching detailed information'
                });
            }
        }, 30000); // 30 second timeout
        
    } catch (error) {
        console.error('Error fetching job details:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch job details'
        });
    }
});

// Refresh jobs endpoint - triggers Python scraper
app.post('/api/jobs/refresh', async (req, res) => {
    try {
        console.log('🔄 Jobs refresh requested - triggering Python scraper...');
        
        // Import child_process for running Python script
        const { spawn } = require('child_process');
        
        // Start Python scraper
        const pythonProcess = spawn('python3', ['run_scraper.py'], {
            stdio: ['pipe', 'pipe', 'pipe']
        });
        
        let output = '';
        let errorOutput = '';
        
        // Collect output from Python script
        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
            console.log(`Python output: ${data}`);
        });
        
        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
            console.error(`Python error: ${data}`);
        });
        
        // Handle timeout
        const timeout = setTimeout(() => {
            if (!pythonProcess.killed) {
                pythonProcess.kill();
                if (!res.headersSent) {
                    res.status(408).json({
                        success: false,
                        error: 'Python scraper timed out'
                    });
                }
            }
        }, 60000); // 60 second timeout
        
        // Clear timeout when process completes
        pythonProcess.on('close', (code) => {
            clearTimeout(timeout);
            console.log(`Python scraper finished with code ${code}`);
            
            if (!res.headersSent) {
                if (code === 0) {
                    res.json({
                        success: true,
                        message: 'Python scraper completed successfully',
                        total: jobsDatabase.length,
                        jobs: jobsDatabase,
                        pythonOutput: output
                    });
                } else {
                    res.status(500).json({
                        success: false,
                        error: 'Python scraper failed',
                        pythonError: errorOutput,
                        pythonOutput: output
                    });
                }
            }
        });
        
    } catch (error) {
        console.error('Error refreshing jobs:', error);
        res.status(500).json({
            success: false,
            error: `Failed to refresh jobs: ${error.message}`
        });
    }
});

// Serve the frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Server error:', error);
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Job scraper server running on port ${PORT}`);
    console.log(`📱 Frontend: http://localhost:${PORT}`);
    console.log(`🔗 API: http://localhost:${PORT}/api/jobs`);
    console.log(`📥 Import endpoint: http://localhost:${PORT}/api/jobs/import`);
});

module.exports = app;