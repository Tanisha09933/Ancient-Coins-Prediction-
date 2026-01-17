document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById('searchInput');
    const fileInput = document.getElementById('coinInput');
    const loadingMessage = document.getElementById('loading-message');

    // Get references for the text search results
    const textResultsContainer = document.getElementById('results-container');
    const dbResultsSection = document.getElementById('database-results-section');
    const dbResultsContainer = document.getElementById('database-results');
    const webResultsSection = document.getElementById('web-results-section');
    const webResultsContainer = document.getElementById('web-results');

    // Get references for the NEW image identification results
    const imageIdResultsContainer = document.getElementById('image-id-results-container');
    const coinPreviewImage = document.getElementById('coinPreview');
    const aiPredictionResultContainer = document.getElementById('ai-prediction-result');


    // --- TEXT SEARCH FUNCTIONALITY ---
    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) { return; }

        // Clear image results and show loading message in the main container
        imageIdResultsContainer.style.display = 'none';
        clearResultsAndShowLoading('Searching our database and the web...', textResultsContainer);

        try {
            const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
            await handleApiResponse(response);
        } catch (error) {
            handleFetchError(error);
        } finally {
            loadingMessage.style.display = 'none';
        }
    };

    // --- AI IMAGE IDENTIFICATION FUNCTIONALITY ---
    const identifyByImage = async (file) => {
        if (!file) return;

        // Clear text search results and show loading message
        textResultsContainer.style.display = 'none';
        clearResultsAndShowLoading('Uploading image and running AI analysis...', imageIdResultsContainer);

        const formData = new FormData();
        formData.append('coin_image', file);

        try {
            const response = await fetch('/api/ai-identify', {
                method: 'POST',
                body: formData
            });
            await handleApiResponse(response, true);
        } catch (error) {
            handleFetchError(error);
        } finally {
             loadingMessage.style.display = 'none';
        }
    };

    // --- HELPER FUNCTIONS ---
    const clearResultsAndShowLoading = (message, containerToShow) => {
        loadingMessage.textContent = message;
        containerToShow.prepend(loadingMessage); // Move loading message to the correct container
        loadingMessage.style.display = 'block';

        // Hide all result sections
        dbResultsSection.style.display = 'none';
        webResultsSection.style.display = 'none';
        aiPredictionResultContainer.innerHTML = '';
        dbResultsContainer.innerHTML = '';
        webResultsContainer.innerHTML = '';
    };

    const handleApiResponse = async (response, isAiResponse = false) => {
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (isAiResponse && data.ai_prediction) {
            displayAiPrediction(data.ai_prediction);
        } else {
            // If it's a text search, ensure the AI-specific container is hidden
            imageIdResultsContainer.style.display = 'none';
        }

        // These will now only be called if there's data for them
        displayDatabaseResults(data.database_results || []);
        displayWebResults(data.web_results || []);
    };

    const handleFetchError = (error) => {
        console.error('Fetch error:', error);
        clearResultsAndShowLoading('');
        textResultsContainer.style.display = 'block';
        webResultsContainer.innerHTML = `<div class="result-card"><p class="error-message">Error: ${error.message}</p></div>`;
        webResultsSection.style.display = 'block';
    };

    // --- EVENT LISTENERS ---
    searchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') performSearch();
    });

    fileInput.addEventListener('change', (event) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            showPreview(event);
            identifyByImage(file);
        }
    });

    // --- DISPLAY FUNCTIONS ---
    const displayAiPrediction = (prediction) => {
        const predictionText = `AI Prediction: <strong>${prediction.predicted_class}</strong> (Confidence: ${prediction.probability})`;
        aiPredictionResultContainer.innerHTML = `<div class="ai-prediction-info">${predictionText}</div>`;
        imageIdResultsContainer.style.display = 'block';
    };

    const displayDatabaseResults = (results) => {
        if (results.length > 0) {
            dbResultsContainer.innerHTML = ''; // Clear previous
            results.forEach(item => {
                const card = document.createElement('div');
                card.className = 'result-card db-result';
                const imageHtml = item.image_url
                    ? `<div class="db-coin-image-container"><img src="${item.image_url}" alt="Image of ${item.code}" class="db-coin-image"></div>`
                    : '';
                card.innerHTML = `
                    <div class="db-result-content">
                        ${imageHtml}
                        <div class="db-coin-details">
                            <h3>${item.king_name} - ${item.dynasty}</h3>
                            <p class="coin-code">Code: ${item.code}</p>
                            <p>${item.details}</p>
                        </div>
                    </div>`;
                dbResultsContainer.appendChild(card);
            });
            textResultsContainer.style.display = 'block';
            dbResultsSection.style.display = 'block';
        }
    };

    const displayWebResults = (results) => {
        if (results.length > 0) {
            webResultsContainer.innerHTML = ''; // Clear previous
            results.forEach(item => {
                const card = document.createElement('div');
                card.className = 'result-card web-result';
                const summary = item.full_text && item.full_text.length > 10 ?
                                item.full_text.substring(0, 300) + '...' :
                                item.snippet;
                card.innerHTML = `
                    <h3>${item.title} <span class="engine-tag">${item.engine}</span></h3>
                    <p>${summary}</p>
                    <a href="${item.link}" target="_blank" class="read-more">Read more on their site</a>`;
                webResultsContainer.appendChild(card);
            });
            textResultsContainer.style.display = 'block';
            webResultsSection.style.display = 'block';
        }
    };
});

function showPreview(event) {
    const input = event.target;
    const preview = document.getElementById("coinPreview");
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            preview.style.display = "block"; // Make the preview image visible
            imageIdResultsContainer.style.display = 'block'; // Make its container visible too
        };
        reader.readAsDataURL(input.files[0]);
    }
}

