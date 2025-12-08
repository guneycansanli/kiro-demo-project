/**
 * Weather Web Service - Frontend Application
 * 
 * This module handles all frontend interactions including search,
 * autocomplete, geolocation, and weather display.
 */

// ============================================================================
// API Client Functions
// ============================================================================

/**
 * Fetch weather data by location query
 * @param {string} location - Location query (city, zip code, etc.)
 * @returns {Promise<Object>} Weather data
 */
async function fetchWeather(location) {
    try {
        const response = await fetch(`/api/weather?location=${encodeURIComponent(location)}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to fetch weather data');
        }
        
        return await response.json();
    } catch (error) {
        if (error.message.includes('Failed to fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}

/**
 * Fetch weather data by coordinates
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {Promise<Object>} Weather data
 */
async function fetchWeatherByCoordinates(lat, lon) {
    try {
        const response = await fetch(`/api/weather/coordinates?lat=${lat}&lon=${lon}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to fetch weather data');
        }
        
        return await response.json();
    } catch (error) {
        if (error.message.includes('Failed to fetch')) {
            throw new Error('Network error: Unable to connect to the server');
        }
        throw error;
    }
}

/**
 * Fetch autocomplete suggestions
 * @param {string} query - Search query
 * @returns {Promise<Array>} Array of location suggestions
 */
async function fetchAutocomplete(query) {
    try {
        const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch autocomplete suggestions');
        }
        
        const data = await response.json();
        return data.suggestions || [];
    } catch (error) {
        console.error('Autocomplete error:', error);
        return [];
    }
}

// ============================================================================
// SearchInterface Class
// ============================================================================

class SearchInterface {
    constructor(inputId, suggestionsId) {
        this.input = document.getElementById(inputId);
        this.suggestionsContainer = document.getElementById(suggestionsId);
        this.suggestions = [];
        this.selectedIndex = -1;
        this.debounceTimer = null;
        this.onSearchCallback = null;
        
        this.setupEventListeners();
    }
    
    /**
     * Set up event listeners for search input
     */
    setupEventListeners() {
        // Input event with debouncing
        this.input.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            // Clear previous timer
            if (this.debounceTimer) {
                clearTimeout(this.debounceTimer);
            }
            
            // Debounce autocomplete requests (300ms)
            if (query.length > 0) {
                this.debounceTimer = setTimeout(() => {
                    this.fetchAndShowSuggestions(query);
                }, 300);
            } else {
                this.hideSuggestions();
            }
        });
        
        // Enter key to submit search
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                
                if (this.selectedIndex >= 0 && this.suggestions[this.selectedIndex]) {
                    // Select highlighted suggestion
                    this.selectSuggestion(this.suggestions[this.selectedIndex]);
                } else if (this.input.value.trim()) {
                    // Search with current input value
                    this.hideSuggestions();
                    if (this.onSearchCallback) {
                        this.onSearchCallback(this.input.value.trim());
                    }
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.navigateSuggestions(1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateSuggestions(-1);
            } else if (e.key === 'Escape') {
                this.hideSuggestions();
            }
        });
        
        // Click outside to close suggestions
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.suggestionsContainer.contains(e.target)) {
                this.hideSuggestions();
            }
        });
    }
    
    /**
     * Fetch and display autocomplete suggestions
     * @param {string} query - Search query
     */
    async fetchAndShowSuggestions(query) {
        try {
            const suggestions = await fetchAutocomplete(query);
            this.showSuggestions(suggestions);
        } catch (error) {
            console.error('Failed to fetch suggestions:', error);
            this.hideSuggestions();
        }
    }
    
    /**
     * Display autocomplete suggestions
     * @param {Array} suggestions - Array of suggestion objects
     */
    showSuggestions(suggestions) {
        this.suggestions = suggestions;
        this.selectedIndex = -1;
        
        if (suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        // Build suggestions HTML
        const html = suggestions.map((suggestion, index) => `
            <div class="suggestion-item" data-index="${index}">
                <div class="suggestion-name">${this.escapeHtml(suggestion.display_name)}</div>
                <div class="suggestion-type">${this.escapeHtml(suggestion.type)}</div>
            </div>
        `).join('');
        
        this.suggestionsContainer.innerHTML = html;
        this.suggestionsContainer.style.display = 'block';
        
        // Add click handlers to suggestions
        this.suggestionsContainer.querySelectorAll('.suggestion-item').forEach((item) => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.selectSuggestion(this.suggestions[index]);
            });
        });
    }
    
    /**
     * Hide autocomplete suggestions
     */
    hideSuggestions() {
        this.suggestionsContainer.style.display = 'none';
        this.suggestionsContainer.innerHTML = '';
        this.suggestions = [];
        this.selectedIndex = -1;
    }
    
    /**
     * Navigate through suggestions with keyboard
     * @param {number} direction - 1 for down, -1 for up
     */
    navigateSuggestions(direction) {
        if (this.suggestions.length === 0) return;
        
        // Remove previous highlight
        const items = this.suggestionsContainer.querySelectorAll('.suggestion-item');
        if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
            items[this.selectedIndex].classList.remove('active');
        }
        
        // Update selected index
        this.selectedIndex += direction;
        
        // Wrap around
        if (this.selectedIndex < 0) {
            this.selectedIndex = this.suggestions.length - 1;
        } else if (this.selectedIndex >= this.suggestions.length) {
            this.selectedIndex = 0;
        }
        
        // Highlight new selection
        if (items[this.selectedIndex]) {
            items[this.selectedIndex].classList.add('active');
            items[this.selectedIndex].scrollIntoView({ block: 'nearest' });
        }
    }
    
    /**
     * Select a suggestion and trigger search
     * @param {Object} suggestion - Selected suggestion object
     */
    selectSuggestion(suggestion) {
        this.input.value = suggestion.display_name;
        this.hideSuggestions();
        
        if (this.onSearchCallback) {
            this.onSearchCallback(suggestion.display_name);
        }
    }
    
    /**
     * Set callback for search events
     * @param {Function} callback - Function to call when search is triggered
     */
    onSearch(callback) {
        this.onSearchCallback = callback;
    }
    
    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// ============================================================================
// GeolocationHandler Class
// ============================================================================

class GeolocationHandler {
    constructor() {
        this.onSuccessCallback = null;
        this.onErrorCallback = null;
    }
    
    /**
     * Request user's current location
     */
    requestLocation() {
        if (!navigator.geolocation) {
            const error = new Error('Geolocation is not supported by your browser');
            if (this.onErrorCallback) {
                this.onErrorCallback(error);
            }
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                if (this.onSuccessCallback) {
                    this.onSuccessCallback(position.coords.latitude, position.coords.longitude);
                }
            },
            (error) => {
                let errorMessage = 'Unable to retrieve your location';
                
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location access denied. Please enable location permissions.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information is unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out.';
                        break;
                }
                
                if (this.onErrorCallback) {
                    this.onErrorCallback(new Error(errorMessage));
                }
            },
            {
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 300000 // 5 minutes
            }
        );
    }
    
    /**
     * Set success callback
     * @param {Function} callback - Function to call on success (lat, lon)
     */
    onSuccess(callback) {
        this.onSuccessCallback = callback;
    }
    
    /**
     * Set error callback
     * @param {Function} callback - Function to call on error
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }
}

// ============================================================================
// WeatherDisplay Class
// ============================================================================

class WeatherDisplay {
    constructor(displayId, errorId) {
        this.displayContainer = document.getElementById(displayId);
        this.errorContainer = document.getElementById(errorId);
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        this.hideError();
        this.displayContainer.innerHTML = '<div class="loading">Loading weather data</div>';
    }
    
    /**
     * Display weather data
     * @param {Object} data - Weather data object
     */
    showWeather(data) {
        this.hideError();
        
        const weather = data.weather;
        const location = data.location;
        const advisory = data.advisory;
        
        // Get weather icon based on conditions
        const iconClass = this.getWeatherIcon(weather.conditions);
        
        let html = `
            <div class="weather-card">
                <div class="weather-location">
                    <span class="icon-location"></span>
                    ${this.escapeHtml(location.name)}
                </div>
                
                <div class="weather-icon ${iconClass}"></div>
                
                <div class="weather-temp">
                    ${weather.temp_f}°F / ${weather.temp_c}°C
                </div>
                
                <div class="weather-conditions">
                    ${this.escapeHtml(weather.conditions)}
                </div>
                
                <div class="weather-metrics">
                    <div class="weather-metric">
                        <span class="weather-metric-icon icon-rain"></span>
                        <div>
                            <span class="weather-metric-label">Rain Chance</span>
                            <div class="weather-metric-value">${weather.rain_chance}%</div>
                        </div>
                    </div>
                    
                    <div class="weather-metric">
                        <span class="weather-metric-icon icon-humidity"></span>
                        <div>
                            <span class="weather-metric-label">Humidity</span>
                            <div class="weather-metric-value">${weather.humidity}%</div>
                        </div>
                    </div>
                    
                    <div class="weather-metric">
                        <span class="weather-metric-icon icon-wind"></span>
                        <div>
                            <span class="weather-metric-label">Wind Speed</span>
                            <div class="weather-metric-value">${this.escapeHtml(weather.wind_speed)}</div>
                        </div>
                    </div>
                </div>
        `;
        
        // Add advisory or no advisory message
        if (advisory) {
            html += this.getAdvisoryHtml(advisory);
        } else {
            html += '<div class="no-advisory">No active weather advisories</div>';
        }
        
        html += '</div>';
        
        this.displayContainer.innerHTML = html;
    }
    
    /**
     * Get advisory HTML
     * @param {Object} advisory - Advisory object
     * @returns {string} HTML string
     */
    getAdvisoryHtml(advisory) {
        const severityClass = advisory.severity.toLowerCase();
        
        return `
            <div class="advisory-banner ${severityClass}">
                <div class="advisory-type">
                    <span class="severity-indicator ${severityClass}"></span>
                    ${this.escapeHtml(advisory.type)}
                </div>
                <div class="advisory-description">
                    ${this.escapeHtml(advisory.description)}
                </div>
            </div>
        `;
    }
    
    /**
     * Get weather icon class based on conditions
     * @param {string} conditions - Weather conditions text
     * @returns {string} Icon class name
     */
    getWeatherIcon(conditions) {
        const lower = conditions.toLowerCase();
        
        if (lower.includes('sunny') || lower.includes('clear')) {
            return 'icon-sunny';
        } else if (lower.includes('partly cloudy') || lower.includes('partly sunny')) {
            return 'icon-partly-cloudy';
        } else if (lower.includes('cloudy') || lower.includes('overcast')) {
            return 'icon-cloudy';
        } else if (lower.includes('rain') || lower.includes('shower')) {
            return 'icon-rainy';
        } else if (lower.includes('storm') || lower.includes('thunder')) {
            return 'icon-stormy';
        } else if (lower.includes('snow') || lower.includes('flurr')) {
            return 'icon-snowy';
        } else if (lower.includes('fog') || lower.includes('mist')) {
            return 'icon-foggy';
        } else if (lower.includes('wind')) {
            return 'icon-windy';
        }
        
        return 'icon-partly-cloudy'; // Default
    }
    
    /**
     * Display error message
     * @param {string} message - Error message
     * @param {Function} retryCallback - Optional callback for retry button
     */
    showError(message, retryCallback = null) {
        this.displayContainer.innerHTML = '';
        
        let html = `<div class="error-message">${this.escapeHtml(message)}</div>`;
        
        if (retryCallback) {
            html += '<button class="retry-button">Retry</button>';
        }
        
        this.errorContainer.innerHTML = html;
        this.errorContainer.style.display = 'block';
        
        if (retryCallback) {
            const retryButton = this.errorContainer.querySelector('.retry-button');
            if (retryButton) {
                retryButton.addEventListener('click', retryCallback);
            }
        }
    }
    
    /**
     * Hide error message
     */
    hideError() {
        this.errorContainer.style.display = 'none';
        this.errorContainer.innerHTML = '';
    }
    
    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// ============================================================================
// Application Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Weather Web Service initialized');
    
    // Initialize components
    const searchInterface = new SearchInterface('search-input', 'autocomplete-suggestions');
    const geolocationHandler = new GeolocationHandler();
    const weatherDisplay = new WeatherDisplay('weather-display', 'error-display');
    
    // Handle search submissions
    searchInterface.onSearch(async (location) => {
        weatherDisplay.showLoading();
        
        try {
            const data = await fetchWeather(location);
            weatherDisplay.showWeather(data);
        } catch (error) {
            weatherDisplay.showError(error.message, () => {
                searchInterface.onSearchCallback(location);
            });
        }
    });
    
    // Handle current location button
    const currentLocationBtn = document.getElementById('current-location-btn');
    if (currentLocationBtn) {
        currentLocationBtn.addEventListener('click', () => {
            weatherDisplay.showLoading();
            
            geolocationHandler.onSuccess(async (lat, lon) => {
                try {
                    const data = await fetchWeatherByCoordinates(lat, lon);
                    weatherDisplay.showWeather(data);
                } catch (error) {
                    weatherDisplay.showError(error.message, () => {
                        currentLocationBtn.click();
                    });
                }
            });
            
            geolocationHandler.onError((error) => {
                weatherDisplay.showError(error.message);
            });
            
            geolocationHandler.requestLocation();
        });
    }
    
    // Focus search input on page load
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.focus();
    }
});
