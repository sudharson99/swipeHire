const express = require('express');
const { db } = require('../utils/database');
const { validateCity } = require('../middleware/validation');

const router = express.Router();

// Get jobs for swiping
router.get('/', validateCity, async (req, res) => {
  try {
    const { 
      city = 'vancouver', 
      limit = 100, 
      offset = 0,
      exclude_swiped = false,
      user_id = null 
    } = req.query;

    // Get jobs from database
    const jobs = await db.getJobs({ 
      city: city.toLowerCase(), 
      limit: parseInt(limit), 
      offset: parseInt(offset) 
    });

    // If user wants to exclude already swiped jobs and provides user_id
    let filteredJobs = jobs;
    if (exclude_swiped && user_id) {
      const userSwipes = await db.getUserSwipes(user_id);
      const swipedJobIds = userSwipes.map(swipe => swipe.job_id);
      filteredJobs = jobs.filter(job => !swipedJobIds.includes(job.id));
    }

    res.json({
      success: true,
      jobs: filteredJobs,
      total: filteredJobs.length,
      city: city,
      page: Math.floor(offset / limit) + 1,
      has_more: filteredJobs.length === parseInt(limit)
    });

  } catch (error) {
    console.error('Error fetching jobs:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch jobs',
      error: error.message
    });
  }
});

// Get single job details
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const job = await db.getJobById(id);

    if (!job) {
      return res.status(404).json({
        success: false,
        message: 'Job not found'
      });
    }

    res.json({
      success: true,
      job: job
    });

  } catch (error) {
    console.error('Error fetching job:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch job details',
      error: error.message
    });
  }
});

// Get jobs by city with stats
router.get('/city/:city', async (req, res) => {
  try {
    const { city } = req.params;
    const { limit = 100 } = req.query;

    const jobs = await db.getJobs({ 
      city: city.toLowerCase(), 
      limit: parseInt(limit) 
    });

    // Calculate job stats
    const stats = {
      total_jobs: jobs.length,
      sources: {},
      latest_scrape: null
    };

    jobs.forEach(job => {
      stats.sources[job.source_portal] = (stats.sources[job.source_portal] || 0) + 1;
      if (!stats.latest_scrape || job.scraped_at > stats.latest_scrape) {
        stats.latest_scrape = job.scraped_at;
      }
    });

    res.json({
      success: true,
      city: city,
      jobs: jobs,
      stats: stats
    });

  } catch (error) {
    console.error('Error fetching city jobs:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch jobs for city',
      error: error.message
    });
  }
});

// Search jobs
router.get('/search/:query', async (req, res) => {
  try {
    const { query } = req.params;
    const { city, limit = 50 } = req.query;

    // Basic search implementation (can be improved with full-text search)
    let jobs = await db.getJobs({ 
      city: city?.toLowerCase(), 
      limit: parseInt(limit) * 2 // Get more to filter
    });

    // Filter jobs that match search query
    const searchTerms = query.toLowerCase().split(' ');
    const filteredJobs = jobs.filter(job => {
      const searchText = `${job.title} ${job.company} ${job.description}`.toLowerCase();
      return searchTerms.some(term => searchText.includes(term));
    }).slice(0, parseInt(limit));

    res.json({
      success: true,
      query: query,
      jobs: filteredJobs,
      total: filteredJobs.length
    });

  } catch (error) {
    console.error('Error searching jobs:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to search jobs',
      error: error.message
    });
  }
});

module.exports = router;