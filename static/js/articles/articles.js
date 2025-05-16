/**
 * Articles Page JavaScript
 * 
 * This script handles all functionality for the Articles page including:
 * - Loading featured, recommended, and all articles
 * - Filtering articles by category
 * - Implementing search functionality
 * - Displaying article modals
 * - Newsletter subscription
 * - Pagination
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const featuredArticlesContainer = document.getElementById('featuredArticlesContainer');
    const recommendedArticlesContainer = document.getElementById('recommendedArticlesContainer');
    const allArticlesContainer = document.getElementById('allArticlesContainer');
    const articlesPagination = document.getElementById('articlesPagination');
    const categoriesContainer = document.getElementById('categoriesContainer');
    const articleSearch = document.getElementById('articleSearch');
    const articlesSort = document.getElementById('articlesSort');
    const newsletterForm = document.getElementById('newsletterForm');
    const articleModal = document.getElementById('articleModal');
    const modalContent = document.getElementById('modalContent');
    
    // State management
    let articles = [];
    let featuredArticles = [];
    let recommendedArticles = [];
    let categories = [];
    let currentPage = 1;
    let totalPages = 1;
    let currentCategory = 'all';
    let currentSort = 'newest';
    let searchQuery = '';
    
    // Check URL for category parameter
    const urlParams = new URLSearchParams(window.location.search);
    const categoryParam = urlParams.get('category');
    if (categoryParam) {
      currentCategory = categoryParam;
    }
    
    // Initialize
    init();
    
    /**
     * Initialize the page
     */
    async function init() {
      try {
        // Load categories first
        await loadCategories();
        
        // Load all article types in parallel
        await Promise.all([
          loadFeaturedArticles(),
          loadRecommendedArticles(),
          loadAllArticles()
        ]);
        
        // Set up event listeners
        setupEventListeners();
        
        // If category param was in URL, select it
        if (categoryParam) {
          selectCategory(categoryParam);
        }
      } catch (error) {
        console.error('Error initializing articles page:', error);
        showError('There was an error loading articles. Please try again later.');
      }
    }
    
    /**
     * Load article categories
     */
    async function loadCategories() {
      try {
        const response = await fetch('/api/articles/categories');
        
        if (!response.ok) {
          throw new Error('Failed to load categories');
        }
        
        categories = await response.json();
        renderCategories();
      } catch (error) {
        console.error('Error loading categories:', error);
        // Use default categories as fallback
        categories = [
          { id: 'resume-tips', name: 'Resume Tips' },
          { id: 'cover-letters', name: 'Cover Letters' },
          { id: 'job-search', name: 'Job Search' },
          { id: 'interviews', name: 'Interviews' },
          { id: 'career-advice', name: 'Career Advice' }
        ];
        renderCategories();
      }
    }
    
    /**
     * Render categories in the filter bar
     */
    function renderCategories() {
      // Keep the "All" button
      const allButton = categoriesContainer.querySelector('.category-pill[data-category="all"]');
      
      // Clear existing categories except "All"
      categoriesContainer.innerHTML = '';
      
      // Re-add the "All" button
      categoriesContainer.appendChild(allButton);
      
      // Add each category
      categories.forEach(category => {
        const categoryButton = document.createElement('button');
        categoryButton.className = 'category-pill';
        categoryButton.setAttribute('data-category', category.id);
        categoryButton.textContent = category.name;
        
        if (category.id === currentCategory) {
          categoryButton.classList.add('active');
          allButton.classList.remove('active');
        }
        
        categoriesContainer.appendChild(categoryButton);
      });
    }
    
    /**
     * Load featured articles
     */
    async function loadFeaturedArticles() {
      try {
        featuredArticlesContainer.innerHTML = '<div class="articles-loading">Loading featured articles...</div>';
        
        const response = await fetch('/api/articles/featured');
        
        if (!response.ok) {
          throw new Error('Failed to load featured articles');
        }
        
        featuredArticles = await response.json();
        renderFeaturedArticles();
      } catch (error) {
        console.error('Error loading featured articles:', error);
        featuredArticlesContainer.innerHTML = '<p class="text-center">Could not load featured articles. Please try again later.</p>';
        
        // Use sample data as fallback
        featuredArticles = getSampleArticles(3, true);
        renderFeaturedArticles();
      }
    }
    
    /**
     * Render featured articles
     */
    function renderFeaturedArticles() {
      featuredArticlesContainer.innerHTML = '';
      
      featuredArticles.forEach(article => {
        const articleCard = createArticleCard(article);
        featuredArticlesContainer.appendChild(articleCard);
      });
      
      // Add slider controls if needed
      if (featuredArticles.length > 3) {
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'featured-controls';
        controlsDiv.innerHTML = `
          <button class="featured-control prev-button">
            <i aria-hidden="true">←</i>
          </button>
          <button class="featured-control next-button">
            <i aria-hidden="true">→</i>
          </button>
        `;
        
        featuredArticlesContainer.parentNode.appendChild(controlsDiv);
        
        // Set up slider controls
        const prevButton = controlsDiv.querySelector('.prev-button');
        const nextButton = controlsDiv.querySelector('.next-button');
        
        prevButton.addEventListener('click', () => {
          featuredArticlesContainer.scrollBy({ left: -300, behavior: 'smooth' });
        });
        
        nextButton.addEventListener('click', () => {
          featuredArticlesContainer.scrollBy({ left: 300, behavior: 'smooth' });
        });
      }
    }
    
    /**
     * Load recommended articles
     */
    async function loadRecommendedArticles() {
      try {
        recommendedArticlesContainer.innerHTML = '<div class="articles-loading">Loading recommended articles...</div>';
        
        const response = await fetch('/api/articles/user_recommended_articles');
        
        if (!response.ok) {
          throw new Error('Failed to load recommended articles');
        }
        
        recommendedArticles = await response.json();
        renderRecommendedArticles();
      } catch (error) {
        console.error('Error loading recommended articles:', error);
        recommendedArticlesContainer.innerHTML = '<p class="text-center">Could not load recommendations. Please try again later.</p>';
        
        // Use sample data as fallback
        recommendedArticles = getSampleArticles(6);
        renderRecommendedArticles();
      }
    }
    
    /**
     * Render recommended articles
     */
    function renderRecommendedArticles() {
      recommendedArticlesContainer.innerHTML = '';
      
      if (recommendedArticles.length === 0) {
        recommendedArticlesContainer.innerHTML = '<p class="text-center">No recommendations available yet. Add more details to your CV to get personalized recommendations.</p>';
        return;
      }
      
      recommendedArticles.forEach(article => {
        const articleCard = createArticleCard(article);
        recommendedArticlesContainer.appendChild(articleCard);
      });
    }
    
    /**
     * Load all articles with pagination
     */
    async function loadAllArticles() {
      try {
        allArticlesContainer.innerHTML = '<div class="articles-loading">Loading articles...</div>';
        
        const apiUrl = new URL('/api/articles', window.location.origin);
        apiUrl.searchParams.append('page', currentPage);
        apiUrl.searchParams.append('sort', currentSort);
        
        if (currentCategory !== 'all') {
          apiUrl.searchParams.append('category', currentCategory);
        }
        
        if (searchQuery) {
          apiUrl.searchParams.append('search', searchQuery);
        }
        
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
          throw new Error('Failed to load articles');
        }
        
        const data = await response.json();
        articles = data.articles;
        totalPages = data.totalPages || 1;
        currentPage = data.currentPage || 1;
        
        renderAllArticles();
        renderPagination();
      } catch (error) {
        console.error('Error loading all articles:', error);
        allArticlesContainer.innerHTML = '<p class="text-center">Could not load articles. Please try again later.</p>';
        
        // Use sample data as fallback
        articles = getSampleArticles(9);
        renderAllArticles();
        
        // Generate sample pagination
        totalPages = 3;
        renderPagination();
      }
    }
    
    /**
     * Render all articles
     */
    function renderAllArticles() {
      allArticlesContainer.innerHTML = '';
      
      if (articles.length === 0) {
        allArticlesContainer.innerHTML = '<p class="text-center">No articles found matching your criteria.</p>';
        return;
      }
      
      articles.forEach(article => {
        const articleCard = createArticleCard(article);
        allArticlesContainer.appendChild(articleCard);
      });
    }
    
    /**
     * Render pagination controls
     */
    function renderPagination() {
      articlesPagination.innerHTML = '';
      
      if (totalPages <= 1) {
        return;
      }
      
      // Previous button
      if (currentPage > 1) {
        const prevButton = document.createElement('div');
        prevButton.className = 'pagination-item';
        prevButton.innerHTML = '<i aria-hidden="true">←</i>';
        prevButton.addEventListener('click', () => changePage(currentPage - 1));
        articlesPagination.appendChild(prevButton);
      }
      
      // Page numbers - simplified pagination with max 5 buttons
      const startPage = Math.max(1, currentPage - 2);
      const endPage = Math.min(totalPages, startPage + 4);
      
      for (let i = startPage; i <= endPage; i++) {
        const pageButton = document.createElement('div');
        pageButton.className = 'pagination-item';
        pageButton.textContent = i;
        
        if (i === currentPage) {
          pageButton.classList.add('active');
        }
        
        pageButton.addEventListener('click', () => changePage(i));
        articlesPagination.appendChild(pageButton);
      }
      
      // Next button
      if (currentPage < totalPages) {
        const nextButton = document.createElement('div');
        nextButton.className = 'pagination-item';
        nextButton.innerHTML = '<i aria-hidden="true">→</i>';
        nextButton.addEventListener('click', () => changePage(currentPage + 1));
        articlesPagination.appendChild(nextButton);
      }
    }
    
    /**
     * Change current page and reload articles
     */
    function changePage(page) {
      currentPage = page;
      loadAllArticles();
      
      // Scroll to articles section
      document.getElementById('all-articles').scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Create an article card element
     */
    function createArticleCard(article) {
      const template = document.getElementById('articleCardTemplate');
      const card = document.importNode(template.content, true).querySelector('.article-card');
      
      // Set card data
      card.querySelector('.article-category').textContent = getCategoryName(article.category);
      card.querySelector('.article-image').src = article.imageUrl || '/api/placeholder/400/200';
      card.querySelector('.article-image').alt = article.title;
      card.querySelector('.article-title').textContent = article.title;
      card.querySelector('.article-excerpt').textContent = article.excerpt;
      card.querySelector('.article-date').innerHTML = `<i aria-hidden="true">📅</i> ${formatDate(article.publishedAt)}`;
      card.querySelector('.article-read-time').innerHTML = `<i aria-hidden="true">⏱️</i> ${article.readTime || '5 min read'}`;
      
      // Store article data for modal
      card.setAttribute('data-article-id', article.id);
      
      // Add click event
      card.addEventListener('click', () => openArticleModal(article));
      
      return card;
    }
    
    /**
     * Get category name from ID
     */
    function getCategoryName(categoryId) {
      const category = categories.find(cat => cat.id === categoryId);
      return category ? category.name : categoryId;
    }
    
    /**
     * Format date for display
     */
    function formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    }
    
    /**
     * Open article modal
     */
    function openArticleModal(article) {
      // Update browser history
      const articleUrl = `/articles/article?articleId=${article.id}&source=article_card`;
      history.pushState({ articleId: article.id }, article.title, articleUrl);
      
      // Create modal content
      modalContent.innerHTML = `
        <div class="modal-article-header">
          <div class="modal-article-category">${getCategoryName(article.category)}</div>
          <h2 class="modal-article-title">${article.title}</h2>
          <div class="modal-article-meta">
            <div class="modal-article-author">
              <img src="${article.author?.avatar || '/api/placeholder/40/40'}" class="author-avatar" alt="Author">
              <span class="author-name">${article.author?.name || 'CVFlow Team'}</span>
            </div>
            <div class="article-date">
              <i aria-hidden="true">📅</i> ${formatDate(article.publishedAt)}
            </div>
            <div class="article-read-time">
              <i aria-hidden="true">⏱️</i> ${article.readTime || '5 min read'}
            </div>
          </div>
        </div>
        
        <img src="${article.imageUrl || '/api/placeholder/900/400'}" alt="${article.title}" class="modal-article-image">
        
        <div class="modal-article-content">
          ${article.content || `<p>${article.excerpt}</p><p>This is a placeholder article content. In the real implementation, this would be replaced with the actual article content fetched from the server.</p><p>The article would include detailed text, possibly with headers, images, and formatting to provide value to the reader.</p>`}
        </div>
        
        <div class="article-tags">
          ${renderTags(article.tags)}
        </div>
        
        <h3 class="related-articles-title">Related Articles</h3>
        <div class="related-articles" id="relatedArticles">
          <div class="articles-loading">Loading related articles...</div>
        </div>
      `;
      
      // Show modal
      articleModal.style.display = 'block';
      document.body.style.overflow = 'hidden'; // Prevent scrolling
      
      // Load related articles
      loadRelatedArticles(article.id);
    }
    
    /**
     * Close article modal
     */
    function closeArticleModal() {
      articleModal.style.display = 'none';
      document.body.style.overflow = 'auto'; // Re-enable scrolling
      
      // Restore original URL
      history.pushState({}, document.title, '/articles');
    }
    
    /**
     * Load related articles
     */
    async function loadRelatedArticles(articleId) {
      const relatedArticlesContainer = document.getElementById('relatedArticles');
      
      try {
        const response = await fetch(`/api/articles/${articleId}/related`);
        
        if (!response.ok) {
          throw new Error('Failed to load related articles');
        }
        
        const relatedArticles = await response.json();
        
        relatedArticlesContainer.innerHTML = '';
        
        if (relatedArticles.length === 0) {
          relatedArticlesContainer.innerHTML = '<p>No related articles found.</p>';
          return;
        }
        
        relatedArticles.forEach(article => {
          const articleCard = createArticleCard(article);
          relatedArticlesContainer.appendChild(articleCard);
        });
      } catch (error) {
        console.error('Error loading related articles:', error);
        
        // Use sample data as fallback
        const relatedArticles = getSampleArticles(3);
        relatedArticlesContainer.innerHTML = '';
        
        relatedArticles.forEach(article => {
          const articleCard = createArticleCard(article);
          relatedArticlesContainer.appendChild(articleCard);
        });
      }
    }
    
    /**
     * Render article tags
     */
    function renderTags(tags = []) {
      if (!tags || tags.length === 0) {
        tags = ['CV Tips', 'Resume', 'Job Search'];
      }
      
      return tags.map(tag => `<span class="article-tag">${tag}</span>`).join('');
    }
    
    /**
     * Show error message
     */
    function showError(message) {
      const errorAlert = document.createElement('div');
      errorAlert.className = 'alert-error';
      errorAlert.textContent = message;
      
      document.body.insertBefore(errorAlert, document.body.firstChild);
      
      setTimeout(() => {
        errorAlert.classList.add('fade-out');
        setTimeout(() => errorAlert.remove(), 500);
      }, 3000);
    }
    
    /**
     * Filter articles by category
     */
    function selectCategory(categoryId) {
      currentCategory = categoryId;
      currentPage = 1;
      
      // Update URL
      const url = new URL(window.location);
      if (categoryId === 'all') {
        url.searchParams.delete('category');
      } else {
        url.searchParams.set('category', categoryId);
      }
      history.pushState({}, '', url);
      
      // Update UI
      const categoryButtons = categoriesContainer.querySelectorAll('.category-pill');
      categoryButtons.forEach(button => {
        if (button.getAttribute('data-category') === categoryId) {
          button.classList.add('active');
        } else {
          button.classList.remove('active');
        }
      });
      
      // Reload articles
      loadAllArticles();
    }
    
    /**
     * Setup event listeners
     */
    function setupEventListeners() {
      // Category filter
      categoriesContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('category-pill')) {
          const category = e.target.getAttribute('data-category');
          selectCategory(category);
        }
      });
      
      // Search
      let searchTimeout;
      articleSearch.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          searchQuery = e.target.value.trim();
          currentPage = 1;
          loadAllArticles();
        }, 300);
      });
      
      // Sort
      articlesSort.addEventListener('change', (e) => {
        currentSort = e.target.value;
        currentPage = 1;
        loadAllArticles();
      });
      
      // Newsletter form
      newsletterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = newsletterForm.querySelector('input[type="email"]').value;
        
        // Submit to API
        fetch('/api/newsletter/subscribe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email }),
        })
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to subscribe');
          }
          return response.json();
        })
        .then(data => {
          // Show success message
          newsletterForm.innerHTML = '<p class="success-message">Thanks for subscribing! Check your email for confirmation.</p>';
        })
        .catch(error => {
          console.error('Error subscribing to newsletter:', error);
          showError('Failed to subscribe. Please try again later.');
        });
      });
      
      // Modal close button
      const closeModalButton = document.querySelector('.close-modal');
      closeModalButton.addEventListener('click', closeArticleModal);
      
      // Close modal when clicking outside
      articleModal.addEventListener('click', (e) => {
        if (e.target === articleModal) {
          closeArticleModal();
        }
      });
      
      // Handle escape key press for modal
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && articleModal.style.display === 'block') {
          closeArticleModal();
        }
      });
      
      // Handle browser back button
      window.addEventListener('popstate', (e) => {
        if (articleModal.style.display === 'block') {
          closeArticleModal();
        }
      });
    }
    
    /**
     * Get sample articles for fallback
     */
    function getSampleArticles(count = 6, featured = false) {
      const sampleArticles = [
        {
          id: '1',
          title: 'Top 10 Resume Mistakes to Avoid in 2025',
          excerpt: 'Learn about the most common resume mistakes that can cost you job opportunities and how to fix them effectively.',
          category: 'resume-tips',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-01-15T00:00:00Z',
          readTime: '5 min read',
          author: {
            name: 'Sarah Johnson',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['Resume Tips', 'Job Search', 'Career Advice']
        },
        {
          id: '2',
          title: 'AI Skills That Will Boost Your CV in 2025',
          excerpt: 'Discover the AI skills that employers are looking for and how to showcase them effectively on your resume.',
          category: 'career-advice',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-02-03T00:00:00Z',
          readTime: '7 min read',
          author: {
            name: 'Michael Chen',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['AI Skills', 'Tech Career', 'Resume Building']
        },
        {
          id: '3',
          title: 'How to Write a Cover Letter That Gets Noticed',
          excerpt: 'Tips and templates for crafting compelling cover letters that complement your CV and get you interviews.',
          category: 'cover-letters',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-02-18T00:00:00Z',
          readTime: '6 min read',
          author: {
            name: 'Emily Roberts',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['Cover Letters', 'Job Application', 'Writing Tips']
        },
        {
          id: '4',
          title: 'Mastering Remote Job Interviews: A Comprehensive Guide',
          excerpt: 'Prepare for your next remote interview with these expert tips on technology, presentation and follow-up strategies.',
          category: 'interviews',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-03-05T00:00:00Z',
          readTime: '8 min read',
          author: {
            name: 'David Wilson',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['Interviews', 'Remote Work', 'Job Search']
        },
        {
          id: '5',
          title: 'Career Transition: How to Position Your CV for a New Industry',
          excerpt: 'Learn how to highlight transferable skills and reframe your experience when changing career paths.',
          category: 'career-advice',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-03-22T00:00:00Z',
          readTime: '9 min read',
          author: {
            name: 'Jessica Miller',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['Career Change', 'Resume Strategy', 'Professional Development']
        },
        {
          id: '6',
          title: 'Using Keywords to Get Past ATS Systems',
          excerpt: 'Strategic approaches to optimize your resume for Applicant Tracking Systems without keyword stuffing.',
          category: 'resume-tips',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-04-10T00:00:00Z',
          readTime: '5 min read',
          author: {
            name: 'Thomas Brown',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['ATS', 'Resume Tips', 'Job Application']
        },
        {
          id: '7',
          title: 'Networking Strategies That Will Land You Your Dream Job',
          excerpt: 'Learn how to build and leverage your professional network effectively during your job search.',
          category: 'job-search',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-04-28T00:00:00Z',
          readTime: '6 min read',
          author: {
            name: 'Alexandra Davis',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['Networking', 'Job Search', 'Professional Relationships']
        },
        {
          id: '8',
          title: 'Industry-Specific Resume Templates for 2025',
          excerpt: 'Customized resume formats and examples for different industries including tech, healthcare, finance, and more.',
          category: 'resume-tips',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-05-05T00:00:00Z',
          readTime: '7 min read',
          author: {
            name: 'CVFlow Team',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['Templates', 'Resume Design', 'Industry Specific']
        },
        {
          id: '9',
          title: 'LinkedIn Profile Optimization: Align Your CV with Your Online Presence',
          excerpt: 'Strategies to ensure your LinkedIn profile complements your resume and attracts recruiters.',
          category: 'job-search',
          imageUrl: '/api/placeholder/400/200',
          publishedAt: '2025-05-12T00:00:00Z',
          readTime: '6 min read',
          author: {
            name: 'Ryan Taylor',
            avatar: '/api/placeholder/40/40'
          },
          tags: ['LinkedIn', 'Online Presence', 'Personal Branding']
        }
      ];
      
      // If featured is true, mark the first few as featured
      if (featured) {
        sampleArticles.slice(0, 3).forEach(article => {
          article.featured = true;
        });
      }
      
      // Return requested number of articles
      return sampleArticles.slice(0, count);
    }
  });