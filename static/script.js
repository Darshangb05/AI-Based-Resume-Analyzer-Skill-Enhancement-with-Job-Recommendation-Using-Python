document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnText = analyzeBtn.querySelector('.btn-text');
    const loading = analyzeBtn.querySelector('.loading');
    const fileInput = document.getElementById('resume');
    
    // File input validation
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const fileSize = file.size / 1024 / 1024; // MB
            const fileType = file.name.split('.').pop().toLowerCase();
            
            if (fileSize > 5) {
                alert('File size must be less than 5MB');
                this.value = '';
                return;
            }
            
            if (!['pdf', 'docx'].includes(fileType)) {
                alert('Only PDF and DOCX files are allowed');
                this.value = '';
                return;
            }
        }
    });
    
    // Form submission
    form.addEventListener('submit', function(e) {
        const file = fileInput.files[0];
        const jobTitle = document.getElementById('job_title').value;
        
        if (!file || !jobTitle) {
            e.preventDefault();
            alert('Please fill in all required fields');
            return;
        }
        
        // Show loading state
        analyzeBtn.disabled = true;
        btnText.style.display = 'none';
        loading.style.display = 'flex';
    });
    
    // Drag and drop functionality
    const uploadSection = document.querySelector('.upload-section');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadSection.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadSection.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadSection.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        uploadSection.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        uploadSection.classList.remove('drag-over');
    }
    
    uploadSection.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    }
});

// Add drag-over styles
const style = document.createElement('style');
style.textContent = `
    .upload-section.drag-over {
        border: 2px dashed #667eea;
        background: rgba(102, 126, 234, 0.05);
        transform: scale(1.02);
    }
`;
document.head.appendChild(style);
