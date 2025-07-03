const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { db } = require('../utils/database');
const { validateSignup, validateLogin } = require('../middleware/validation');

const router = express.Router();

// JWT secret
const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production';

// Generate JWT token
const generateToken = (userId) => {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: '30d' });
};

// Signup endpoint
router.post('/signup', validateSignup, async (req, res) => {
  try {
    const { email, password, first_name, last_name, phone, preferred_city } = req.body;

    // Check if user already exists
    const existingUser = await db.getUserByEmail(email);
    if (existingUser) {
      return res.status(409).json({
        success: false,
        message: 'User with this email already exists'
      });
    }

    // Hash password
    const saltRounds = 12;
    const password_hash = await bcrypt.hash(password, saltRounds);

    // Create user
    const userData = {
      email,
      password_hash,
      first_name,
      last_name,
      phone,
      preferred_city: preferred_city?.toLowerCase() || 'vancouver',
      created_at: new Date().toISOString()
    };

    const user = await db.createUser(userData);

    // Generate token
    const token = generateToken(user.id);

    // Return user data without password
    const { password_hash: _, ...userResponse } = user;

    res.status(201).json({
      success: true,
      message: 'Account created successfully',
      user: userResponse,
      token: token
    });

  } catch (error) {
    console.error('Signup error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to create account',
      error: error.message
    });
  }
});

// Login endpoint
router.post('/login', validateLogin, async (req, res) => {
  try {
    const { email, password } = req.body;

    // Get user by email
    const user = await db.getUserByEmail(email);
    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'Invalid email or password'
      });
    }

    // Check password
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    if (!isValidPassword) {
      return res.status(401).json({
        success: false,
        message: 'Invalid email or password'
      });
    }

    // Generate token
    const token = generateToken(user.id);

    // Return user data without password
    const { password_hash: _, ...userResponse } = user;

    res.json({
      success: true,
      message: 'Login successful',
      user: userResponse,
      token: token
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to login',
      error: error.message
    });
  }
});

// Verify token endpoint
router.get('/verify', async (req, res) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'No token provided'
      });
    }

    // Verify JWT token
    const decoded = jwt.verify(token, JWT_SECRET);
    const user = await db.getUserById(decoded.userId);

    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'Invalid token'
      });
    }

    // Return user data without password
    const { password_hash: _, ...userResponse } = user;

    res.json({
      success: true,
      user: userResponse
    });

  } catch (error) {
    console.error('Token verification error:', error);
    res.status(401).json({
      success: false,
      message: 'Invalid or expired token'
    });
  }
});

// Convert anonymous swipes to user account
router.post('/convert-swipes', async (req, res) => {
  try {
    const { session_id, user_id } = req.body;

    if (!session_id || !user_id) {
      return res.status(400).json({
        success: false,
        message: 'Session ID and User ID are required'
      });
    }

    // Get anonymous swipes
    const anonymousSwipes = await db.getAnonymousSwipes(session_id);

    // Convert to user swipes
    const convertedSwipes = [];
    for (const swipe of anonymousSwipes) {
      const userSwipeData = {
        user_id: user_id,
        job_id: swipe.job_id,
        swipe_action: swipe.swipe_action,
        swiped_at: swipe.swiped_at
      };

      const convertedSwipe = await db.createSwipe(userSwipeData);
      convertedSwipes.push(convertedSwipe);
    }

    res.json({
      success: true,
      message: `Converted ${convertedSwipes.length} anonymous swipes to user account`,
      converted_swipes: convertedSwipes.length
    });

  } catch (error) {
    console.error('Error converting swipes:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to convert anonymous swipes',
      error: error.message
    });
  }
});

module.exports = router;