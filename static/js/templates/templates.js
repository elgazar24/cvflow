document.addEventListener('DOMContentLoaded', function() {
  // Variables to store template data
  let allTemplates = [];
  let filteredTemplates = [];
  let selectedSector = 'all';
  let selectedTemplateId = null;
  
  // Fetch templates from server
  fetchTemplates();
  
  // Event listeners
  document.getElementById('templateSearch').addEventListener('input', filterTemplates);
  document.getElementById('templateFilter').addEventListener('change', filterTemplates);
  
  // Setup sector tabs
  const sectorTabs = document.querySelectorAll('.sector-tab');
  sectorTabs.forEach(tab => {
    tab.addEventListener('click', function() {
      sectorTabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      selectedSector = this.dataset.sector;
      updateRecommendedTemplates();
    });
  });
  
  // Setup modal close buttons
  document.getElementById('closePreview').addEventListener('click', closePreviewModal);
  document.getElementById('closePreviewBtn').addEventListener('click', closePreviewModal);
  
  // Use template button
  document.getElementById('useTemplateBtn').addEventListener('click', function() {
    if (selectedTemplateId) {
      window.location.href = `/dashboard?template_id=${selectedTemplateId}`;
    }
  });
  
  // Function to fetch templates from the server
  function fetchTemplates() {
    // In production, replace with actual API endpoint
    fetch('/api/templates')
      .then(response => {
        // For development/testing purposes, simulate server response
        if (!response.ok) {
          return simulateTemplateData();
        }
        return response.json();
      })
      .then(data => {
        allTemplates = data;
        filteredTemplates = [...allTemplates];
        renderAllTemplates();
        updateRecommendedTemplates();
      })
      .catch(error => {
        console.error('Error fetching templates:', error);
        // Use simulated data for development/preview
        const data = simulateTemplateData();
        allTemplates = data;
        filteredTemplates = [...allTemplates];
        renderAllTemplates();
        updateRecommendedTemplates();
      });
  }
  
  // Function to filter templates
  function filterTemplates() {
    const searchTerm = document.getElementById('templateSearch').value.toLowerCase();
    const filterValue = document.getElementById('templateFilter').value;
    
    filteredTemplates = allTemplates.filter(template => {
      const matchesSearch = 
        template.name.toLowerCase().includes(searchTerm) || 
        template.description.toLowerCase().includes(searchTerm) ||
        template.features.some(feature => feature.toLowerCase().includes(searchTerm));
      
      const matchesFilter = filterValue === 'all' || template.category === filterValue;
      
      return matchesSearch && matchesFilter;
    });
    
    renderAllTemplates();
    updateRecommendedTemplates();
  }
  
  // Function to render all templates
  function renderAllTemplates() {
    const container = document.getElementById('allTemplates');
    container.innerHTML = '';
    
    if (filteredTemplates.length === 0) {
      container.innerHTML = `
        <div class="text-center" style="grid-column: 1 / -1;">
          <p>No templates found matching your criteria. Please try different search terms.</p>
        </div>
      `;
      return;
    }
    
    filteredTemplates.forEach(template => {
      container.appendChild(createTemplateCard(template));
    });
  }
  
  // Function to update recommended templates based on selected sector
  function updateRecommendedTemplates() {
    const container = document.getElementById('recommendedTemplates');
    container.innerHTML = '';
    
    let recommendedTemplates;
    
    if (selectedSector === 'all') {
      // Show featured templates for all sectors
      recommendedTemplates = filteredTemplates.filter(template => template.featured);
    } else {
      // Show templates for the selected sector
      recommendedTemplates = filteredTemplates.filter(template => 
        template.sectors.includes(selectedSector)
      );
    }
    
    if (recommendedTemplates.length === 0) {
      container.innerHTML = `
        <div class="text-center" style="grid-column: 1 / -1;">
          <p>No recommended templates found for this sector. Try a different sector or check all templates below.</p>
        </div>
      `;
      return;
    }
    
    // Sort recommended templates by rating
    recommendedTemplates.sort((a, b) => b.rating - a.rating);
    
    // Take only the top 4 templates
    recommendedTemplates.slice(0, 4).forEach(template => {
      container.appendChild(createTemplateCard(template));
    });
  }
  
  // Function to create template card
  function createTemplateCard(template) {
    const card = document.createElement('div');
    card.className = 'template-card';
    
    const featuresHTML = template.features.map(feature => 
      `<span class="feature-tag">${feature}</span>`
    ).join('');
    
    card.innerHTML = `
      <div class="template-image">
        <img src="${template.imageUrl}" alt="${template.name}">
      </div>
      <div class="template-content">
        <h3 class="template-name">${template.name}</h3>
        <p class="template-description">${template.description}</p>
        <div class="template-features">
          ${featuresHTML}
        </div>
        <div class="template-actions">
          <button class="template-btn use-btn" data-id="${template.id}">Use Template</button>
          <button class="template-btn preview-btn" data-id="${template.id}">Preview</button>
        </div>
      </div>
    `;
    
    // Add event listeners to buttons
    const useBtn = card.querySelector('.use-btn');
    const previewBtn = card.querySelector('.preview-btn');
    
    useBtn.addEventListener('click', function() {
      window.location.href = `/dashboard?template_id=${template.id}`;
    });
    
    previewBtn.addEventListener('click', function() {
      openPreviewModal(template);
    });
    
    return card;
  }
  
  // Function to open preview modal
  function openPreviewModal(template) {
    selectedTemplateId = template.id;
    document.getElementById('previewTemplateTitle').textContent = template.name;
    
    // In production, this would fetch the actual preview HTML from the server
    const previewBody = document.getElementById('previewBody');
    
    // Show loading state
    previewBody.innerHTML = '<div class="text-center"><p>Loading preview...</p></div>';
    
    // Simulate loading preview (in production, fetch from server)
    setTimeout(() => {
      // For demo purposes, show a simple preview
      previewBody.innerHTML = generatePreviewHTML(template);
    }, 500);
    
    document.getElementById('previewModal').classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  
  // Function to close preview modal
  function closePreviewModal() {
    document.getElementById('previewModal').classList.remove('active');
    document.body.style.overflow = '';
  }
  
  // Generate a simple preview HTML (in production, this would come from the server)
  function generatePreviewHTML(template) {
    return `
      <div style="max-width: 800px; margin: 0 auto; padding: 2rem; font-family: var(--font-main);">
        <h2 style="text-align: center; margin-bottom: 2rem; color: var(--primary-color);">Sample CV using ${template.name} Template</h2>
        
        <div style="display: flex; gap: 2rem; margin-bottom: 2rem;">
          ${template.features.includes('Photo') ? 
            `<div style="width: 150px; height: 150px; border-radius: 50%; overflow: hidden; flex-shrink: 0;">
              <img src="/api/placeholder/150/150" alt="Profile Photo" style="width: 100%; height: 100%; object-fit: cover;">
            </div>` : ''}
          
          <div>
            <h1 style="margin-bottom: 0.5rem; color: var(--text-color);">John Doe</h1>
            <p style="color: var(--text-light); margin-bottom: 1rem;">Senior Software Engineer</p>
            
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                </svg>
                <span>+1 (555) 123-4567</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <span>john.doe@example.com</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <span>San Francisco, CA</span>
              </div>
            </div>
          </div>
        </div>
        
        ${template.features.includes('Summary') || template.features.includes('Objective') ? 
        `<section style="margin-bottom: 2rem;">
          <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: var(--primary-color); border-bottom: 2px solid var(--primary-light); padding-bottom: 0.5rem;">Professional Summary</h2>
          <p>Experienced software engineer with 8+ years of expertise in developing scalable web applications. Proficient in JavaScript, Python, and cloud technologies with a strong focus on creating efficient and maintainable code.</p>
        </section>` : ''}
        
        ${template.features.includes('Experience') ? 
        `<section style="margin-bottom: 2rem;">
          <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: var(--primary-color); border-bottom: 2px solid var(--primary-light); padding-bottom: 0.5rem;">Work Experience</h2>
          
          <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
              <h3 style="font-size: 1.2rem; font-weight: 600; margin: 0;">Senior Software Engineer</h3>
              <span style="color: var(--text-light);">2020 - Present</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
              <h4 style="font-size: 1rem; font-weight: 500; margin: 0; color: var(--text-light);">Tech Innovations Inc.</h4>
              <span style="color: var(--text-light);">San Francisco, CA</span>
            </div>
            <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
              <li>Led the development of a microservices architecture that improved system scalability by 200%</li>
              <li>Managed a team of 5 engineers, implementing agile methodologies that increased productivity by 30%</li>
              <li>Reduced application load time by 60% through code optimization and implementing lazy loading techniques</li>
            </ul>
          </div>
          
          <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
              <h3 style="font-size: 1.2rem; font-weight: 600; margin: 0;">Software Developer</h3>
              <span style="color: var(--text-light);">2017 - 2020</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
              <h4 style="font-size: 1rem; font-weight: 500; margin: 0; color: var(--text-light);">WebSolutions Co.</h4>
              <span style="color: var(--text-light);">Seattle, WA</span>
            </div>
            <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
              <li>Developed and maintained RESTful APIs serving over 100,000 daily users</li>
              <li>Implemented automated testing that reduced bug reports by 40%</li>
              <li>Collaborated with UX designers to improve user interface, increasing user engagement by 25%</li>
            </ul>
          </div>
        </section>` : ''}
        
        ${template.features.includes('Education') ? 
        `<section style="margin-bottom: 2rem;">
          <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: var(--primary-color); border-bottom: 2px solid var(--primary-light); padding-bottom: 0.5rem;">Education</h2>
          
          <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
              <h3 style="font-size: 1.2rem; font-weight: 600; margin: 0;">Master of Science in Computer Science</h3>
              <span style="color: var(--text-light);">2015 - 2017</span>
            </div>
            <h4 style="font-size: 1rem; font-weight: 500; margin: 0; color: var(--text-light);">Stanford University</h4>
            <p style="margin-top: 0.5rem;">GPA: 3.8/4.0 | Thesis: "Optimizing Machine Learning Algorithms for Edge Computing"</p>
          </div>
          
          <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
              <h3 style="font-size: 1.2rem; font-weight: 600; margin: 0;">Bachelor of Science in Software Engineering</h3>
              <span style="color: var(--text-light);">2011 - 2015</span>
            </div>
            <h4 style="font-size: 1rem; font-weight: 500; margin: 0; color: var(--text-light);">University of Washington</h4>
            <p style="margin-top: 0.5rem;">GPA: 3.7/4.0 | Minor in Mathematics</p>
          </div>
        </section>` : ''}
        
        ${template.features.includes('Skills') ? 
        `<section style="margin-bottom: 2rem;">
          <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: var(--primary-color); border-bottom: 2px solid var(--primary-light); padding-bottom: 0.5rem;">Skills</h2>
          
          <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">JavaScript</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">React</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">Node.js</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">Python</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">Django</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">AWS</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">Docker</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">REST APIs</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">GraphQL</span>
            <span style="padding: 0.5rem 1rem; background-color: rgba(79, 70, 229, 0.1); color: var(--primary-color); border-radius: 50px; font-size: 0.9rem;">CI/CD</span>
          </div>
        </section>` : ''}
        
        ${template.features.includes('Projects') ? 
        `<section style="margin-bottom: 2rem;">
          <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: var(--primary-color); border-bottom: 2px solid var(--primary-light); padding-bottom: 0.5rem;">Projects</h2>
          
          <div style="margin-bottom: 1.5rem;">
            <h3 style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">E-Commerce Platform Redesign</h3>
            <p style="margin-bottom: 0.5rem;">Led the complete redesign of an e-commerce platform serving 50,000+ monthly users.</p>
            <ul style="padding-left: 1.5rem;">
              <li>Implemented a microservices architecture using Node.js and Docker</li>
              <li>Designed a responsive frontend using React and Redux</li>
              <li>Increased site performance score from 65 to 95 on Google PageSpeed Insights</li>
            </ul>
          </div>
          
          <div>
            <h3 style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">AI-Powered Content Recommendation System</h3>
            <p style="margin-bottom: 0.5rem;">Developed a machine learning algorithm to improve content recommendations.</p>
            <ul style="padding-left: 1.5rem;">
              <li>Built using Python, TensorFlow, and AWS services</li>
              <li>Increased user engagement by 35% and average session duration by 25%</li>
              <li>Presented findings at the 2023 AI Technology Conference</li>
            </ul>
          </div>
        </section>` : ''}
        
        ${template.features.includes('Certifications') ? 
        `<section style="margin-bottom: 2rem;">
          <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: var(--primary-color); border-bottom: 2px solid var(--primary-light); padding-bottom: 0.5rem;">Certifications</h2>
          
          <ul style="list-style-type: none; padding: 0;">
            <li style="margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: 500;">AWS Certified Solutions Architect</span>
                <span style="color: var(--text-light);">2023</span>
              </div>
            </li>
            <li style="margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: 500;">Google Cloud Professional Developer</span>
                <span style="color: var(--text-light);">2022</span>
              </div>
            </li>
            <li>
              <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: 500;">MongoDB Certified Developer</span>
                <span style="color: var(--text-light);">2021</span>
              </div>
            </li>
          </ul>
        </section>` : ''}
        
        ${template.features.includes('Languages') ? 
        `<section>
          <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: var(--primary-color); border-bottom: 2px solid var(--primary-light); padding-bottom: 0.5rem;">Languages</h2>
          
          <div style="display: flex; gap: 2rem;">
            <div>
              <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 500; margin-right: 1rem; min-width: 80px;">English</span>
                <div style="flex: 1; height: 8px; background-color: #e5e7eb; border-radius: 4px;">
                  <div style="width: 100%; height: 100%; background-color: var(--primary-color); border-radius: 4px;"></div>
                </div>
                <span style="margin-left: 1rem; font-size: 0.9rem;">Native</span>
              </div>
            </div>
            
            <div>
              <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 500; margin-right: 1rem; min-width: 80px;">Spanish</span>
                <div style="flex: 1; height: 8px; background-color: #e5e7eb; border-radius: 4px;">
                  <div style="width: 75%; height: 100%; background-color: var(--primary-color); border-radius: 4px;"></div>
                </div>
                <span style="margin-left: 1rem; font-size: 0.9rem;">Advanced</span>
              </div>
            </div>
          </div>
        </section>` : ''}
      </div>
    `;
  }
  
  // Function to simulate template data (for development/testing)
  function simulateTemplateData() {
    return [
      {
        id: 'template-001',
        name: 'Professional Modern',
        description: 'Clean and modern design perfect for corporate environments and traditional industries.',
        imageUrl: '/api/placeholder/400/250',
        category: 'professional',
        features: ['Summary', 'Experience', 'Education', 'Skills', 'Projects', 'Certifications'],
        sectors: ['business', 'it', 'engineering', 'healthcare'],
        rating: 4.9,
        featured: true
      },
      {
        id: 'template-002',
        name: 'Creative Portfolio',
        description: 'Showcase your creativity with this visually appealing template for creative professionals.',
        imageUrl: '/api/placeholder/400/250',
        category: 'creative',
        features: ['Photo', 'Summary', 'Experience', 'Projects', 'Skills', 'Education'],
        sectors: ['creative', 'education'],
        rating: 4.7,
        featured: true
      },
      {
        id: 'template-003',
        name: 'Technical Specialist',
        description: 'Highlight your technical skills and projects with this specialized template.',
        imageUrl: '/api/placeholder/400/250',
        category: 'professional',
        features: ['Summary', 'Skills', 'Experience', 'Projects', 'Education', 'Certifications'],
        sectors: ['it', 'engineering', 'science'],
        rating: 4.8,
        featured: true
      },
      {
        id: 'template-004',
        name: 'Academic CV',
        description: 'Detailed template for academic professionals focusing on research and publications.',
        imageUrl: '/api/placeholder/400/250',
        category: 'academic',
        features: ['Education', 'Publications', 'Research', 'Teaching', 'Conferences', 'Awards'],
        sectors: ['education', 'science', 'healthcare'],
        rating: 4.6,
        featured: false
      },
      {
        id: 'template-005',
        name: 'Executive Resume',
        description: 'Elegant design highlighting leadership experience for senior professionals.',
        imageUrl: '/api/placeholder/400/250',
        category: 'professional',
        features: ['Summary', 'Experience', 'Achievements', 'Education', 'Skills'],
        sectors: ['business', 'healthcare'],
        rating: 4.9,
        featured: true
      },
      {
        id: 'template-006',
        name: 'Minimalist Clean',
        description: 'Simple and clean design focusing on content with minimal visual elements.',
        imageUrl: '/api/placeholder/400/250',
        category: 'simple',
        features: ['Summary', 'Experience', 'Education', 'Skills'],
        sectors: ['it', 'business', 'engineering'],
        rating: 4.5,
        featured: false
      },
      {
        id: 'template-007',
        name: 'Developer Portfolio',
        description: 'Specialized template for software developers with coding skills showcase.',
        imageUrl: '/api/placeholder/400/250',
        category: 'modern',
        features: ['Photo', 'Summary', 'Skills', 'Projects', 'Experience', 'Education', 'GitHub Projects'],
        sectors: ['it'],
        rating: 4.8,
        featured: true
      },
      {
        id: 'template-008',
        name: 'Healthcare Professional',
        description: 'Specialized template for medical and healthcare professionals.',
        imageUrl: '/api/placeholder/400/250',
        category: 'professional',
        features: ['Photo', 'Summary', 'Experience', 'Education', 'Certifications', 'Skills'],
        sectors: ['healthcare'],
        rating: 4.7,
        featured: false
      },
      {
        id: 'template-009',
        name: 'Engineering Excellence',
        description: 'Focused template for engineering professionals highlighting technical skills.',
        imageUrl: '/api/placeholder/400/250',
        category: 'professional',
        features: ['Summary', 'Technical Skills', 'Experience', 'Projects', 'Education', 'Certifications'],
        sectors: ['engineering', 'science'],
        rating: 4.6,
        featured: false
      },
      {
        id: 'template-010',
        name: 'Creative Colorful',
        description: 'Bold and colorful design that stands out for creative professionals.',
        imageUrl: '/api/placeholder/400/250',
        category: 'creative',
        features: ['Photo', 'Summary', 'Experience', 'Skills', 'Projects', 'Education'],
        sectors: ['creative'],
        rating: 4.5,
        featured: false
      },
      {
        id: 'template-011',
        name: 'Business Professional',
        description: 'Traditional business template with a focus on achievements and results.',
        imageUrl: '/api/placeholder/400/250',
        category: 'professional',
        features: ['Summary', 'Experience', 'Achievements', 'Skills', 'Education'],
        sectors: ['business'],
        rating: 4.7,
        featured: false
      },
      {
        id: 'template-012',
        name: 'Research Scientist',
        description: 'Academic template focused on research experience and publications.',
        imageUrl: '/api/placeholder/400/250',
        category: 'academic',
        features: ['Education', 'Research', 'Publications', 'Conferences', 'Skills', 'Grants'],
        sectors: ['science', 'education'],
        rating: 4.8,
        featured: false
      }
    ];
  }
});