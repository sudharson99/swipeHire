# SwipeHire - Tinder for Jobs

A modern job search platform that lets users swipe through job opportunities in major Canadian cities.

## 🏗️ Project Structure

```
swipeHire/
├── api/                 # Node.js Backend API (Deploy to Render)
│   ├── src/
│   │   ├── routes/      # API endpoints
│   │   ├── middleware/  # Auth, validation, etc.
│   │   └── utils/       # Database, helpers
│   ├── server.js        # Main server file
│   └── package.json
├── scraper/            # Python Job Scraper (Deploy to Render Worker)
│   ├── src/
│   │   └── scrapers/   # Individual portal scrapers
│   └── requirements.txt
├── frontend/           # Next.js Frontend (Deploy to Vercel)
├── database/           # SQL schemas for Supabase
└── render.yaml         # Render deployment config
```

## 🚀 Quick Start

### 1. Set up Supabase Database

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Run the SQL from `database/schema.sql` in Supabase SQL editor
4. Get your project URL and anon key from Settings > API

### 2. Run API Locally

```bash
cd api
npm install
cp .env.example .env

# Edit .env with your Supabase credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your-anon-key

npm start
```

### 3. Test API Endpoints

```bash
# Health check
curl http://localhost:10000/health

# Get jobs for Vancouver
curl http://localhost:10000/api/jobs?city=vancouver

# Create test user
curl -X POST http://localhost:10000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "preferred_city": "vancouver"
  }'
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/signup` - Create user account
- `POST /api/auth/login` - User login
- `GET /api/auth/verify` - Verify JWT token
- `POST /api/auth/convert-swipes` - Convert anonymous swipes to user account

### Jobs
- `GET /api/jobs` - Get jobs (with city filter)
- `GET /api/jobs/:id` - Get single job details
- `GET /api/jobs/city/:city` - Get jobs by city with stats
- `GET /api/jobs/search/:query` - Search jobs

### Swipes
- `POST /api/swipes/anonymous` - Track anonymous swipe
- `POST /api/swipes/user` - Track user swipe (requires auth)
- `GET /api/swipes/history` - Get user swipe history (requires auth)
- `GET /api/swipes/liked` - Get user's liked jobs (requires auth)
- `GET /api/swipes/stats` - Get swipe statistics (requires auth)

### Users
- `GET /api/users/me` - Get current user profile (requires auth)
- `PUT /api/users/me` - Update user profile (requires auth)
- `GET /api/users/applications` - Get user applications (requires auth)
- `POST /api/users/apply-bulk` - Apply to multiple jobs (requires auth)
- `POST /api/users/apply/:job_id` - Apply to single job (requires auth)

## 🌍 Supported Cities

- Vancouver, BC
- Toronto, ON  
- Calgary, AB

## 💾 Database Tables

- `jobs` - Job postings from various portals
- `users` - User accounts and profiles
- `user_swipes` - User swipe history (after signup)
- `anonymous_swipes` - Anonymous swipes (before signup)
- `applications` - Job applications submitted
- `scraping_logs` - Scraper monitoring and health

## 🔧 Environment Variables

```env
NODE_ENV=production
PORT=10000
FRONTEND_URL=https://your-frontend.vercel.app
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
JWT_SECRET=your-super-secret-key
```

## 🚀 Deployment

### Deploy to Render

1. Connect your GitHub repo to Render
2. Create Web Service using `render.yaml`
3. Set environment variables in Render dashboard
4. Deploy!

### Frontend (Next.js on Vercel)

1. Create `frontend/` folder with Next.js app
2. Connect to Vercel
3. Set API_BASE_URL to your Render API URL
4. Deploy!

## 🔜 Next Steps

1. **Frontend Development** - Build Next.js swiping interface
2. **Scraper Service** - Create Python background worker
3. **Resume Upload** - Add file upload with Supabase Storage
4. **Email Notifications** - Notify users of application status
5. **Admin Dashboard** - Monitor jobs, users, applications

## 📈 MVP Features

✅ **User Authentication** - Signup, login, JWT tokens  
✅ **Anonymous Swiping** - Try before signup  
✅ **Job Management** - Store and serve job data  
✅ **Swipe Tracking** - Track user preferences  
✅ **Bulk Applications** - Apply to multiple jobs  
✅ **Multi-city Support** - Vancouver, Toronto, Calgary  

## 🛡️ Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting
- Input validation with Joi
- CORS protection
- Helmet security headers
- Row Level Security in Supabase

Ready to build the future of job searching! 🚀