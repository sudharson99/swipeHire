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

        cardContainer.addEventListener('mousedown', this.handleStart.bind(this));
        cardContainer.addEventListener('touchstart', this.handleStart.bind(this));
        
        document.addEventListener('mousemove', this.handleMove.bind(this));
        document.addEventListener('touchmove', this.handleMove.bind(this));
        
        document.addEventListener('mouseup', this.handleEnd.bind(this));
        document.addEventListener('touchend', this.handleEnd.bind(this));

        function handleStart(e) {
            card = e.target.closest('.job-card');
            if (!card) return;

            isDragging = true;
            startX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX;
            card.classList.add('dragging');
        }

        function handleMove(e) {
            if (!isDragging || !card) return;

            currentX = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX;
            const deltaX = currentX - startX;
            const rotation = deltaX * 0.1;

            card.style.transform = `translateX(${deltaX}px) rotate(${rotation}deg)`;
            card.style.opacity = Math.max(0.5, 1 - Math.abs(deltaX) / 200);
        }

        function handleEnd() {
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
        }

        // Bind methods to preserve 'this' context
        this.handleStart = handleStart.bind(this);
        this.handleMove = handleMove.bind(this);
        this.handleEnd = handleEnd.bind(this);
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

    swipeLeft() {
        this.performSwipe('left');
    }

    swipeRight() {
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