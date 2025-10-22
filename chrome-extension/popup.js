document.addEventListener('DOMContentLoaded', async function() {
    const generateBtn = document.getElementById('generateBtn');
    const status = document.getElementById('status');
    const preview = document.getElementById('preview');
    const previewContent = document.getElementById('preview-content');
    const arrivalTimeInput = document.getElementById('arrivalTime');
    const scatteringMinutesInput = document.getElementById('scatteringMinutes');
    
    // Default settings
    const defaultSettings = {
        arrivalTime: '09:00',
        scatteringMinutes: 10
    };
    
    // Load saved settings
    async function loadSettings() {
        try {
            const result = await chrome.storage.sync.get(defaultSettings);
            arrivalTimeInput.value = result.arrivalTime;
            scatteringMinutesInput.value = result.scatteringMinutes;
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    // Save settings when changed
    async function saveSettings() {
        try {
            const settings = {
                arrivalTime: arrivalTimeInput.value,
                scatteringMinutes: parseInt(scatteringMinutesInput.value) || 0
            };
            await chrome.storage.sync.set(settings);
            console.log('Settings saved:', settings);
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }
    
    // Load settings on startup
    await loadSettings();
    
    // Save settings when inputs change
    arrivalTimeInput.addEventListener('change', saveSettings);
    scatteringMinutesInput.addEventListener('change', saveSettings);
    
    // Check if we're on the right page
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab.url.includes('bWorkflowActivityIjstimeentry.ashx') && !tab.url.includes('Stroškovnik')) {
            status.className = 'status error';
            status.textContent = 'Please navigate to a Stroskovnik timesheet page first';
            generateBtn.disabled = true;
            return;
        }
        
        // Get preview data from content script
        chrome.tabs.sendMessage(tab.id, { action: 'getPreview' }, (response) => {
            console.log('Preview response:', response);
            
            if (chrome.runtime.lastError) {
                status.className = 'status error';
                status.textContent = 'Cannot connect to page. Please refresh and try again.';
                generateBtn.disabled = true;
            } else if (response && response.success && response.data) {
                status.className = 'status success';
                status.textContent = 'Timesheet data detected';
                previewContent.textContent = `Name: ${response.data.name}\nPeriod: ${response.data.period}\nWorking days: ${response.data.workingDays}`;
                preview.classList.remove('hidden');
            } else {
                status.className = 'status error';
                status.textContent = 'No timesheet data found on this page';
                generateBtn.disabled = true;
            }
        });
        
    } catch (error) {
        status.className = 'status error';
        status.textContent = 'Error checking page compatibility';
        generateBtn.disabled = true;
    }
    
    generateBtn.addEventListener('click', async function() {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            // Add timeout for message response
            const timeoutId = setTimeout(() => {
                status.className = 'status error';
                status.textContent = 'Generation timed out. Please try again.';
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate PDF';
            }, 10000); // 10 second timeout
            
            chrome.tabs.sendMessage(tab.id, { action: 'generatePDF' }, (response) => {
                clearTimeout(timeoutId);
                
                if (chrome.runtime.lastError) {
                    status.className = 'status error';
                    status.textContent = 'Connection error: ' + chrome.runtime.lastError.message;
                } else if (response && response.success) {
                    status.className = 'status success';
                    status.textContent = 'PDF generated successfully!';
                } else {
                    status.className = 'status error';
                    status.textContent = response ? response.error : 'Failed to generate PDF';
                }
                
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate PDF';
                
                // Close popup after 2 seconds if successful
                if (response && response.success) {
                    setTimeout(() => window.close(), 2000);
                }
            });
            
        } catch (error) {
            status.className = 'status error';
            status.textContent = 'Error: ' + error.message;
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate PDF';
        }
    });
});