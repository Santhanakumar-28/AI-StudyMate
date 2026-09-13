/**
 * AI StudyMate - Upload Manager & Processing Trigger
 */

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('pdf-file-input');
  const browseBtn = document.getElementById('browse-btn');
  const selectedFileCard = document.getElementById('selected-file-card');
  const fileNameDisplay = document.getElementById('file-name-display');
  const fileSizeDisplay = document.getElementById('file-size-display');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const continueBtn = document.getElementById('continue-upload-btn');
  const sampleDemoBtn = document.getElementById('sample-demo-btn');

  let selectedFile = null;

  if (browseBtn && fileInput) {
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => {
      fileInput.click();
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        handleFileSelection(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
      }
    });
  }

  function handleFileSelection(file) {
    // Validate PDF extension
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      UI.showToast('Please select a valid PDF document (.pdf).', 'error');
      return;
    }

    // Validate size (20 MB)
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > 20) {
      UI.showToast(`File size (${sizeMb.toFixed(1)} MB) exceeds 20 MB limit.`, 'error');
      return;
    }

    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = `${sizeMb.toFixed(2)} MB`;

    dropzone.style.display = 'none';
    selectedFileCard.style.display = 'block';
    UI.showToast('PDF selected. Click Continue to analyze concepts.', 'info');
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener('click', () => {
      selectedFile = null;
      if (fileInput) fileInput.value = '';
      selectedFileCard.style.display = 'none';
      dropzone.style.display = 'block';
    });
  }

  if (continueBtn) {
    continueBtn.addEventListener('click', async () => {
      if (!selectedFile) {
        UI.showToast('Please select a PDF file first.', 'warning');
        return;
      }

      continueBtn.disabled = true;
      continueBtn.innerHTML = `<span>Uploading...</span>`;

      const formData = new FormData();
      formData.append('pdf_file', selectedFile);

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });

        const data = await response.json();
        if (data.success) {
          window.location.href = data.redirect_url || '/processing';
        } else {
          UI.showToast(data.error || 'Failed to upload file.', 'error');
          continueBtn.disabled = false;
          continueBtn.textContent = 'Continue to Processing';
        }
      } catch (err) {
        UI.showToast('Network error during upload. Please try again.', 'error');
        continueBtn.disabled = false;
        continueBtn.textContent = 'Continue to Processing';
      }
    });
  }

  if (sampleDemoBtn) {
    sampleDemoBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      sampleDemoBtn.disabled = true;
      sampleDemoBtn.innerHTML = `<span>Loading ML Sample...</span>`;

      try {
        const res = await fetch('/api/sample-demo', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          window.location.href = data.redirect_url || '/processing';
        } else {
          UI.showToast('Failed to load sample demo.', 'error');
          sampleDemoBtn.disabled = false;
        }
      } catch (err) {
        UI.showToast('Network error loading demo.', 'error');
        sampleDemoBtn.disabled = false;
      }
    });
  }
});
