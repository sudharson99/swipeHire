# SwipeHire Project Cleanup Instructions

## Files to KEEP:
```
swipeHire/
├── api/                    # ✅ Your working API backend
│   ├── src/               # API routes, middleware, utils
│   ├── package.json       # Dependencies
│   └── server.js          # Main server file
├── database/              # ✅ Database schema
│   └── schema.sql         # Supabase SQL schema
├── scraper/               # ✅ Job scraper (not deployed yet)
│   ├── src/               # Scraper code
│   ├── main.py            # Main scraper
│   └── requirements.txt   # Python dependencies
├── render.yaml            # ✅ Deployment config
└── README.md              # ✅ Documentation
```

## Files to DELETE:
```
❌ frontend/               # Empty folder
❌ src/                    # Duplicate of api/src/
❌ node_modules/           # Duplicate of api/node_modules/
❌ server.js               # Duplicate of api/server.js
❌ package.json            # Duplicate of api/package.json
❌ package-lock.json       # Duplicate of api/package-lock.json
❌ requirements.txt        # Duplicate of scraper/requirements.txt
❌ job_scraper.py          # Old prototype file
❌ run_scraper.py          # Old prototype file
❌ craigslist_debug.png    # Random image
❌ READ.ME                 # Duplicate README
❌ public/                 # Old prototype folder
❌ add_real_jobs.py        # Test script
❌ add_test_jobs.py        # Test script
❌ add_test_jobs_api.py    # Test script
```

## Current Status:
- ✅ **API**: Working at https://swipehire-api.onrender.com
- ✅ **Database**: Connected to Supabase
- ❌ **Jobs**: Database is empty (no jobs to show)
- ❌ **Frontend**: Not built yet

## Next Steps:
1. Clean up duplicate files
2. Add some jobs to test the system
3. Build simple frontend