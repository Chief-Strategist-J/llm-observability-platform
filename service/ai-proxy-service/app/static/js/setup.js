document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('setup-form');
    const responseDiv = document.getElementById('response');
    const submitButton = form.querySelector('.submit-button');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get all form values
        const formData = new FormData(form);
        const config = {};

        // Collect all provider keys
        const openaiKey = document.getElementById('openai_key').value.trim();
        const anthropicKey = document.getElementById('anthropic_key').value.trim();
        const grokKey = document.getElementById('grok_key').value.trim();
        const cloudflareToken = document.getElementById('cloudflare_token').value.trim();
        const cloudflareAccount = document.getElementById('cloudflare_account').value.trim();

        // Build request payload - only include non-empty values
        if (openaiKey) config.openai_key = openaiKey;
        if (anthropicKey) config.anthropic_key = anthropicKey;
        if (grokKey) config.grok_key = grokKey;
        if (cloudflareToken) config.cloudflare_token = cloudflareToken;
        if (cloudflareAccount) config.cloudflare_account = cloudflareAccount;

        // Validate that at least one key is provided
        if (Object.keys(config).length === 0) {
            showResponse('Please provide at least one API key.', 'error');
            return;
        }

        // Disable button and show loading state
        submitButton.disabled = true;
        submitButton.textContent = 'Saving...';

        try {
            const response = await fetch('/setup-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (response.ok) {
                showResponse(data.message || 'All configurations saved successfully!', 'success');

                // Wait 2 seconds then redirect to FastAPI docs
                setTimeout(() => {
                    window.location.href = '/docs';
                }, 2000);
            } else {
                showResponse(data.message || 'Error saving configurations.', 'error');
            }
        } catch (error) {
            showResponse('Network error occurred. Please try again.', 'error');
            console.error('Setup error:', error);
        } finally {
            // Re-enable button
            submitButton.disabled = false;
            submitButton.textContent = 'Save Configuration';
        }
    });

    function showResponse(message, type) {
        responseDiv.textContent = message;
        responseDiv.className = `response-message ${type}`;
    }

    // Add input validation and visual feedback
    const inputs = form.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            if (input.value.trim()) {
                input.style.borderColor = '#22c55e';
            } else {
                input.style.borderColor = '';
            }
        });
    });
});
