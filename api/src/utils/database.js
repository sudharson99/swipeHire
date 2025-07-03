const { createClient } = require('@supabase/supabase-js');

// Supabase configuration
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase environment variables');
}

// Create Supabase client
const supabase = createClient(supabaseUrl, supabaseKey);

// Database helper functions
const db = {
  // Jobs
  async getJobs(filters = {}) {
    const { city, limit = 100, offset = 0 } = filters;
    let query = supabase
      .from('jobs')
      .select('*')
      .eq('is_active', true)
      .order('scraped_at', { ascending: false });
    
    if (city) {
      query = query.eq('city', city);
    }
    
    const { data, error } = await query
      .range(offset, offset + limit - 1);
    
    if (error) throw error;
    return data;
  },

  async getJobById(id) {
    const { data, error } = await supabase
      .from('jobs')
      .select('*')
      .eq('id', id)
      .single();
    
    if (error) throw error;
    return data;
  },

  async createJob(jobData) {
    const { data, error } = await supabase
      .from('jobs')
      .insert([jobData])
      .select()
      .single();
    
    if (error) throw error;
    return data;
  },

  // Users
  async createUser(userData) {
    const { data, error } = await supabase
      .from('users')
      .insert([userData])
      .select()
      .single();
    
    if (error) throw error;
    return data;
  },

  async getUserByEmail(email) {
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('email', email)
      .single();
    
    if (error && error.code !== 'PGRST116') throw error;
    return data;
  },

  async getUserById(id) {
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', id)
      .single();
    
    if (error) throw error;
    return data;
  },

  async updateUser(id, updates) {
    const { data, error } = await supabase
      .from('users')
      .update(updates)
      .eq('id', id)
      .select()
      .single();
    
    if (error) throw error;
    return data;
  },

  // Swipes
  async createSwipe(swipeData) {
    const { data, error } = await supabase
      .from('user_swipes')
      .insert([swipeData])
      .select()
      .single();
    
    if (error) throw error;
    return data;
  },

  async getUserSwipes(userId, filters = {}) {
    const { action, limit = 50 } = filters;
    let query = supabase
      .from('user_swipes')
      .select(`
        *,
        jobs (
          id, title, company, location, salary, description
        )
      `)
      .eq('user_id', userId)
      .order('swiped_at', { ascending: false });
    
    if (action) {
      query = query.eq('swipe_action', action);
    }
    
    const { data, error } = await query.limit(limit);
    
    if (error) throw error;
    return data;
  },

  // Anonymous swipes
  async createAnonymousSwipe(swipeData) {
    const { data, error } = await supabase
      .from('anonymous_swipes')
      .insert([swipeData])
      .select()
      .single();
    
    if (error) throw error;
    return data;
  },

  async getAnonymousSwipes(sessionId) {
    const { data, error } = await supabase
      .from('anonymous_swipes')
      .select(`
        *,
        jobs (
          id, title, company, location, salary, description
        )
      `)
      .eq('session_id', sessionId)
      .order('swiped_at', { ascending: false });
    
    if (error) throw error;
    return data;
  },

  // Applications
  async createApplication(applicationData) {
    const { data, error } = await supabase
      .from('applications')
      .insert([applicationData])
      .select()
      .single();
    
    if (error) throw error;
    return data;
  },

  async getUserApplications(userId) {
    const { data, error } = await supabase
      .from('applications')
      .select(`
        *,
        jobs (
          id, title, company, location, salary
        )
      `)
      .eq('user_id', userId)
      .order('applied_at', { ascending: false });
    
    if (error) throw error;
    return data;
  }
};

module.exports = { supabase, db };