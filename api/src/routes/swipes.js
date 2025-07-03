const express = require('express');
const { db } = require('../utils/database');
const { authMiddleware } = require('../middleware/auth');
const { validateSwipe } = require('../middleware/validation');

const router = express.Router();

// Track anonymous swipe (before user signup)
router.post('/anonymous', validateSwipe, async (req, res) => {
  try {
    const { job_id, swipe_action, session_id } = req.body;
    const ip_address = req.ip || req.connection.remoteAddress;

    const swipeData = {
      job_id,
      swipe_action, // 'apply' or 'pass'
      session_id,
      ip_address,
      swiped_at: new Date().toISOString()
    };

    const swipe = await db.createAnonymousSwipe(swipeData);

    res.status(201).json({
      success: true,
      message: 'Swipe recorded',
      swipe: swipe
    });

  } catch (error) {
    console.error('Error recording anonymous swipe:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to record swipe',
      error: error.message
    });
  }
});

// Track user swipe (after login)
router.post('/user', authMiddleware, validateSwipe, async (req, res) => {
  try {
    const { job_id, swipe_action } = req.body;
    const user_id = req.user.id;

    const swipeData = {
      user_id,
      job_id,
      swipe_action, // 'apply', 'pass', or 'save'
      swiped_at: new Date().toISOString()
    };

    const swipe = await db.createSwipe(swipeData);

    res.status(201).json({
      success: true,
      message: 'Swipe recorded',
      swipe: swipe
    });

  } catch (error) {
    console.error('Error recording user swipe:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to record swipe',
      error: error.message
    });
  }
});

// Get user's swipe history
router.get('/history', authMiddleware, async (req, res) => {
  try {
    const user_id = req.user.id;
    const { action, limit = 50 } = req.query;

    const swipes = await db.getUserSwipes(user_id, { 
      action, 
      limit: parseInt(limit) 
    });

    res.json({
      success: true,
      swipes: swipes,
      total: swipes.length
    });

  } catch (error) {
    console.error('Error fetching swipe history:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch swipe history',
      error: error.message
    });
  }
});

// Get user's liked jobs (apply swipes)
router.get('/liked', authMiddleware, async (req, res) => {
  try {
    const user_id = req.user.id;
    const { limit = 50 } = req.query;

    const likedSwipes = await db.getUserSwipes(user_id, { 
      action: 'apply', 
      limit: parseInt(limit) 
    });

    res.json({
      success: true,
      liked_jobs: likedSwipes,
      total: likedSwipes.length
    });

  } catch (error) {
    console.error('Error fetching liked jobs:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch liked jobs',
      error: error.message
    });
  }
});

// Get anonymous swipes by session
router.get('/anonymous/:session_id', async (req, res) => {
  try {
    const { session_id } = req.params;

    const swipes = await db.getAnonymousSwipes(session_id);

    // Count swipes by action
    const stats = {
      total: swipes.length,
      apply: swipes.filter(s => s.swipe_action === 'apply').length,
      pass: swipes.filter(s => s.swipe_action === 'pass').length
    };

    res.json({
      success: true,
      swipes: swipes,
      stats: stats
    });

  } catch (error) {
    console.error('Error fetching anonymous swipes:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch swipes',
      error: error.message
    });
  }
});

// Get swipe statistics for user
router.get('/stats', authMiddleware, async (req, res) => {
  try {
    const user_id = req.user.id;

    const allSwipes = await db.getUserSwipes(user_id, { limit: 1000 });

    const stats = {
      total_swipes: allSwipes.length,
      applications: allSwipes.filter(s => s.swipe_action === 'apply').length,
      passes: allSwipes.filter(s => s.swipe_action === 'pass').length,
      saves: allSwipes.filter(s => s.swipe_action === 'save').length,
      swipes_today: allSwipes.filter(s => {
        const today = new Date().toDateString();
        const swipeDate = new Date(s.swiped_at).toDateString();
        return today === swipeDate;
      }).length
    };

    res.json({
      success: true,
      stats: stats
    });

  } catch (error) {
    console.error('Error fetching swipe stats:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch statistics',
      error: error.message
    });
  }
});

module.exports = router;