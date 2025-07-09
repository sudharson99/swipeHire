class SwipeHire {
    constructor() {
        this.jobs = [];
        this.currentJobIndex = 0;
        this.currentCity = 'vancouver';
        this.isLoading = false;
        this.apiUrl = 'https://swipehire-api.onrender.com/api';
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadJobs();
    }

    setupEventListeners() {
        // City selector
        document.getElementById('citySelect').addEventListener('change', (e) => {
            this.currentCity = e.target.value;
            this.currentJobIndex = 0;
            this.loadJobs();
        });

        // Action buttons
        document.getElementById('passBtn').addEventListener('click', () => this.swipeLeft());
        document.getElementById('applyBtn').addEventListener('click', () => this.swipeRight());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') this.swipeLeft();
            if (e.key === 'ArrowRight') this.swipeRight();
        });

        // Touch/mouse events for card swiping
        this.setupCardSwiping();
    }

    setupCardSwiping() {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        let card = null;

        const cardContainer = document.getElementById('cardContainer');

        const handleStart = (e) => {
            card = e.target.closest('.job-card');
            if (!card) return;

            isDragging = true;
            startX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX;
            card.classList.add('dragging');
        };

        const handleMove = (e) => {
            if (!isDragging || !card) return;

            currentX = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX;
            const deltaX = currentX - startX;
            const rotation = deltaX * 0.1;

            card.style.transform = `translateX(${deltaX}px) rotate(${rotation}deg)`;
            card.style.opacity = Math.max(0.5, 1 - Math.abs(deltaX) / 200);
        };

        const handleEnd = () => {
            if (!isDragging || !card) return;

            const deltaX = currentX - startX;
            const threshold = 100;

            if (Math.abs(deltaX) > threshold) {
                if (deltaX > 0) {
                    this.swipeRight();
                } else {
                    this.swipeLeft();
                }
            } else {
                // Snap back
                card.style.transform = 'translateX(0) rotate(0deg)';
                card.style.opacity = '1';
            }

            isDragging = false;
            card.classList.remove('dragging');
            card = null;
        };

        cardContainer.addEventListener('mousedown', handleStart);
        cardContainer.addEventListener('touchstart', handleStart);
        
        document.addEventListener('mousemove', handleMove);
        document.addEventListener('touchmove', handleMove);
        
        document.addEventListener('mouseup', handleEnd);
        document.addEventListener('touchend', handleEnd);
    }

    async loadJobs() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading();

        try {
            const response = await fetch(`${this.apiUrl}/jobs?city=${this.currentCity}&limit=20`);
            const data = await response.json();

            if (data.success) {
                this.jobs = data.jobs;
                this.currentJobIndex = 0;
                this.renderCurrentJob();
            } else {
                this.showError('Failed to load jobs');
            }
        } catch (error) {
            console.error('Error loading jobs:', error);
            this.showError('Failed to connect to server');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    renderCurrentJob() {
        const cardContainer = document.getElementById('cardContainer');
        const job = this.jobs[this.currentJobIndex];

        if (!job) {
            this.showNoJobs();
            return;
        }

        const jobCard = this.createJobCard(job);
        cardContainer.innerHTML = '';
        cardContainer.appendChild(jobCard);

        // Preload next job card
        if (this.currentJobIndex + 1 < this.jobs.length) {
            const nextJob = this.jobs[this.currentJobIndex + 1];
            const nextCard = this.createJobCard(nextJob);
            nextCard.style.zIndex = '-1';
            nextCard.style.transform = 'scale(0.95)';
            cardContainer.appendChild(nextCard);
        }
    }

    createJobCard(job) {
        const card = document.createElement('div');
        card.className = 'job-card';
        
        const salary = job.salary ? `<div class="job-salary">${job.salary}</div>` : '';
        const contact = this.createContactSection(job);
        
        card.innerHTML = `
            <div class="job-header">
                <div class="job-title">${job.title}</div>
                <div class="job-company">${job.company || 'Company not specified'}</div>
                <div class="job-location">${job.location}</div>
                ${salary}
            </div>
            
            <div class="job-description">
                ${job.description || 'No description available'}
            </div>
            
            <div class="job-meta">
                <span>📍 ${job.city}</span>
                <span>🏢 ${job.source_portal}</span>
                ${job.job_type ? `<span>💼 ${job.job_type}</span>` : ''}
                ${job.experience_level ? `<span>📈 ${job.experience_level}</span>` : ''}
            </div>
            
            ${contact}
        `;

        return card;
    }

    createContactSection(job) {
        const contacts = [];
        
        if (job.contact_email) {
            contacts.push(`<a href="mailto:${job.contact_email}">📧 Email</a>`);
        }
        
        if (job.contact_phone) {
            contacts.push(`<a href="tel:${job.contact_phone}">📞 ${job.contact_phone}</a>`);
        }
        
        if (job.job_url) {
            contacts.push(`<a href="${job.job_url}" target="_blank">🔗 View Original</a>`);
        }

        if (contacts.length > 0) {
            return `<div class="job-contact">${contacts.join('')}</div>`;
        }
        
        return '';
    }

    openEmailApplication(job) {
        const subject = encodeURIComponent(`Application for ${job.title} - ${job.company}`);
        const body = encodeURIComponent(`Dear Hiring Manager,

I am writing to express my interest in the ${job.title} position at ${job.company} that I found on your job posting.

${job.description ? 'I am particularly interested in this role because of the opportunity to ' + job.description.substring(0, 100) + '...' : 'I believe my skills and experience would be a great fit for this position.'}

I would welcome the opportunity to discuss how my background can contribute to your team. Please find my resume attached, and I look forward to hearing from you.

Best regards,
[Your Name]
[Your Phone Number]

---
Original Job Posting: ${job.job_url || 'N/A'}
Location: ${job.location}
${job.salary ? 'Salary: ' + job.salary : ''}
        `);

        const mailtoLink = `mailto:${job.contact_email}?subject=${subject}&body=${body}`;
        
        // Open email client
        window.open(mailtoLink, '_blank');
        
        // Log application for analytics
        console.log('📧 Email application opened for:', job.title, 'at', job.company);
        
        // Show success message
        this.showApplicationSuccess(job);
    }

    showApplicationSuccess(job) {
        // Create temporary success message
        const successMsg = document.createElement('div');
        successMsg.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #28a745;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 1000;
            font-weight: bold;
        `;
        successMsg.innerHTML = `✅ Email opened for ${job.title}!`;
        
        document.body.appendChild(successMsg);
        
        // Remove after 3 seconds
        setTimeout(() => {
            document.body.removeChild(successMsg);
        }, 3000);
    }

    swipeLeft() {
        this.performSwipe('left');
    }

    swipeRight() {
        const currentJob = this.jobs[this.currentJobIndex];
        if (currentJob && currentJob.contact_email) {
            this.openEmailApplication(currentJob);
        }
        this.performSwipe('right');
    }

    performSwipe(direction) {
        const card = document.querySelector('.job-card:not([style*="z-index: -1"])');
        if (!card) return;

        // Visual feedback
        card.classList.add(`swipe-${direction}`);
        
        // Log swipe (could be sent to API later)
        console.log(`Swiped ${direction} on job:`, this.jobs[this.currentJobIndex]?.title);

        // Move to next job after animation
        setTimeout(() => {
            this.currentJobIndex++;
            this.renderCurrentJob();
        }, 300);
    }

    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('cardContainer').style.display = 'none';
        document.getElementById('noJobs').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('cardContainer').style.display = 'block';
    }

    showNoJobs() {
        document.getElementById('cardContainer').style.display = 'none';
        document.getElementById('noJobs').style.display = 'block';
    }

    showError(message) {
        const cardContainer = document.getElementById('cardContainer');
        cardContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <h2>Error</h2>
                <p>${message}</p>
                <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    Retry
                </button>
            </div>
        `;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SwipeHire();
});