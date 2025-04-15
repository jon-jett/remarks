// Get the current user's default download path
const defaultPath = `/Users/${process.env.USER}/Movies/remarks/library`;

document.addEventListener('DOMContentLoaded', function() {
    const downloadLocationInput = document.getElementById('downloadLocation');
    const browseButton = document.getElementById('browseButton');
    const videoUrlInput = document.getElementById('videoUrl');
    const downloadButton = document.getElementById('downloadButton');
    const statusDiv = document.getElementById('status');

    // Set default download location - we'll get this from the backend
    fetch('http://localhost:8000/default-path')
        .then(response => response.json())
        .then(data => {
            downloadLocationInput.value = data.path;
        })
        .catch(error => {
            console.error('Error fetching default path:', error);
            downloadLocationInput.value = '/Users/adamderstine/Movies/remarks/library'; // Fallback
        });

    // Make the input editable
    downloadLocationInput.removeAttribute('readonly');

    // Handle directory selection
    browseButton.addEventListener('click', () => {
        // Create an input element of type 'file'
        const dirPicker = document.createElement('input');
        dirPicker.type = 'file';
        // Allow directory selection
        dirPicker.setAttribute('webkitdirectory', '');
        dirPicker.setAttribute('directory', '');

        dirPicker.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                // Get the path of the first file in the selected directory
                const path = e.target.files[0].webkitRelativePath.split('/')[0];
                downloadLocationInput.value = path;
            }
        });

        dirPicker.click();
    });

    // Handle download
    downloadButton.addEventListener('click', async () => {
        const url = videoUrlInput.value.trim();
        const downloadLocation = downloadLocationInput.value;

        if (!url) {
            statusDiv.textContent = 'Please enter a video URL';
            return;
        }

        statusDiv.textContent = 'Downloading...';

        try {
            const response = await fetch('http://localhost:8000/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    download_dir: downloadLocation
                })
            });

            const data = await response.json();

            if (data.success) {
                statusDiv.textContent = `Download complete! File saved to: ${data.file_path}`;
            } else {
                statusDiv.textContent = `Download failed: ${data.error}`;
            }
        } catch (error) {
            statusDiv.textContent = `Error: ${error.message}`;
        }
    });

    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        });
    });
});