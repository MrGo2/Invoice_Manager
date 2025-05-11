document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('id_file');
    const dropzone = document.getElementById('dropzone');
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const removeFileBtn = document.getElementById('remove-file');
    const submitButton = document.getElementById('submit-button');
    const submitText = document.getElementById('submit-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    const uploadForm = document.getElementById('upload-form');

    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Update file preview
    function updateFilePreview(file) {
        if (file) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            filePreview.classList.remove('hidden');
            submitButton.disabled = false;
        } else {
            filePreview.classList.add('hidden');
            submitButton.disabled = true;
        }
    }

    // Handle file input change
    fileInput.addEventListener('change', function(e) {
        if (this.files.length > 0) {
            updateFilePreview(this.files[0]);
        }
    });

    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropzone.classList.add('dropzone-active');
    }

    function unhighlight() {
        dropzone.classList.remove('dropzone-active');
    }

    dropzone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            updateFilePreview(files[0]);
        }
    }

    // Handle file removal
    removeFileBtn.addEventListener('click', function() {
        fileInput.value = '';
        filePreview.classList.add('hidden');
        submitButton.disabled = true;
    });

    // Form submission
    uploadForm.addEventListener('submit', function() {
        submitButton.disabled = true;
        submitText.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
    });
});
