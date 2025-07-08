const { Pool } = require('pg');

// PostgreSQL configuration
const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error('Missing DATABASE_URL environment variable');
}

// Create PostgreSQL client
const pool = new Pool({
  connectionString: databaseUrl,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Database helper functions
const db = {
  // Jobs
  async getJobs(filters = {}) {
    const { city, limit = 100, offset = 0 } = filters;
    let query = 'SELECT * FROM jobs WHERE is_active = true';
    let params = [];
    
    if (city) {
      query += ' AND city = $1';
      params.push(city);
    }
    
    query += ' ORDER BY scraped_at DESC';
    query += ` LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);
    
    const result = await pool.query(query, params);
    return result.rows;
  },

  async getJobById(id) {
    const result = await pool.query('SELECT * FROM jobs WHERE id = $1', [id]);
    return result.rows[0];
  },

  async createJob(jobData) {
    const {
      title, company, location, city, province, description, full_description,
      job_url, source_portal, contact_email, contact_phone, posted_date,
      job_type, experience_level, salary, scraped_at, is_active = true
    } = jobData;
    
    const result = await pool.query(`
      INSERT INTO jobs (
        title, company, location, city, province, description, full_description,
        job_url, source_portal, contact_email, contact_phone, posted_date,
        job_type, experience_level, salary, scraped_at, is_active
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
      RETURNING *
    `, [
      title, company, location, city, province, description, full_description,
      job_url, source_portal, contact_email, contact_phone, posted_date,
      job_type, experience_level, salary, scraped_at, is_active
    ]);
    
    return result.rows[0];
  },

  // Users - simplified for now, can be expanded later
  async createUser(userData) {
    // For now, just return a placeholder - user auth can be added later
    return { id: 1, email: userData.email, ...userData };
  },

  async getUserByEmail(email) {
    // For now, just return a placeholder - user auth can be added later
    return { id: 1, email: email };
  },

  async getUserById(id) {
    // For now, just return a placeholder - user auth can be added later
    return { id: id };
  },

  async updateUser(id, updates) {
    // For now, just return a placeholder - user auth can be added later
    return { id: id, ...updates };
  },

  // Swipes - simplified for now, can be expanded later
  async createSwipe(swipeData) {
    // For now, just return a placeholder - swipe tracking can be added later
    return { id: 1, ...swipeData };
  },

  async getUserSwipes(userId, filters = {}) {
    // For now, just return empty array - swipe tracking can be added later
    return [];
  },

  // Anonymous swipes - simplified for now
  async createAnonymousSwipe(swipeData) {
    // For now, just return a placeholder - anonymous swipe tracking can be added later
    return { id: 1, ...swipeData };
  },

  async getAnonymousSwipes(sessionId) {
    // For now, just return empty array - anonymous swipe tracking can be added later
    return [];
  },

  // Applications - simplified for now
  async createApplication(applicationData) {
    // For now, just return a placeholder - application tracking can be added later
    return { id: 1, ...applicationData };
  },

  async getUserApplications(userId) {
    // For now, just return empty array - application tracking can be added later
    return [];
  }
};

module.exports = { pool, db };