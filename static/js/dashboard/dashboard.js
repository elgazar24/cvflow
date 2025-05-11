// Global variables
let currentCvId = null;
let currentTemplateId = 1;
let profileImageUploaded = false;
let profileImageFilename = '';

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function () {

    setupJsonImport();
    
    // Setup preloaded CV data import
    importPreloadedCvData();

    document.getElementById('export-json').addEventListener('click', exportCvAsJson);


    // Initialize Select2 for Languages
    $('#languages').select2({
        tags: true,  // Enable free-text entries
        createTag: function (params) {
            return {
                id: params.term,
                text: params.term,
                newTag: true  // Mark as unsaved
            };
        },
        placeholder: {
            id: '-1',
            text: 'Type to search for languages'
        },
        minimumInputLength: 1,
        width: '100%',
        language: {
            noResults: function () {
                return "No languages found";
            },
            searching: function () {
                return "Searching languages...";
            }
        },
        ajax: {
            url: '/get_languages',  // Different endpoint for languages
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    input: params.term,
                };
            },
            processResults: function (data) {
                return { results: data };
            }
        }
    });

    // Initialize Select2 for Technologies
    $('#technologies').select2({
        tags: true,  // Enable free-text entries
        createTag: function (params) {
            return {
                id: params.term,
                text: params.term,
                newTag: true  // Mark as unsaved
            };
        },
        placeholder: {
            id: '-1',
            text: 'Type to search for technologies'
        },
        minimumInputLength: 1,
        width: '100%',
        language: {
            noResults: function () {
                return "No technologies found";
            },
            searching: function () {
                return "Searching technologies...";
            }
        },
        ajax: {
            url: '/get_technologies',  // Different endpoint for technologies
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    input: params.term,
                };
            },

            processResults: function (data) {
                return { results: data };
            }
        }
    });

    // Set up template selection change event
    document.getElementById('template-select').addEventListener('change', function () {
        currentTemplateId = parseInt(this.value);
        document.getElementById('template-id').value = currentTemplateId;
        loadTemplateFields(currentTemplateId);
    });

    // Initialize first template
    loadTemplateFields(currentTemplateId);

    // Initialize event listeners for dynamic content
    initializeEventListeners();

    // Load CV list
    loadCvList();

    // Set up preview refresh button
    document.getElementById('refresh-preview').addEventListener('click', refreshPreview);

    // Create new CV button
    document.getElementById('create-new-cv').addEventListener('click', createNewCv);

    // Initialize profile image upload
    initializeProfileImageUpload();

    // Set up AI recommendation buttons
    setupAiRecommendations();

    // Save draft button
    document.getElementById('save-draft-btn').addEventListener('click', saveDraft);

    // Download PDF link
    document.getElementById('download-pdf-link').addEventListener('click', downloadPdf);

    // Setup modal functionalities
    setupModals();
});

// Initialize event listeners for dynamic elements
function initializeEventListeners() {
    // Add education item
    document.getElementById('add-education').addEventListener('click', function () {
        addItem('education');
    });

    // Add experience item
    document.getElementById('add-experience').addEventListener('click', function () {
        addItem('experience');
    });

    // Add project item
    document.getElementById('add-project').addEventListener('click', function () {
        addItem('project');
    });

    // Event delegation for dynamic elements
    document.addEventListener('click', function (e) {
        // Remove items (education, experience, project)
        if (e.target.closest('.remove-item')) {
            e.target.closest('.education-item, .experience-item, .project-item').remove();
        }

        // Remove responsibility items
        if (e.target.closest('.remove-responsibility')) {
            e.target.closest('.responsibility-item').remove();
        }

        // Add responsibility items
        if (e.target.closest('.add-responsibility')) {
            const container = e.target.closest('.form-group').querySelector('.responsibilities-list');
            const itemType = e.target.closest('.experience-item, .project-item') ?
                (e.target.closest('.experience-item') ? 'experience' : 'project') : null;

            if (itemType) {
                addResponsibility(container, `${itemType}-responsibility[]`);
            }
        }

        // Edit existing CV
        if (e.target.closest('.edit-cv')) {
            const cvId = e.target.closest('.cv-list-item').dataset.cvId;
            loadCv(cvId);
        }

        // Delete CV
        if (e.target.closest('.delete-cv')) {
            const cvId = e.target.closest('.cv-list-item').dataset.cvId;
            openDeleteModal(cvId);
        }
    });

    // Form submission
    document.getElementById('cv-form').addEventListener('submit', function (e) {
        e.preventDefault();
        saveAndGeneratePdf();
    });
}

// Add new item (education, experience, project)
function addItem(type) {
    const template = document.getElementById(`${type}-template`);
    const container = document.getElementById(`${type}-fields`);

    if (template && container) {
        // Create a deep clone of the template content
        const clone = template.content.cloneNode(true);

        // Append the clone to the container
        container.appendChild(clone);
    } else {
        console.error(`Missing template or container for ${type}`);
    }
}

// Add new responsibility item
function addResponsibility(container, nameAttr) {
    const template = document.getElementById('responsibility-template');

    if (template && container) {
        // Create a deep clone of the template content
        const clone = template.content.cloneNode(true);

        // Set the name attribute of the input
        const input = clone.querySelector('input');
        if (input) {
            input.name = nameAttr;
        }

        // Append the clone to the container
        container.appendChild(clone);
    } else {
        console.error('Missing responsibility template or container');
    }
}

// Load template fields from server
function loadTemplateFields(templateId) {
    fetch(`/get_template_fields/${templateId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update form based on template requirements
                const profileImageSection = document.getElementById('profile-image-section');
                profileImageSection.style.display = data.requires_image ? 'block' : 'none';

                // Clear existing fields
                clearFormSections();

                // Add required sections based on template fields
                addRequiredSections(data.fields);

                // Update preview if we have a current CV
                if (currentCvId) {
                    refreshPreview();
                }
            }
        })
        .catch(error => {
            console.error('Error loading template fields:', error);
            showAlert('Error loading template, please try again', 'error');
        });
}

// Clear existing form sections
function clearFormSections() {
    document.getElementById('education-fields').innerHTML = '';
    document.getElementById('experience-fields').innerHTML = '';
    document.getElementById('project-fields').innerHTML = '';
}

// Add required sections based on template
function addRequiredSections(fields) {
    // This function would add or hide sections based on the template requirements
    // For now, we'll just show/hide the main sections
    const sections = {
        'objective': document.querySelector('.form-section:has(#objective)'),
        'education': document.querySelector('.form-section:has(#education-fields)'),
        'experience': document.querySelector('.form-section:has(#experience-fields)'),
        'projects': document.querySelector('.form-section:has(#project-fields)'),
        'skills': document.querySelector('.form-section:has(#languages)')
    };

    // Check if the browser supports :has selector
    const hasSupport = CSS.supports('selector(:has(*))');

    if (!hasSupport) {
        // Fallback for browsers that don't support :has
        sections.objective = document.querySelector('.form-section h3 i.fa-bullseye').closest('.form-section');
        sections.education = document.querySelector('.form-section h3 i.fa-graduation-cap').closest('.form-section');
        sections.experience = document.querySelector('.form-section h3 i.fa-briefcase').closest('.form-section');
        sections.projects = document.querySelector('.form-section h3 i.fa-project-diagram').closest('.form-section');
        sections.skills = document.querySelector('.form-section h3 i.fa-code').closest('.form-section');
    }

    // Process fields from template
    for (const key in sections) {
        if (sections[key]) {
            sections[key].style.display = (fields.includes(key)) ? 'block' : 'none';
        }
    }
}

// Initialize profile image upload
function initializeProfileImageUpload() {
    const profileInput = document.getElementById('profile-image-input');
    const previewImg = document.getElementById('profile-image');
    const filenameInput = document.getElementById('profile-image-filename');

    if (profileInput) {
        profileInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                // Create FormData
                const formData = new FormData();
                formData.append('profile_image', file);

                // Upload image
                fetch('/dashboard/upload_profile_image', {
                    method: 'POST',
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Update preview
                            previewImg.src = data.file_url;
                            filenameInput.value = data.filename;
                            profileImageUploaded = true;
                            profileImageFilename = data.filename;
                            showAlert('Image uploaded successfully', 'success');
                        }
                    })
                    .catch(error => {
                        console.error('Error uploading image:', error);
                        showAlert('Error uploading image', 'error');
                    });
            }
        });
    }
}

// Load CV list from server
function loadCvList() {
    const cvList = document.querySelector('.cv-list');
    const createNewMessage = document.querySelector('.no-cv-message');

    if (cvList) {
        // Check if we have CVs
        if (cvList.children.length > (createNewMessage ? 1 : 0)) {
            // Add event listeners to existing CV items
            const items = cvList.querySelectorAll('.cv-list-item');
            items.forEach(item => {
                const cvId = item.dataset.cvId;
                item.querySelector('.edit-cv').addEventListener('click', () => loadCv(cvId));
                item.querySelector('.delete-cv').addEventListener('click', () => openDeleteModal(cvId));
            });
        }
    }
}

// Load CV data from server
function loadCv(cvId) {
    fetch(`/get_cv/${cvId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentCvId = parseInt(cvId);
                const cvData = data.data;

                // Set CV ID
                document.getElementById('cv-id').value = cvId;

                // Set CV name
                document.getElementById('cv-name').value = cvData.cv_name || 'Untitled CV';

                // Set template if available
                if (cvData.template_id) {
                    const templateSelect = document.getElementById('template-select');
                    templateSelect.value = cvData.template_id;
                    document.getElementById('template-id').value = cvData.template_id;
                    currentTemplateId = parseInt(cvData.template_id);
                    loadTemplateFields(currentTemplateId);
                }

                // Fill personal info
                fillPersonalInfo(cvData.personal_info);

                // Fill content sections
                fillContentSections(cvData.content);

                // Update preview
                refreshPreview();

                // Show success message
                showAlert('CV loaded successfully', 'success');

                // Highlight selected CV in the list
                highlightSelectedCv(cvId);
            }
        })
        .catch(error => {
            console.error('Error loading CV:', error);
            showAlert('Error loading CV', 'error');
        });
}

// Fill personal info fields
function fillPersonalInfo(personalInfo) {
    if (!personalInfo) return;

    // Set basic fields
    document.getElementById('name').value = personalInfo.name || '';
    document.getElementById('email').value = personalInfo.email || '';
    document.getElementById('phone').value = personalInfo.phone || '';
    document.getElementById('linkedin').value = personalInfo.linkedin || '';
    document.getElementById('github').value = personalInfo.github || '';
    document.getElementById('location').value = personalInfo.location || '';

    // Set profile image if available
    if (personalInfo.image && personalInfo.image !== 'path/to/image') {
        document.getElementById('profile-image').src = personalInfo.image.startsWith('http') ?
            personalInfo.image : `/uploads/${personalInfo.image}`;
        document.getElementById('profile-image-filename').value = personalInfo.image;
        profileImageUploaded = true;
        profileImageFilename = personalInfo.image;
    } else {
        // Reset to default
        document.getElementById('profile-image').src = '/static/img/profile-placeholder.png';
        document.getElementById('profile-image-filename').value = '';
        profileImageUploaded = false;
        profileImageFilename = '';
    }
}

// Fill content section fields
function fillContentSections(content) {
    if (!content) return;

    // Fill objective
    if (content.objective) {
        document.getElementById('objective').value = content.objective;
    }

    // Fill education
    if (content.education && content.education.length > 0) {
        const educationContainer = document.getElementById('education-fields');
        educationContainer.innerHTML = ''; // Clear existing

        content.education.forEach(edu => {
            addItem('education');
            const lastItem = educationContainer.lastElementChild;

            lastItem.querySelector('[name="education-degree[]"]').value = edu.degree || '';
            lastItem.querySelector('[name="education-university[]"]').value = edu.university || '';
            lastItem.querySelector('[name="education-startDate[]"]').value = edu.startDate || '';
            lastItem.querySelector('[name="education-endDate[]"]').value = edu.endDate || '';
            lastItem.querySelector('[name="education-gpa[]"]').value = edu.gpa || '';
            lastItem.querySelector('[name="education-coursework[]"]').value = edu.coursework || '';
        });
    }

    // Fill experience
    if (content.experience && content.experience.length > 0) {
        const experienceContainer = document.getElementById('experience-fields');
        experienceContainer.innerHTML = ''; // Clear existing

        content.experience.forEach(exp => {
            addItem('experience');
            const lastItem = experienceContainer.lastElementChild;

            lastItem.querySelector('[name="experience-role[]"]').value = exp.role || '';
            lastItem.querySelector('[name="experience-company[]"]').value = exp.company || '';
            lastItem.querySelector('[name="experience-location[]"]').value = exp.location || '';
            lastItem.querySelector('[name="experience-startDate[]"]').value = exp.startDate || '';
            lastItem.querySelector('[name="experience-endDate[]"]').value = exp.endDate || '';

            // Handle responsibilities
            const responsibilitiesList = lastItem.querySelector('.responsibilities-list');
            responsibilitiesList.innerHTML = ''; // Clear default responsibility

            if (exp.responsibilities && exp.responsibilities.length > 0) {
                exp.responsibilities.forEach(resp => {
                    addResponsibility(responsibilitiesList, 'experience-responsibility[]');
                    const lastResp = responsibilitiesList.lastElementChild;
                    lastResp.querySelector('input').value = resp;
                });
            } else {
                // Add one empty responsibility field
                addResponsibility(responsibilitiesList, 'experience-responsibility[]');
            }
        });
    }

    // Fill projects
    if (content.projects && content.projects.length > 0) {
        const projectContainer = document.getElementById('project-fields');
        projectContainer.innerHTML = ''; // Clear existing

        content.projects.forEach(proj => {
            addItem('project');
            const lastItem = projectContainer.lastElementChild;

            lastItem.querySelector('[name="project-title[]"]').value = proj.title || '';
            lastItem.querySelector('[name="project-github_link[]"]').value = proj.github_link || '';

            // Handle responsibilities
            const responsibilitiesList = lastItem.querySelector('.responsibilities-list');
            responsibilitiesList.innerHTML = ''; // Clear default responsibility

            if (proj.responsibilities && proj.responsibilities.length > 0) {
                proj.responsibilities.forEach(resp => {
                    addResponsibility(responsibilitiesList, 'project-responsibility[]');
                    const lastResp = responsibilitiesList.lastElementChild;
                    lastResp.querySelector('input').value = resp;
                });
            } else {
                // Add one empty responsibility field
                addResponsibility(responsibilitiesList, 'project-responsibility[]');
            }
        });
    }

    // Fill skills
    if (content.languages && content.languages.length > 0) {
        // Reset Select2
        $('#languages').val(null).trigger('change');

        // Add selected options
        const languagesSelect = $('#languages');

        // First ensure all options exist
        content.languages.forEach(lang => {
            // Check if option exists
            if (languagesSelect.find(`option[value="${lang}"]`).length === 0) {
                // Create new option
                const newOption = new Option(lang, lang, true, true);
                languagesSelect.append(newOption);
            }
        });

        // Set selected values
        languagesSelect.val(content.languages).trigger('change');
    }

    if (content.technologies && content.technologies.length > 0) {
        // Reset Select2
        $('#technologies').val(null).trigger('change');

        // Add selected options
        const techSelect = $('#technologies');

        // First ensure all options exist
        content.technologies.forEach(tech => {
            // Check if option exists
            if (techSelect.find(`option[value="${tech}"]`).length === 0) {
                // Create new option
                const newOption = new Option(tech, tech, true, true);
                techSelect.append(newOption);
            }
        });

        // Set selected values
        techSelect.val(content.technologies).trigger('change');
    }
}

// Create a new CV
function createNewCv() {
    // Reset form
    document.getElementById('cv-form').reset();

    // Clear CV ID
    document.getElementById('cv-id').value = '';
    currentCvId = null;

    // Set default template
    const templateSelect = document.getElementById('template-select');
    templateSelect.value = '1';
    document.getElementById('template-id').value = '1';
    currentTemplateId = 1;

    // Load template fields
    loadTemplateFields(currentTemplateId);

    // Reset profile image
    document.getElementById('profile-image').src = '/static/images/profile-placeholder-white.png';
    document.getElementById('profile-image-filename').value = '';
    profileImageUploaded = false;
    profileImageFilename = '';

    // Reset Select2 fields
    $('#languages').val(null).trigger('change');
    $('#technologies').val(null).trigger('change');

    // Clear containers
    clearFormSections();

    // Reset preview
    document.querySelector('.preview-iframe').src = '';
    document.querySelector('.preview-placeholder').style.display = 'block';

    // Remove highlight from CV list
    const selectedItems = document.querySelectorAll('.cv-list-item.selected');
    selectedItems.forEach(item => item.classList.remove('selected'));

    showAlert('Created new CV', 'success');
}

// Save CV draft
function saveDraft() {
    // Same as save but without generating PDF
    const formData = collectFormData();

    fetch('/save_cv', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update current CV ID
                currentCvId = data.cv_id;
                document.getElementById('cv-id').value = data.cv_id;

                // Show success message
                showAlert('CV draft saved successfully', 'success');

                // Update CV list or add new item
                updateCvListItem(data.cv_id, formData.cv_name);
            } else {
                showAlert(data.error || 'Error saving CV draft', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error saving CV draft', 'error');
        });
}

// Save CV and generate PDF
function saveAndGeneratePdf() {
    const formData = collectFormData();

    fetch('/save_cv', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update current CV ID
                currentCvId = data.cv_id;
                document.getElementById('cv-id').value = data.cv_id;

                // Update preview iframe
                const previewIframe = document.querySelector('.preview-iframe');
                previewIframe.src = data.pdf_url;

                // Hide placeholder
                document.querySelector('.preview-placeholder').style.display = 'none';

                // Update download link
                document.getElementById('download-pdf-link').href = `/download_pdf_dashboard?cv_id=${data.cv_id}&template_id=${currentTemplateId}`;

                // Show success message
                showAlert('CV saved and PDF generated successfully', 'success');

                // Update CV list or add new item
                updateCvListItem(data.cv_id, formData.cv_name);
            } else {
                showAlert(data.error || 'Error saving CV', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error saving CV', 'error');
        });
}

// Refresh preview iframe
function refreshPreview() {
    if (currentCvId) {
        const previewIframe = document.querySelector('.preview-iframe');
        previewIframe.src = `/preview_pdf_dashboard?cv_id=${currentCvId}&template_id=${currentTemplateId}`;
        document.querySelector('.preview-placeholder').style.display = 'none';
    }
}

// Download PDF
function downloadPdf(e) {
    e.preventDefault();

    if (currentCvId) {
        window.location.href = `/download_pdf_dashboard?cv_id=${currentCvId}&template_id=${currentTemplateId}`;
    } else {
        showAlert('Please save your CV first', 'error');
    }
}

// Setup AI recommendations
function setupAiRecommendations() {
    const aiButtons = document.querySelectorAll('.ai-recommend-btn');
    const modal = document.getElementById('ai-recommend-modal');
    const getRecommendBtn = document.getElementById('get-ai-recommendation');
    const applyRecommendBtn = document.getElementById('apply-ai-recommendation');
    const promptInput = document.getElementById('ai-prompt');
    const resultDiv = document.querySelector('.ai-result');
    const loadingDiv = document.querySelector('.ai-loading');

    let currentField = null;

    // Open modal when clicking AI recommend button
    aiButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            currentField = this.dataset.field;
            modal.style.display = 'block';
            promptInput.value = '';
            resultDiv.innerHTML = '';
            resultDiv.style.display = 'none';
            loadingDiv.style.display = 'none';
            document.querySelector('.modal-header h3').textContent = `AI Recommendations for ${currentField.charAt(0).toUpperCase() + currentField.slice(1)}`;
        });
    });

    // Get AI recommendation
    if (getRecommendBtn) {
        getRecommendBtn.addEventListener('click', function () {
            const prompt = promptInput.value.trim();
            if (!prompt) {
                showAlert('Please enter a prompt', 'error');
                return;
            }

            // Show loading
            resultDiv.style.display = 'none';
            loadingDiv.style.display = 'flex';

            // Collect current form data
            const formData = collectFormData();

            // Send request to AI service
            fetch('/ai_recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    field: currentField,
                    cv_data: formData
                })
            })
                .then(response => response.json())
                .then(data => {
                    // Hide loading
                    loadingDiv.style.display = 'none';

                    if (data.success && data.recommendation) {
                        // Show result
                        resultDiv.textContent = data.recommendation;
                        resultDiv.style.display = 'block';

                        // Enable apply button
                        applyRecommendBtn.disabled = false;
                    } else {
                        // Show empty result for now
                        resultDiv.textContent = "No recommendations available at this time. This feature will be enhanced in future updates.";
                        resultDiv.style.display = 'block';

                        // Disable apply button
                        applyRecommendBtn.disabled = true;
                    }
                })
                .catch(error => {
                    console.error('Error getting AI recommendation:', error);
                    loadingDiv.style.display = 'none';
                    resultDiv.textContent = "An error occurred. Please try again later.";
                    resultDiv.style.display = 'block';

                    // Disable apply button
                    applyRecommendBtn.disabled = true;
                });
        });
    }

    // Apply AI recommendation
    if (applyRecommendBtn) {
        applyRecommendBtn.addEventListener('click', function () {
            if (resultDiv.textContent && currentField) {
                // Apply text to appropriate field
                if (currentField === 'objective') {
                    
                    // Clean the text content
                    resultDiv.textContent = resultDiv.textContent.replace(/["{}`]+$/g, '');

                    // Remove this : "objective": or "objective" : 
                    resultDiv.textContent = resultDiv.textContent.replace(/objective:/g, '');
                    resultDiv.textContent = resultDiv.textContent.replace(/objective :/g, '');

                    document.getElementById('objective').value = resultDiv.textContent;
                }
                // Other fields would need specific implementation based on structure
                if (currentField === 'education') {
                    // ...
                }
                if (currentField === 'experience') {
                    // ...
                }
                if (currentField === 'projects') {
                    // ...
                }
                if (currentField === 'languages') {
                    // Remove Any Trailing " and ending " and {}
                    resultDiv.textContent = resultDiv.textContent.replace(/["]+$/g, '');
                    resultDiv.textContent = resultDiv.textContent.replace(/[{]+$/g, '');
                    resultDiv.textContent = resultDiv.textContent.replace(/[}]+$/g, '');


                    // Assume comma-separated list of language names
                    const languages = resultDiv.textContent.split(',').map(lang => lang.trim());
                    document.getElementById('languages').value = languages;
                }
                if (currentField === 'skills') {
                    // Clean the text content
                    resultDiv.textContent = resultDiv.textContent.replace(/["{}`]+$/g, '');

                    // Remove this : "objective": or "objective" : 
                    resultDiv.textContent = resultDiv.textContent.replace(/objective:/g, '');
                    resultDiv.textContent = resultDiv.textContent.replace(/objective :/g, '');

                    
                    // Get comma-separated technologies and trim whitespace
                    const technologies = resultDiv.textContent.split(',')
                        .map(tech => tech.trim())
                        .filter(tech => tech.length > 0);
                
                    // Get current Select2 instance
                    const $select = $('#technologies');
                    
                    // Clear existing selections
                    $select.val(null).trigger('change');
                    
                    // Add new technologies
                    technologies.forEach(tech => {
                        // Check if option exists
                        if ($select.find('option[value="' + tech + '"]').length === 0) {
                            // Create new option if it doesn't exist
                            const newOption = new Option(tech, tech, true, true);
                            $select.append(newOption);
                        }
                        
                        // Select the option
                        $select.val(function() {
                            const current = $(this).val() || [];
                            return [...current, tech];
                        });
                    });
                    
                    // Update Select2
                    $select.trigger('change');
                }

                // Close modal
                modal.style.display = 'none';

                // Show success message
                showAlert('AI recommendation applied', 'success');
            }
        });
    }
}

// Setup modals
function setupModals() {
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');

    // Close when clicking X
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const modal = this.closest('.modal');
            modal.style.display = 'none';
        });
    });

    // Close when clicking outside
    window.addEventListener('click', function (e) {
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Delete modal specific setup
    const deleteModal = document.getElementById('delete-modal');
    const cancelDeleteBtn = document.getElementById('cancel-delete');
    const confirmDeleteBtn = document.getElementById('confirm-delete');
    let cvToDelete = null;

    // Cancel delete
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function () {
            deleteModal.style.display = 'none';
            cvToDelete = null;
        });
    }

    // Confirm delete
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function () {
            if (cvToDelete) {
                deleteCv(cvToDelete);
                deleteModal.style.display = 'none';
            }
        });
    }

    // Open delete modal
    window.openDeleteModal = function (cvId) {
        cvToDelete = cvId;
        if (deleteModal) {
            deleteModal.style.display = 'block';
        }
    };
}

// Delete CV
function deleteCv(cvId) {
    fetch(`/delete_cv/${cvId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove CV from list
                const cvItem = document.querySelector(`.cv-list-item[data-cv-id="${cvId}"]`);
                if (cvItem) {
                    cvItem.remove();
                }

                // Reset form if current CV was deleted
                if (currentCvId === parseInt(cvId)) {
                    createNewCv();
                }

                // Show success message
                showAlert('CV deleted successfully', 'success');

                // Update no CV message if needed
                const cvList = document.querySelector('.cv-list');
                if (cvList && cvList.children.length === 0) {
                    const noMessage = document.createElement('div');
                    noMessage.className = 'no-cv-message';
                    noMessage.innerHTML = `
                    <i class="fas fa-file-alt"></i>
                    <p>No CVs created yet</p>
                    <p>Create your first CV to get started</p>
                `;
                    cvList.appendChild(noMessage);
                }
            } else {
                showAlert(data.error || 'Error deleting CV', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting CV:', error);
            showAlert('Error deleting CV', 'error');
        });
}

// Helper: Show alert message
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${type}`;
    alertDiv.innerHTML = `<p>${message}</p>`;

    // Find insertion point
    const insertPoint = document.querySelector('.editor-header');
    if (insertPoint) {
        insertPoint.parentNode.insertBefore(alertDiv, insertPoint.nextSibling);

        // Remove after 3 seconds
        setTimeout(() => alertDiv.remove(), 3000);
    } else {
        // Fallback if editor header not found
        const mainElement = document.querySelector('main');
        if (mainElement) {
            mainElement.prepend(alertDiv);

            // Remove after 3 seconds
            setTimeout(() => alertDiv.remove(), 3000);
        }
    }
}

// Helper: Highlight selected CV in list
function highlightSelectedCv(cvId) {
    // Remove existing selection
    const selectedItems = document.querySelectorAll('.cv-list-item.selected');
    selectedItems.forEach(item => item.classList.remove('selected'));

    // Add selection to current CV
    const currentItem = document.querySelector(`.cv-list-item[data-cv-id="${cvId}"]`);
    if (currentItem) {
        currentItem.classList.add('selected');
    }
}

// Helper: Update CV list item or add new one
function updateCvListItem(cvId, cvName) {
    const cvList = document.querySelector('.cv-list');
    const existingItem = document.querySelector(`.cv-list-item[data-cv-id="${cvId}"]`);

    // Get current date formatted
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });

    if (existingItem) {
        // Update existing item
        existingItem.querySelector('.cv-name').textContent = cvName || 'Untitled CV';
        existingItem.querySelector('.cv-date').textContent = dateStr;

        // Make sure it's selected
        highlightSelectedCv(cvId);
    } else {
        // Create new item
        const noMessage = document.querySelector('.no-cv-message');
        if (noMessage) {
            noMessage.remove();
        }

        const newItem = document.createElement('div');
        newItem.className = 'cv-list-item selected';
        newItem.dataset.cvId = cvId;
        newItem.innerHTML = `
            <div class="cv-item-content">
                <span class="cv-name">${cvName || 'Untitled CV'}</span>
                <span class="cv-date">${dateStr}</span>
            </div>
            <div class="cv-item-actions">
                <button class="cv-action-btn edit-cv" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="cv-action-btn delete-cv" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        // Add to list
        cvList.appendChild(newItem);

        // Remove existing selection
        const selectedItems = document.querySelectorAll('.cv-list-item.selected');
        selectedItems.forEach(item => {
            if (item !== newItem) {
                item.classList.remove('selected');
            }
        });

        // Add event listeners
        newItem.querySelector('.edit-cv').addEventListener('click', () => loadCv(cvId));
        newItem.querySelector('.delete-cv').addEventListener('click', () => openDeleteModal(cvId));
    }
}



function collectFormData() {
    // Base data structure
    const formData = {
        cv_id: document.getElementById('cv-id').value || null,
        cv_name: document.getElementById('cv-name').value || 'Untitled CV',
        template_id: currentTemplateId,
        personal_info: {
            name: document.getElementById('name').value || '',
            email: document.getElementById('email').value || '',
            phone: document.getElementById('phone').value || '',
            linkedin: document.getElementById('linkedin').value || '',
            github: document.getElementById('github').value || '',
            location: document.getElementById('location').value || '',
            image: profileImageUploaded ? profileImageFilename : 'path/to/image'
        },
        content: {
            objective: document.getElementById('objective').value || '',
            education: collectEducation(),
            experience: collectExperience(),
            projects: collectProjects(),
            languages: $('#languages').val() || [],
            technologies: $('#technologies').val() || []
        }
    };

    return formData;
}

// Helper functions to collect array-based data
function collectEducation() {
    const education = [];
    const educationItems = document.querySelectorAll('.education-item');

    educationItems.forEach(item => {
        education.push({
            degree: item.querySelector('[name="education-degree[]"]').value || '',
            university: item.querySelector('[name="education-university[]"]').value || '',
            startDate: item.querySelector('[name="education-startDate[]"]').value || '',
            endDate: item.querySelector('[name="education-endDate[]"]').value || '',
            gpa: item.querySelector('[name="education-gpa[]"]').value || '',
            certificate: item.querySelector('[name="education-certificate[]"]') ?
                item.querySelector('[name="education-certificate[]"]').value || 'N\\A' : 'N\\A',
            coursework: item.querySelector('[name="education-coursework[]"]').value || ''
        });
    });

    return education;
}

function collectExperience() {
    const experience = [];
    const experienceItems = document.querySelectorAll('.experience-item');

    experienceItems.forEach(item => {
        const responsibilities = [];
        const responsibilityInputs = item.querySelectorAll('[name="experience-responsibility[]"]');

        responsibilityInputs.forEach(input => {
            if (input.value.trim()) {
                responsibilities.push(input.value.trim());
            }
        });

        experience.push({
            role: item.querySelector('[name="experience-role[]"]').value || '',
            company: item.querySelector('[name="experience-company[]"]').value || '',
            location: item.querySelector('[name="experience-location[]"]').value || '',
            startDate: item.querySelector('[name="experience-startDate[]"]').value || '',
            endDate: item.querySelector('[name="experience-endDate[]"]').value || '',
            responsibilities: responsibilities
        });
    });

    return experience;
}

function collectProjects() {
    const projects = [];
    const projectItems = document.querySelectorAll('.project-item');

    projectItems.forEach(item => {
        const responsibilities = [];
        const responsibilityInputs = item.querySelectorAll('[name="project-responsibility[]"]');

        responsibilityInputs.forEach(input => {
            if (input.value.trim()) {
                responsibilities.push(input.value.trim());
            }
        });

        projects.push({
            title: item.querySelector('[name="project-title[]"]').value || '',
            github_link: item.querySelector('[name="project-github_link[]"]').value || '',
            responsibilities: responsibilities
        });
    });

    return projects;
}

// Download PDF handler
function downloadPdf(e) {
    e.preventDefault();

    // First ensure CV is saved
    if (!currentCvId) {
        saveAndGeneratePdf().then(() => {
            if (currentCvId) {
                window.location.href = `/download_pdf_dashboard?cv_id=${currentCvId}&template_id=${currentTemplateId}`;
            }
        });
    } else {
        window.location.href = `/download_pdf_dashboard?cv_id=${currentCvId}&template_id=${currentTemplateId}`;
    }
}

// Initialize when document is ready (additional initializations)
document.addEventListener('DOMContentLoaded', function () {
    // Add mobile menu toggle
    const mobileMenuToggle = document.querySelector('.hamburger');
    const mobileMenu = document.querySelector('.nav-links');

    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function () {
            mobileMenuToggle.classList.toggle('active');
            mobileMenu.classList.toggle('show');
        });
    }

    // Initialize template selector
    loadTemplates();

    // Initialize theme switcher if present
    const themeSwitch = document.querySelector('.theme-switch input');
    if (themeSwitch) {
        if (localStorage.getItem('theme') === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeSwitch.checked = true;
        }

        themeSwitch.addEventListener('change', function (e) {
            if (e.target.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    // Handle header shrink on scroll
    window.addEventListener('scroll', function () {
        const header = document.querySelector('.main-header');
        if (header) {
            if (window.scrollY > 50) {
                header.classList.add('header-shrink');
            } else {
                header.classList.remove('header-shrink');
            }
        }
    });
});

// Load templates from server
function loadTemplates() {
    fetch('/get_templates')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.templates) {
                const templateSelect = document.getElementById('template-select');

                // Clear existing options except the default/placeholder
                while (templateSelect.options.length > 1) {
                    templateSelect.remove(1);
                }

                // Add templates
                data.templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.name;
                    templateSelect.appendChild(option);
                });

                // Set current template
                if (currentTemplateId) {
                    templateSelect.value = currentTemplateId;
                }
            }
        })
        .catch(error => {
            console.error('Error loading templates:', error);
            showAlert('Error loading templates from server', 'error');
        });
}

// Helper function for saving CV as promise (for chaining)
function saveAndGeneratePdfPromise() {
    return new Promise((resolve, reject) => {
        const formData = collectFormData();

        fetch('/save_cv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update current CV ID
                    currentCvId = data.cv_id;
                    document.getElementById('cv-id').value = data.cv_id;

                    // Update preview iframe
                    const previewIframe = document.querySelector('.preview-iframe');
                    previewIframe.src = data.pdf_url;

                    // Hide placeholder
                    document.querySelector('.preview-placeholder').style.display = 'none';

                    // Update download link
                    document.getElementById('download-pdf-link').href =
                        `/download_pdf_dashboard?cv_id=${data.cv_id}&template_id=${currentTemplateId}`;

                    // Show success message
                    showAlert('CV saved and PDF generated successfully', 'success');

                    // Update CV list or add new item
                    updateCvListItem(data.cv_id, formData.cv_name);

                    resolve(data);
                } else {
                    showAlert(data.error || 'Error saving CV', 'error');
                    reject(new Error(data.error || 'Error saving CV'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error saving CV', 'error');
                reject(error);
            });
    });
}

// Enhanced refresh preview
function refreshPreview() {
    if (currentCvId) {
        const previewIframe = document.querySelector('.preview-iframe');
        const placeholderDiv = document.querySelector('.preview-placeholder');

        // Show loading state
        if (placeholderDiv) {
            placeholderDiv.innerHTML = '<div class="loading-spinner"></div><p>Generating preview...</p>';
            placeholderDiv.style.display = 'flex';
        }

        // Load the preview
        previewIframe.src = `/preview_pdf_dashboard?cv_id=${currentCvId}&template_id=${currentTemplateId}`;

        // Hide placeholder when iframe loads
        previewIframe.onload = function () {
            if (placeholderDiv) {
                placeholderDiv.style.display = 'none';
            }
        };
    } else {
        saveDraft().then(() => {
            if (currentCvId) {
                refreshPreview();
            }
        });
    }
}

// Enhanced Save CV and generate PDF
function saveAndGeneratePdf() {
    return saveAndGeneratePdfPromise();
}

// Enhanced saveDraft function that returns Promise for chaining
function saveDraft() {
    return new Promise((resolve, reject) => {
        const formData = collectFormData();

        fetch('/save_cv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update current CV ID
                    currentCvId = data.cv_id;
                    document.getElementById('cv-id').value = data.cv_id;

                    // Show success message
                    showAlert('CV draft saved successfully', 'success');

                    // Update CV list or add new item
                    updateCvListItem(data.cv_id, formData.cv_name);

                    resolve(data);
                } else {
                    showAlert(data.error || 'Error saving CV draft', 'error');
                    reject(new Error(data.error || 'Error saving CV draft'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error saving CV draft', 'error');
                reject(error);
            });
    });
}

// Function to handle responsive behavior
function handleResponsiveBehavior() {
    const dashboardContainer = document.querySelector('.dashboard-container');
    const cvEditor = document.querySelector('.cv-editor');
    const cvPreview = document.querySelector('.cv-preview');

    if (window.innerWidth <= 992) {
        // Mobile/tablet view
        const editorTab = document.getElementById('editor-tab');
        const previewTab = document.getElementById('preview-tab');

        if (editorTab && previewTab) {
            editorTab.addEventListener('click', function () {
                this.classList.add('active');
                previewTab.classList.remove('active');
                cvEditor.style.display = 'block';
                cvPreview.style.display = 'none';
            });

            previewTab.addEventListener('click', function () {
                this.classList.add('active');
                editorTab.classList.remove('active');
                cvPreview.style.display = 'block';
                cvEditor.style.display = 'none';
            });
        }
    } else {
        // Desktop view
        if (cvEditor && cvPreview) {
            cvEditor.style.display = 'block';
            cvPreview.style.display = 'block';
        }
    }
}

// Initialize responsive behavior
window.addEventListener('load', handleResponsiveBehavior);
window.addEventListener('resize', handleResponsiveBehavior);



// JSON Import functionality
function setupJsonImport() {
    // Add event listener to the import button
    document.getElementById('import-json').addEventListener('click', function() {
        // Create a file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.json';
        fileInput.style.display = 'none';
        
        // Add event listener for file selection
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    try {
                        const jsonData = JSON.parse(event.target.result);
                        importCvFromJson(jsonData);
                    } catch (error) {
                        console.error('Error parsing JSON:', error);
                        showAlert('Error parsing JSON file', 'error');
                    }
                };
                reader.readAsText(file);
            }
        });
        
        // Trigger file selection dialog
        document.body.appendChild(fileInput);
        fileInput.click();
        document.body.removeChild(fileInput);
    });
}

// Function to import CV data from JSON
function importCvFromJson(jsonData) {
    try {
        // Clear any existing data
        createNewCv();
        
        // Set CV name (generate from name and current date)
        const name = jsonData.personal_info?.name || 'Imported CV';
        const currentDate = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        document.getElementById('cv-name').value = `${name}'s CV - ${currentDate}`;
        
        // Fill personal info
        if (jsonData.personal_info) {
            document.getElementById('name').value = jsonData.personal_info.name || '';
            document.getElementById('email').value = jsonData.personal_info.email || '';
            document.getElementById('phone').value = jsonData.personal_info.phone || '';
            document.getElementById('linkedin').value = jsonData.personal_info.linkedin || '';
            document.getElementById('github').value = jsonData.personal_info.github || '';
            document.getElementById('location').value = jsonData.personal_info.location || '';
            
            // Handle profile image if present
            if (jsonData.personal_info.image && jsonData.personal_info.image !== '') {
                document.getElementById('profile-image-filename').value = jsonData.personal_info.image;
                profileImageFilename = jsonData.personal_info.image;
                
                // If it's a URL, display it directly
                if (jsonData.personal_info.image.startsWith('http')) {
                    document.getElementById('profile-image').src = jsonData.personal_info.image;
                    profileImageUploaded = true;
                }
            }
        }
        
        // Fill objective
        if (jsonData.content?.objective) {
            document.getElementById('objective').value = jsonData.content.objective;
        }
        
        // Fill education
        if (jsonData.content?.education && jsonData.content.education.length > 0) {
            const educationContainer = document.getElementById('education-fields');
            educationContainer.innerHTML = ''; // Clear existing
            
            jsonData.content.education.forEach(edu => {
                addItem('education');
                const lastItem = educationContainer.lastElementChild;
                
                lastItem.querySelector('[name="education-degree[]"]').value = edu.degree || '';
                lastItem.querySelector('[name="education-university[]"]').value = edu.university || '';
                lastItem.querySelector('[name="education-startDate[]"]').value = edu.startDate || '';
                lastItem.querySelector('[name="education-endDate[]"]').value = edu.endDate || '';
                lastItem.querySelector('[name="education-gpa[]"]').value = edu.gpa || '';
                lastItem.querySelector('[name="education-coursework[]"]').value = edu.coursework || '';
            });
        }
        
        // Fill experience
        if (jsonData.content?.experience && jsonData.content.experience.length > 0) {
            const experienceContainer = document.getElementById('experience-fields');
            experienceContainer.innerHTML = ''; // Clear existing
            
            jsonData.content.experience.forEach(exp => {
                addItem('experience');
                const lastItem = experienceContainer.lastElementChild;
                
                lastItem.querySelector('[name="experience-role[]"]').value = exp.role || '';
                lastItem.querySelector('[name="experience-company[]"]').value = exp.company || '';
                lastItem.querySelector('[name="experience-location[]"]').value = exp.location || '';
                lastItem.querySelector('[name="experience-startDate[]"]').value = exp.startDate || '';
                lastItem.querySelector('[name="experience-endDate[]"]').value = exp.endDate || '';
                
                // Handle responsibilities
                const responsibilitiesList = lastItem.querySelector('.responsibilities-list');
                responsibilitiesList.innerHTML = ''; // Clear default responsibility
                
                if (exp.responsibilities && exp.responsibilities.length > 0) {
                    exp.responsibilities.forEach(resp => {
                        addResponsibility(responsibilitiesList, 'experience-responsibility[]');
                        const lastResp = responsibilitiesList.lastElementChild;
                        lastResp.querySelector('input').value = resp;
                    });
                } else {
                    // Add one empty responsibility field
                    addResponsibility(responsibilitiesList, 'experience-responsibility[]');
                }
            });
        }
        
        // Fill projects
        if (jsonData.content?.projects && jsonData.content.projects.length > 0) {
            const projectContainer = document.getElementById('project-fields');
            projectContainer.innerHTML = ''; // Clear existing
            
            jsonData.content.projects.forEach(proj => {
                addItem('project');
                const lastItem = projectContainer.lastElementChild;
                
                lastItem.querySelector('[name="project-title[]"]').value = proj.title || '';
                lastItem.querySelector('[name="project-github_link[]"]').value = proj.github_link || '';
                
                // Handle responsibilities
                const responsibilitiesList = lastItem.querySelector('.responsibilities-list');
                responsibilitiesList.innerHTML = ''; // Clear default responsibility
                
                if (proj.responsibilities && proj.responsibilities.length > 0) {
                    proj.responsibilities.forEach(resp => {
                        addResponsibility(responsibilitiesList, 'project-responsibility[]');
                        const lastResp = responsibilitiesList.lastElementChild;
                        lastResp.querySelector('input').value = resp;
                    });
                } else {
                    // Add one empty responsibility field
                    addResponsibility(responsibilitiesList, 'project-responsibility[]');
                }
            });
        }
        
        // Fill languages
        if (jsonData.content?.languages && jsonData.content.languages.length > 0) {
            // Reset Select2
            $('#languages').val(null).trigger('change');
            
            // Add options and select them
            const languagesSelect = $('#languages');
            jsonData.content.languages.forEach(lang => {
                if (languagesSelect.find(`option[value="${lang}"]`).length === 0) {
                    const newOption = new Option(lang, lang, true, true);
                    languagesSelect.append(newOption);
                }
            });
            languagesSelect.val(jsonData.content.languages).trigger('change');
        }
        
        // Fill technologies
        if (jsonData.content?.technologies && jsonData.content.technologies.length > 0) {
            // Reset Select2
            $('#technologies').val(null).trigger('change');
            
            // Add options and select them
            const techSelect = $('#technologies');
            jsonData.content.technologies.forEach(tech => {
                if (techSelect.find(`option[value="${tech}"]`).length === 0) {
                    const newOption = new Option(tech, tech, true, true);
                    techSelect.append(newOption);
                }
            });
            techSelect.val(jsonData.content.technologies).trigger('change');
        }
        
        // Show success message
        showAlert('CV data imported successfully', 'success');
        
        // Save as draft
        saveDraft();
    } catch (error) {
        console.error('Error importing CV data:', error);
        showAlert('Error importing CV data', 'error');
    }
}

// Add a direct import function for the provided JSON data (pre-loaded)
function importPreloadedCvData() {
    // Create a button for preloaded data
    const preloadedButton = document.createElement('button');
    preloadedButton.id = 'import-preloaded';
    preloadedButton.className = 'preloaded-import-btn';
    preloadedButton.innerHTML = '<i class="fas fa-file-download"></i> Load Sample CV';
    
    // Add it to the sidebar
    const sidebarActions = document.querySelector('.sidebar-actions');
    if (sidebarActions) {
        sidebarActions.prepend(preloadedButton);
        
        // Add event listener
        preloadedButton.addEventListener('click', function() {
            // Fetch the sample JSON data
            fetch('/get_sample_cv_data')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        importCvFromJson(data.data);
                    } else {
                        showAlert('Error loading sample CV data', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error loading sample CV data:', error);
                    showAlert('Failed to load sample CV data', 'error');
                });
        });
    }
}

function exportCvAsJson() {
    // First collect all the form data
    const formData = collectFormData();
    
    // Convert to pretty-printed JSON string
    const jsonString = JSON.stringify(formData, null, 2);
    
    // Create a Blob with the JSON data
    const blob = new Blob([jsonString], { type: 'application/json' });
    
    // Create a download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // Generate filename based on CV name or default
    const cvName = formData.cv_name || 'my_cv';
    const filename = `${cvName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${new Date().toISOString().split('T')[0]}.txt`;
    a.download = filename;
    
    // Trigger the download
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
    
    // Show success message
    showAlert('CV data exported successfully', 'success');
}