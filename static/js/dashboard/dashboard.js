// JavaScript for dynamic form fields
document.getElementById('add-education').addEventListener('click', function () {
    const newEdu = document.createElement('div');
    newEdu.className = 'education-item';
    newEdu.innerHTML = `
            <div class="form-group">
                <label>Degree</label>
                <input type="text" name="education-degree[]" required>
            </div>
            <div class="form-group">
                <label>University</label>
                <input type="text" name="education-university[]" required>
            </div>
            <div class="form-group">
                <label>Start Date</label>
                <input type="text" name="education-startDate[]">
            </div>
            <div class="form-group">
                <label>End Date</label>
                <input type="text" name="education-endDate[]">
            </div>
            <div class="form-group">
                <label>GPA</label>
                <input type="text" name="education-gpa[]">
            </div>
            <div class="form-group">
                <label>Coursework</label>
                <textarea name="education-coursework[]" rows="3"></textarea>
            </div>
            <button type="button" class="remove-item">
                <i class="fas fa-trash"></i>
            </button>
        `;
    document.getElementById('education-fields').appendChild(newEdu);
});

document.getElementById('add-experience').addEventListener('click', function () {
    const newExp = document.createElement('div');
    newExp.className = 'experience-item';
    newExp.innerHTML = `
            <div class="form-group">
                <label>Role</label>
                <input type="text" name="experience-role[]" required>
            </div>
            <div class="form-group">
                <label>Company</label>
                <input type="text" name="experience-company[]" required>
            </div>
            <div class="form-group">
                <label>Location</label>
                <input type="text" name="experience-location[]">
            </div>
            <div class="form-group">
                <label>Start Date</label>
                <input type="text" name="experience-startDate[]">
            </div>
            <div class="form-group">
                <label>End Date</label>
                <input type="text" name="experience-endDate[]">
            </div>
            <div class="form-group">
                <label>Responsibilities</label>
                <div class="responsibilities-list">
                    <div class="responsibility-item">
                        <input type="text" name="experience-responsibility[]">
                        <button type="button" class="remove-responsibility">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <button type="button" class="add-responsibility">
                    <i class="fas fa-plus"></i> Add Responsibility
                </button>
            </div>
            <button type="button" class="remove-item">
                <i class="fas fa-trash"></i>
            </button>
        `;
    document.getElementById('experience-fields').appendChild(newExp);
});

document.getElementById('add-project').addEventListener('click', function () {
    const newProj = document.createElement('div');
    newProj.className = 'project-item';
    newProj.innerHTML = `
            <div class="form-group">
                <label>Title</label>
                <input type="text" name="project-title[]" required>
            </div>
            <div class="form-group">
                <label>GitHub Link</label>
                <input type="url" name="project-github_link[]">
            </div>
            <div class="form-group">
                <label>Responsibilities</label>
                <div class="responsibilities-list">
                    <div class="responsibility-item">
                        <input type="text" name="project-responsibility[]">
                        <button type="button" class="remove-responsibility">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <button type="button" class="add-responsibility">
                    <i class="fas fa-plus"></i> Add Responsibility
                </button>
            </div>
            <button type="button" class="remove-item">
                <i class="fas fa-trash"></i>
            </button>
        `;
    document.getElementById('project-fields').appendChild(newProj);
});

// Event delegation for remove buttons
document.addEventListener('click', function (e) {
    if (e.target.closest('.remove-item')) {
        e.target.closest('.education-item, .experience-item, .project-item').remove();
    }

    if (e.target.closest('.remove-responsibility')) {
        e.target.closest('.responsibility-item').remove();
    }

    if (e.target.closest('.add-responsibility')) {
        const container = e.target.closest('.form-group').querySelector('.responsibilities-list');
        const newItem = document.createElement('div');
        newItem.className = 'responsibility-item';
        newItem.innerHTML = `
                <input type="text" name="${e.target.closest('.add-responsibility').parentElement.querySelector('input').name}">
                <button type="button" class="remove-responsibility">
                    <i class="fas fa-times"></i>
                </button>
            `;
        container.appendChild(newItem);
    }
});

// Auto-update preview on save
document.getElementById('cv-form').addEventListener('submit', function (e) {
    e.preventDefault();

    // Convert form data to a plain object
    const formData = new FormData(this);
    const formObject = Object.fromEntries(formData.entries());

    fetch("{{ url_for('dashboard.save_cv') }}", {
        method: 'POST',
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(formObject)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Refresh the preview iframe
                document.querySelector('.preview-iframe').contentWindow.location.reload();

                // Show success message
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert success';
                alertDiv.innerHTML = '<p>CV saved successfully!</p>';
                document.querySelector('.cv-editor').insertBefore(alertDiv, document.querySelector('.cv-editor h2').nextSibling);

                // Remove alert after 3 seconds
                setTimeout(() => alertDiv.remove(), 3000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Show error message to user
        });
});