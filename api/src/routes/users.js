const express = require('express');
const { db } = require('../utils/database');
const { authMiddleware } = require('../middleware/auth');

const router = express.Router();

// Get current user profile
router.get('/me', authMiddleware, async (req, res) => {
  try {
    const user = await db.getUserById(req.user.id);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }

    // Remove password from response
    const { password_hash: _, ...userResponse } = user;

    res.json({
      success: true,
      user: userResponse
    });

  } catch (error) {
    console.error('Error fetching user profile:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch user profile',
      error: error.message
    });
  }
});

// Update user profile
router.put('/me', authMiddleware, async (req, res) => {
  try {
    const { first_name, last_name, phone, preferred_city } = req.body;
    
    const updates = {};
    if (first_name) updates.first_name = first_name;
    if (last_name) updates.last_name = last_name;
    if (phone) updates.phone = phone;
    if (preferred_city) updates.preferred_city = preferred_city.toLowerCase();
    
    updates.updated_at = new Date().toISOString();

    const updatedUser = await db.updateUser(req.user.id, updates);
    
    // Remove password from response
    const { password_hash: _, ...userResponse } = updatedUser;

    res.json({
      success: true,
      message: 'Profile updated successfully',
      user: userResponse
    });

  } catch (error) {
    console.error('Error updating user profile:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to update profile',
      error: error.message
    });
  }
});

// Get user applications
router.get('/applications', authMiddleware, async (req, res) => {
  try {
    const applications = await db.getUserApplications(req.user.id);

    res.json({
      success: true,
      applications: applications,
      total: applications.length
    });

  } catch (error) {
    console.error('Error fetching user applications:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch applications',
      error: error.message
    });
  }
});

// Apply to jobs (bulk application from liked swipes)
router.post('/apply-bulk', authMiddleware, async (req, res) => {
  try {
    const { job_ids } = req.body;
    const user_id = req.user.id;

    if (!job_ids || !Array.isArray(job_ids) || job_ids.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Job IDs array is required'
      });
    }

    const applications = [];
    const errors = [];

    for (const job_id of job_ids) {
      try {
        const applicationData = {
          user_id,
          job_id,
          status: 'pending',
          applied_at: new Date().toISOString()
        };

        const application = await db.createApplication(applicationData);
        applications.push(application);
      } catch (error) {
        errors.push({ job_id, error: error.message });
      }
    }

    res.json({
      success: true,
      message: `Applied to ${applications.length} jobs`,
      applications: applications.length,
      errors: errors.length > 0 ? errors : undefined
    });

  } catch (error) {
    console.error('Error bulk applying to jobs:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to apply to jobs',
      error: error.message
    });
  }
});

// Apply to single job
router.post('/apply/:job_id', authMiddleware, async (req, res) => {
  try {
    const { job_id } = req.params;
    const user_id = req.user.id;

    // Check if already applied
    const existingApplications = await db.getUserApplications(user_id);
    const alreadyApplied = existingApplications.some(app => app.job_id === job_id);

    if (alreadyApplied) {
      return res.status(409).json({
        success: false,
        message: 'Already applied to this job'
      });
    }

    const applicationData = {
      user_id,
      job_id,
      status: 'pending',
      applied_at: new Date().toISOString()
    };

    const application = await db.createApplication(applicationData);

    res.status(201).json({
      success: true,
      message: 'Application submitted successfully',
      application: application
    });

  } catch (error) {
    console.error('Error applying to job:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to submit application',
      error: error.message
    });
  }
});

// Upload resume endpoint (placeholder - implement with file upload later)
router.post('/resume', authMiddleware, async (req, res) => {
  try {
    // This will be implemented with file upload middleware later
    res.json({
      success: true,
      message: 'Resume upload endpoint - coming soon',
      note: 'Will implement with multer and Supabase Storage'
    });

  } catch (error) {
    console.error('Error uploading resume:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to upload resume',
      error: error.message
    });
  }
});

module.exports = router;