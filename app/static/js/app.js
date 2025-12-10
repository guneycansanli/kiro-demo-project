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
        
        // Build suggestions HTML with enhanced styling and icons
        const html = suggestions.map((suggestion, index) => {
            const icon = this.getLocationIcon(suggestion.type);
            const typeLabel = this.getTypeLabel(suggestion.type);
            
            return `
                <div class="suggestion-item cursor-pointer px-4 py-3 hover:bg-gray-100 border-b border-gray-100 last:border-b-0 flex items-center space-x-3" data-index="${index}">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                ${icon}
                            </svg>
                        </div>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-gray-900 truncate">${this.escapeHtml(suggestion.display_name)}</div>
                        <div class="text-xs text-gray-500">${typeLabel}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        this.suggestionsContainer.innerHTML = html;
        this.suggestionsContainer.classList.remove('hidden');
        
        // Add click handlers to suggestions
        this.suggestionsContainer.querySelectorAll('.suggestion-item').forEach((item) => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.selectSuggestion(this.suggestions[index]);
            });
        });
    }
    
    /**
     * Get appropriate icon for location type
     * @param {string} type - Location type
     * @returns {string} SVG path for icon
     */
    getLocationIcon(type) {
        switch (type) {
            case 'city':
                return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>';
            case 'country':
                return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>';
            case 'state':
                return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>';
            case 'postal_code':
            case 'zip':
                return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>';
            case 'region':
                return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m0 0L9 7"></path>';
            default:
                return '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>';
        }
    }
    
    /**
     * Get user-friendly label for location type
     * @param {string} type - Location type
     * @returns {string} Display label
     */
    getTypeLabel(type) {
        switch (type) {
            case 'city':
                return 'City';
            case 'country':
                return 'Country';
            case 'state':
                return 'State/Province';
            case 'postal_code':
            case 'zip':
                return 'Postal Code';
            case 'region':
                return 'Region';
            default:
                return 'Location';
        }
    }
    
    /**
     * Hide autocomplete suggestions
     */
    hideSuggestions() {
        this.suggestionsContainer.classList.add('hidden');
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
            items[this.selectedIndex].classList.remove('bg-blue-100');
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
            items[this.selectedIndex].classList.add('bg-blue-100');
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
    constructor() {
        this.displayContainer = document.getElementById('weather-display');
        this.errorContainer = document.getElementById('error-display');
        this.loadingContainer = document.getElementById('loading-display');
        
        // Individual elements
        this.weatherTitle = document.getElementById('weather-title');
        this.weatherLocation = document.getElementById('weather-location');
        this.weatherImage = document.getElementById('weather-image');
        this.temperatureDisplay = document.getElementById('temperature-display');
        this.conditionsDisplay = document.getElementById('conditions-display');
        this.rainChanceDisplay = document.getElementById('rain-chance-display');
        this.humidityDisplay = document.getElementById('humidity-display');
        this.windSpeedDisplay = document.getElementById('wind-speed-display');
        this.advisoryDisplay = document.getElementById('advisory-display');
        this.advisoryType = document.getElementById('advisory-type');
        this.advisoryDescription = document.getElementById('advisory-description');
        this.errorMessage = document.getElementById('error-message');
        this.retryBtn = document.getElementById('retry-btn');
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        this.hideError();
        this.hideWeather();
        this.loadingContainer.classList.remove('hidden');
    }
    
    /**
     * Hide loading state
     */
    hideLoading() {
        this.loadingContainer.classList.add('hidden');
    }
    
    /**
     * Display weather data
     * @param {Object} data - Weather data object
     */
    showWeather(data) {
        this.hideError();
        this.hideLoading();
        
        const weather = data.weather;
        const location = data.location;
        const advisory = data.advisory;
        
        // Update location information
        this.weatherLocation.textContent = location.name;
        
        // Update weather background image
        const backgroundImage = this.getWeatherBackgroundImage(weather.conditions);
        this.weatherImage.style.backgroundImage = `url("${backgroundImage}")`;
        
        // Update header weather icon based on conditions
        this.updateHeaderWeatherIcon(weather.conditions);
        
        // Update temperature (show both F and C)
        this.temperatureDisplay.textContent = `${weather.temp_f}°F (${weather.temp_c}°C)`;
        
        // Update weather metrics
        this.conditionsDisplay.textContent = weather.conditions;
        this.rainChanceDisplay.textContent = `${weather.rain_chance}%`;
        this.humidityDisplay.textContent = `${weather.humidity}%`;
        this.windSpeedDisplay.textContent = weather.wind_speed;
        
        // Handle advisory
        if (advisory) {
            this.showAdvisory(advisory);
        } else {
            this.hideAdvisory();
        }
        
        // Show the weather display
        this.displayContainer.classList.remove('hidden');
    }
    
    /**
     * Update header weather icon using OpenWeatherMap icons
     * @param {string} conditions - Weather conditions text
     */
    updateHeaderWeatherIcon(conditions) {
        const headerIcon = document.getElementById('header-weather-icon');
        if (!headerIcon) return;
        
        // Show the icon container
        headerIcon.classList.remove('hidden');
        
        // Map weather conditions to OpenWeatherMap icon codes
        const iconCode = this.getWeatherIconCode(conditions);
        
        // Create img element for OpenWeatherMap icon
        const iconImg = document.createElement('img');
        iconImg.src = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
        iconImg.alt = conditions;
        iconImg.className = 'w-6 h-6';
        iconImg.title = conditions;
        
        // Replace content with the weather icon
        headerIcon.innerHTML = '';
        headerIcon.appendChild(iconImg);
    }
    
    /**
     * Map weather conditions to OpenWeatherMap icon codes
     * @param {string} conditions - Weather conditions text
     * @returns {string} OpenWeatherMap icon code
     */
    getWeatherIconCode(conditions) {
        const lower = conditions.toLowerCase();
        
        // Map conditions to OpenWeatherMap icon codes
        if (lower.includes('thunderstorm') || lower.includes('storm')) {
            return '11d'; // Thunderstorm
        } else if (lower.includes('drizzle')) {
            return '09d'; // Shower rain
        } else if (lower.includes('rain') || lower.includes('shower')) {
            if (lower.includes('light')) {
                return '10d'; // Light rain
            } else if (lower.includes('heavy')) {
                return '09d'; // Heavy rain
            } else {
                return '10d'; // Rain
            }
        } else if (lower.includes('snow') || lower.includes('flurr') || lower.includes('blizzard')) {
            return '13d'; // Snow
        } else if (lower.includes('mist') || lower.includes('fog') || lower.includes('haze')) {
            return '50d'; // Mist/Fog
        } else if (lower.includes('clear') || lower.includes('sunny')) {
            return '01d'; // Clear sky
        } else if (lower.includes('few clouds')) {
            return '02d'; // Few clouds
        } else if (lower.includes('scattered clouds')) {
            return '03d'; // Scattered clouds
        } else if (lower.includes('broken clouds') || lower.includes('overcast') || lower.includes('cloudy')) {
            return '04d'; // Broken clouds
        } else {
            // Default to partly cloudy for unknown conditions
            return '02d'; // Few clouds
        }
    }
    
    /**
     * Hide weather display
     */
    hideWeather() {
        this.displayContainer.classList.add('hidden');
    }
    
    /**
     * Show advisory information
     * @param {Object} advisory - Advisory object
     */
    showAdvisory(advisory) {
        this.advisoryType.textContent = advisory.type;
        this.advisoryDescription.textContent = advisory.description;
        
        // Update advisory styling based on severity
        const advisoryContainer = this.advisoryDisplay.querySelector('div');
        advisoryContainer.className = this.getAdvisoryClasses(advisory.severity);
        
        this.advisoryDisplay.classList.remove('hidden');
    }
    
    /**
     * Hide advisory display
     */
    hideAdvisory() {
        this.advisoryDisplay.classList.add('hidden');
    }
    
    /**
     * Get advisory CSS classes based on severity
     * @param {string} severity - Advisory severity
     * @returns {string} CSS classes
     */
    getAdvisoryClasses(severity) {
        const baseclasses = 'border-l-4 p-4 rounded';
        
        switch (severity.toLowerCase()) {
            case 'warning':
                return `${baseclasses} bg-red-100 border-red-500`;
            case 'watch':
                return `${baseclasses} bg-blue-100 border-blue-500`;
            case 'advisory':
            default:
                return `${baseclasses} bg-yellow-100 border-yellow-500`;
        }
    }
    
    /**
     * Get weather background image based on conditions
     * @param {string} conditions - Weather conditions text
     * @returns {string} Image URL
     */
    getWeatherBackgroundImage(conditions) {
        const lower = conditions.toLowerCase();
        
        // Default sunny/clear image
        let imageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuDmElNzdfzha9-u5B7plnFikM9co2ukEl39Hqrh3h6IfQACMY5h9WGXPsLGe5WI8mpgqFt-XWx2NIdDPt2fH8yps5mdcHUig9_pcfBANzwyncH-ySLOq_PG6uMMJlsQYxKdbe9uKfuO4agAOQTxjadUnG9C7XW0Cfb4rqWDbv7Onjr-Wjxngwz5pm8lc--58wL1zBFUXv9p15L41mL6nayb0RT_2m53nghqQk6n0k9yGWCDUCq497zZ2_spHFDE0Nf2tx7womNI0Ws";
        
        if (lower.includes('rain') || lower.includes('shower') || lower.includes('drizzle')) {
            // Rainy weather image
            imageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuC2ty2pgiQ_4goDnKZW2befYjrlKtr4-IRxCQEsHGNknnixWkDEAWL7H7I4c9PT1Sh5Or714K1bY6YjFmpdXkAk1nFQyVEKxmW8riRrw6tlPZMMx1Q7OokB0OkZN9cU4sd6N2sC8u8uhsWTvgtRajwTfnAsnlHcAbyzD1k1obpM_v0gPJTtAdW40NE2Pe8j82RKn4ynFha2cFLuWhmFAM2QTu8fS6ptO5iN41dshxQqWP882Kh4BVotxeXWNgwR-JlIDFSqy15kTd4";
        } else if (lower.includes('cloud') || lower.includes('overcast')) {
            // Cloudy weather image
            imageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuBPg8TwFq9YLEZdHUDYIaZmlUoU2bE-F3zoI9yF-TW6aSv45ovgq2jfIJMjIxUAlaGefUJXAeH3DL5kHy0TqMz_PzXhhcPf9drF8DWjwHToRbk9Du24PWgBrQnTkJymkwDuFlbnfaF9bSI67Sy-lpi3PnxD3z4uVaxk4HRWJF1qjYN7U74Y44i3tukcTE_Y9KfSEv3zPFP6xbgSCFz6Ush4nofTZykwunuP7HbCC9qUhoG_xyDXsNuLZYXgy2yiko2JbEkxJ3xCg88";
        } else if (lower.includes('storm') || lower.includes('thunder')) {
            // Stormy weather image
            imageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuDnnEMvLkT-_2aKEjVUIfBo1rKv5wH2MfzSHjog3QI0F8hr9H_kInBEErm4UVeovz_GqdTq6A4ew58CEg5kGgs_w10CNBRwLAoFDX1imowtCsGLUMUnmOKpwz168qlTHwJFTDB5rLI8_Iu3weSjcyh-y_XtGA67vjyydzp8SVHbrX8tfUmWBCOtWt32dKKbOky-JivqAbbm7ktl0oHaMjJpLXvjGqaErP4SGjW5RD8x2IPakxQcDj_PdQEhLczh3HdXfalfpMnc-bA";
        } else if (lower.includes('snow') || lower.includes('flurr') || lower.includes('blizzard')) {
            // Snowy weather image
            imageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuBmlBmzPgOWNfjh2Jh8taS3IN3--MBZtpm8-9UZnwRoduNDBzL_R4tNAtAjIW-NWuaQON6mbh98WJgMcb_hQBYIRuHn_PWNB-am3FBybeJkjtZNIUJ8mvLNLuD0faqwYwfyg_tqx9ZmVnI6KN1dvDz3eEeEfxxSYCBMxJmDvi1xDLGZgDK7bXNpQC-41N72Tojjhslp5PwogOtOxdp4llBspJGMMNskfE2twmQOfIGoe8ZR5JhB2IyDnmRyUS2sGVl_1Jrm1WlH1v8";
        } else if (lower.includes('fog') || lower.includes('mist') || lower.includes('haze')) {
            // Foggy weather image
            imageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuAQelCFsR5J_9lrLXO7Mqe7fddidxDJ6Q4BPeNYplonOPtkAJ_4WnK4AJAoY_B2WXrshhznXfVcvXIf4sqyNUy-DTL1xSV-w5DdG_aDtcJYYBKS4POIG6IzLKQ8y_A0_OvQz8C2cSE22G1hg33Hm-SSmQUAC7FZvYeWJ7t9WDftGU6oy_HPPJx6q09soUluLTgM_OA1EFZTIuFHHSX1f7koODfDt1zrw8Johcj5WyO2U7ekRD_VLnFp2Oo2GyrBL55WLqmvW1Zeq-c";
        }
        
        return imageUrl;
    }
    
    /**
     * Display error message
     * @param {string} message - Error message
     * @param {Function} retryCallback - Optional callback for retry button
     */
    showError(message, retryCallback = null) {
        this.hideWeather();
        this.hideLoading();
        
        this.errorMessage.textContent = message;
        
        if (retryCallback) {
            this.retryBtn.onclick = retryCallback;
            this.retryBtn.classList.remove('hidden');
        } else {
            this.retryBtn.classList.add('hidden');
        }
        
        this.errorContainer.classList.remove('hidden');
    }
    
    /**
     * Hide error message
     */
    hideError() {
        this.errorContainer.classList.add('hidden');
    }
}

// ============================================================================
// Application Initialization
// ============================================================================

// ============================================================================
// TabManager Class
// ============================================================================

class TabManager {
    constructor() {
        this.activeTab = 'today';
        this.tabs = ['today', 'forecast', 'maps', 'news'];
        this.currentLocation = null;
        this.setupTabListeners();
        this.setupMapControls();
        this.setupNewsControls();
    }
    
    /**
     * Set up event listeners for tab buttons
     */
    setupTabListeners() {
        this.tabs.forEach(tabName => {
            const tabButton = document.getElementById(`tab-${tabName}`);
            if (tabButton) {
                tabButton.addEventListener('click', () => {
                    this.switchTab(tabName);
                });
            }
        });
    }
    
    /**
     * Set up map layer controls
     */
    setupMapControls() {
        const mapButtons = ['map-temp', 'map-precipitation', 'map-wind', 'map-satellite'];
        mapButtons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.addEventListener('click', () => {
                    this.switchMapLayer(buttonId);
                });
            }
        });
    }
    
    /**
     * Set up news category controls
     */
    setupNewsControls() {
        const newsButtons = ['news-alerts', 'news-local', 'news-climate', 'news-safety'];
        newsButtons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.addEventListener('click', () => {
                    this.switchNewsCategory(buttonId);
                });
            }
        });
    }
    
    /**
     * Switch to a specific tab
     * @param {string} tabName - Name of the tab to switch to
     */
    switchTab(tabName) {
        if (!this.tabs.includes(tabName)) return;
        
        // Update active tab
        this.activeTab = tabName;
        
        // Update tab button styles
        this.tabs.forEach(tab => {
            const button = document.getElementById(`tab-${tab}`);
            if (button) {
                if (tab === tabName) {
                    button.className = 'nav-tab active text-[#111418] text-sm font-medium leading-normal border-b-2 border-blue-500 pb-1';
                } else {
                    button.className = 'nav-tab text-[#637588] text-sm font-medium leading-normal hover:text-[#111418] pb-1';
                }
            }
        });
        
        // Show/hide content sections
        this.showTabContent(tabName);
    }
    
    /**
     * Show content for the active tab
     * @param {string} tabName - Name of the tab to show
     */
    showTabContent(tabName) {
        // Hide all content sections
        const weatherDisplay = document.getElementById('weather-display');
        const forecastContent = document.getElementById('forecast-content');
        const mapsContent = document.getElementById('maps-content');
        const newsContent = document.getElementById('news-content');
        const errorDisplay = document.getElementById('error-display');
        const loadingDisplay = document.getElementById('loading-display');
        
        // Hide all sections first
        [weatherDisplay, forecastContent, mapsContent, newsContent, errorDisplay, loadingDisplay].forEach(element => {
            if (element) element.classList.add('hidden');
        });
        
        // Show the appropriate content
        switch (tabName) {
            case 'today':
                if (weatherDisplay) weatherDisplay.classList.remove('hidden');
                break;
            case 'forecast':
                if (forecastContent) forecastContent.classList.remove('hidden');
                this.loadForecastData();
                break;
            case 'maps':
                if (mapsContent) mapsContent.classList.remove('hidden');
                this.loadMapsData();
                break;
            case 'news':
                if (newsContent) newsContent.classList.remove('hidden');
                this.loadNewsData();
                break;
        }
    }
    
    /**
     * Update current location for all tabs
     * @param {Object} locationData - Location data from weather API
     */
    updateLocation(locationData) {
        this.currentLocation = locationData;
        
        // Update location displays for all tabs
        const mapsLocationDisplay = document.getElementById('maps-location-display');
        const newsLocationDisplay = document.getElementById('news-location-display');
        const forecastLocationDisplay = document.getElementById('forecast-location-display');
        
        if (mapsLocationDisplay && locationData) {
            mapsLocationDisplay.innerHTML = `<p>Weather maps for <strong>${locationData.location.name}</strong></p>`;
        }
        
        if (newsLocationDisplay && locationData) {
            newsLocationDisplay.innerHTML = `<p>Weather news and alerts for <strong>${locationData.location.name}</strong></p>`;
        }
        
        if (forecastLocationDisplay && locationData) {
            forecastLocationDisplay.innerHTML = `<p>7-day forecast for <strong>${locationData.location.name}</strong></p>`;
        }
        
        // Reload current tab content if it's maps, news, or forecast
        if (this.activeTab === 'maps') {
            this.loadMapsData();
        } else if (this.activeTab === 'news') {
            this.loadNewsData();
        } else if (this.activeTab === 'forecast') {
            this.loadForecastData();
        }
    }
    
    /**
     * Load forecast data based on current location
     */
    loadForecastData() {
        if (!this.currentLocation) {
            return;
        }
        
        const forecastCards = document.getElementById('forecast-cards');
        const forecastPlaceholder = document.getElementById('forecast-placeholder');
        
        if (!forecastCards) return;
        
        // Hide placeholder
        if (forecastPlaceholder) {
            forecastPlaceholder.classList.add('hidden');
        }
        
        // Generate 7-day forecast data
        const forecastData = this.generateForecastData();
        
        // Create forecast cards HTML
        const forecastHtml = forecastData.map(day => `
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div class="text-center">
                    <h3 class="text-lg font-medium text-gray-900 mb-2">${day.dayName}</h3>
                    <p class="text-sm text-gray-500 mb-3">${day.date}</p>
                    
                    <!-- Weather Icon -->
                    <div class="mb-3">
                        <div class="w-16 h-16 mx-auto bg-gradient-to-br ${day.iconGradient} rounded-full flex items-center justify-center">
                            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                ${day.iconPath}
                            </svg>
                        </div>
                    </div>
                    
                    <!-- Temperature -->
                    <div class="mb-3">
                        <div class="text-2xl font-bold text-gray-900">${day.highTemp}°</div>
                        <div class="text-sm text-gray-500">${day.lowTemp}°</div>
                    </div>
                    
                    <!-- Conditions -->
                    <p class="text-sm font-medium text-gray-700 mb-2">${day.conditions}</p>
                    
                    <!-- Details -->
                    <div class="text-xs text-gray-500 space-y-1">
                        <div class="flex justify-between">
                            <span>Rain:</span>
                            <span>${day.rainChance}%</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Wind:</span>
                            <span>${day.windSpeed}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Humidity:</span>
                            <span>${day.humidity}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        forecastCards.innerHTML = forecastHtml;
    }
    
    /**
     * Generate 7-day forecast data based on current weather
     * @returns {Array} Array of forecast day objects
     */
    generateForecastData() {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const today = new Date();
        const forecast = [];
        
        // Base temperature from current weather if available
        let baseTemp = 70; // Default
        if (this.currentLocation && this.currentLocation.weather) {
            baseTemp = parseInt(this.currentLocation.weather.temp_f) || 70;
        }
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(today);
            date.setDate(today.getDate() + i);
            
            // Generate realistic weather variations
            const tempVariation = (Math.random() - 0.5) * 20; // ±10 degrees
            const highTemp = Math.round(baseTemp + tempVariation + Math.random() * 5);
            const lowTemp = Math.round(highTemp - 10 - Math.random() * 10);
            
            // Weather conditions with seasonal bias
            const conditions = this.getRandomWeatherCondition();
            const rainChance = Math.round(Math.random() * 100);
            const windSpeed = Math.round(5 + Math.random() * 15) + ' mph';
            const humidity = Math.round(30 + Math.random() * 50);
            
            forecast.push({
                dayName: i === 0 ? 'Today' : days[date.getDay()],
                date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                highTemp,
                lowTemp,
                conditions: conditions.name,
                iconGradient: conditions.gradient,
                iconPath: conditions.iconPath,
                rainChance,
                windSpeed,
                humidity
            });
        }
        
        return forecast;
    }
    
    /**
     * Get random weather condition with appropriate styling
     * @returns {Object} Weather condition object
     */
    getRandomWeatherCondition() {
        const conditions = [
            {
                name: 'Sunny',
                gradient: 'from-yellow-400 to-orange-500',
                iconPath: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>'
            },
            {
                name: 'Partly Cloudy',
                gradient: 'from-blue-400 to-blue-600',
                iconPath: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"></path>'
            },
            {
                name: 'Cloudy',
                gradient: 'from-gray-400 to-gray-600',
                iconPath: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"></path>'
            },
            {
                name: 'Rainy',
                gradient: 'from-blue-500 to-blue-700',
                iconPath: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>'
            },
            {
                name: 'Thunderstorms',
                gradient: 'from-purple-500 to-purple-700',
                iconPath: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>'
            },
            {
                name: 'Snow',
                gradient: 'from-blue-200 to-blue-400',
                iconPath: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"></path>'
            }
        ];
        
        return conditions[Math.floor(Math.random() * conditions.length)];
    }
    
    /**
     * Load maps data based on current location
     */
    loadMapsData() {
        if (!this.currentLocation) {
            return;
        }
        
        const { lat, lon } = this.currentLocation.location.coordinates;
        this.loadWeatherMap(lat, lon, 'temperature');
    }
    
    /**
     * Load weather map for specific coordinates and layer
     * @param {number} lat - Latitude
     * @param {number} lon - Longitude  
     * @param {string} layer - Map layer type
     */
    loadWeatherMap(lat, lon, layer) {
        const mapIframe = document.getElementById('map-iframe');
        const mapPlaceholder = document.getElementById('map-placeholder');
        
        if (!mapIframe || !mapPlaceholder) return;
        
        // Use OpenWeatherMap or similar service for weather maps
        // For demo purposes, we'll use OpenStreetMap with weather overlay
        const zoom = 8;
        let mapUrl;
        
        switch (layer) {
            case 'temperature':
                // Temperature layer - using OpenWeatherMap API
                mapUrl = `https://tile.openweathermap.org/map/temp_new/${zoom}/${Math.floor((lon + 180) / 360 * Math.pow(2, zoom))}/${Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom))}.png?appid=demo`;
                break;
            case 'precipitation':
                mapUrl = `https://tile.openweathermap.org/map/precipitation_new/${zoom}/${Math.floor((lon + 180) / 360 * Math.pow(2, zoom))}/${Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom))}.png?appid=demo`;
                break;
            case 'wind':
                mapUrl = `https://tile.openweathermap.org/map/wind_new/${zoom}/${Math.floor((lon + 180) / 360 * Math.pow(2, zoom))}/${Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom))}.png?appid=demo`;
                break;
            default:
                // Use embedded Google Maps or OpenStreetMap
                mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${lon-0.5},${lat-0.5},${lon+0.5},${lat+0.5}&layer=mapnik&marker=${lat},${lon}`;
        }
        
        // For demo, we'll create a simple map visualization
        mapPlaceholder.classList.add('hidden');
        mapIframe.src = mapUrl;
        mapIframe.classList.remove('hidden');
    }
    
    /**
     * Switch map layer
     * @param {string} layerId - ID of the layer button
     */
    switchMapLayer(layerId) {
        // Update button styles
        const mapButtons = document.querySelectorAll('.map-layer-btn');
        mapButtons.forEach(btn => {
            btn.className = 'map-layer-btn px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300 transition-colors';
        });
        
        const activeButton = document.getElementById(layerId);
        if (activeButton) {
            activeButton.className = 'map-layer-btn active px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors';
        }
        
        // Update legend
        this.updateMapLegend(layerId);
        
        // Reload map with new layer
        if (this.currentLocation) {
            const { lat, lon } = this.currentLocation.location.coordinates;
            const layer = layerId.replace('map-', '');
            this.loadWeatherMap(lat, lon, layer);
        }
    }
    
    /**
     * Update map legend based on active layer
     * @param {string} layerId - ID of the active layer
     */
    updateMapLegend(layerId) {
        const legendContent = document.getElementById('legend-content');
        if (!legendContent) return;
        
        let legendHtml = '';
        
        switch (layerId) {
            case 'map-temp':
                legendHtml = `
                    <div class="temperature-legend">
                        <div class="flex items-center space-x-4">
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-blue-500 rounded"></div>
                                <span>Cold (&lt;32°F)</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-green-500 rounded"></div>
                                <span>Mild (32-60°F)</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-yellow-500 rounded"></div>
                                <span>Warm (60-80°F)</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-red-500 rounded"></div>
                                <span>Hot (&gt;80°F)</span>
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'map-precipitation':
                legendHtml = `
                    <div class="precipitation-legend">
                        <div class="flex items-center space-x-4">
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-blue-200 rounded"></div>
                                <span>Light</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-blue-400 rounded"></div>
                                <span>Moderate</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-blue-600 rounded"></div>
                                <span>Heavy</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-blue-800 rounded"></div>
                                <span>Severe</span>
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'map-wind':
                legendHtml = `
                    <div class="wind-legend">
                        <div class="flex items-center space-x-4">
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-green-300 rounded"></div>
                                <span>Light (&lt;10 mph)</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-yellow-400 rounded"></div>
                                <span>Moderate (10-25 mph)</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-orange-500 rounded"></div>
                                <span>Strong (25-40 mph)</span>
                            </div>
                            <div class="flex items-center space-x-1">
                                <div class="w-4 h-4 bg-red-600 rounded"></div>
                                <span>Severe (&gt;40 mph)</span>
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'map-satellite':
                legendHtml = `
                    <div class="satellite-legend">
                        <p class="text-sm text-gray-600">Satellite imagery showing cloud cover and weather patterns</p>
                    </div>
                `;
                break;
        }
        
        legendContent.innerHTML = legendHtml;
    }
    
    /**
     * Load news data based on current location
     */
    loadNewsData() {
        if (!this.currentLocation) {
            return;
        }
        
        this.loadWeatherNews('alerts');
    }
    
    /**
     * Load weather news for specific category
     * @param {string} category - News category
     */
    loadWeatherNews(category) {
        const newsArticles = document.getElementById('news-articles');
        const newsPlaceholder = document.getElementById('news-placeholder');
        const newsLoading = document.getElementById('news-loading');
        
        if (!newsArticles) return;
        
        // Show loading
        if (newsPlaceholder) newsPlaceholder.classList.add('hidden');
        if (newsLoading) newsLoading.classList.remove('hidden');
        
        // Simulate loading delay
        setTimeout(() => {
            if (newsLoading) newsLoading.classList.add('hidden');
            
            // Generate location-based news content
            const locationName = this.currentLocation ? this.currentLocation.location.name : 'your area';
            const newsContent = this.generateNewsContent(category, locationName);
            
            newsArticles.innerHTML = newsContent;
        }, 1000);
    }
    
    /**
     * Generate news content based on category and location
     * @param {string} category - News category
     * @param {string} locationName - Location name
     * @returns {string} HTML content
     */
    generateNewsContent(category, locationName) {
        const currentDate = new Date().toLocaleDateString();
        
        switch (category) {
            case 'alerts':
                return `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-6 shadow-sm">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0">
                                <div class="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                                    <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-medium text-red-900">Weather Alert for ${locationName}</h3>
                                <p class="text-red-700 mt-1">Stay informed about current weather conditions in your area.</p>
                                <p class="text-sm text-red-600 mt-2">${currentDate}</p>
                                <div class="mt-3 text-sm text-red-700">
                                    <p>• Monitor local weather conditions</p>
                                    <p>• Check for any active weather advisories</p>
                                    <p>• Stay prepared for changing conditions</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 shadow-sm">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0">
                                <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                                    <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-medium text-yellow-900">Weather Advisory</h3>
                                <p class="text-yellow-700 mt-1">General weather advisory for ${locationName} area.</p>
                                <p class="text-sm text-yellow-600 mt-2">${currentDate}</p>
                            </div>
                        </div>
                    </div>
                `;
                
            case 'local':
                return `
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 shadow-sm">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0">
                                <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-medium text-blue-900">Local Weather Update for ${locationName}</h3>
                                <p class="text-blue-700 mt-1">Current weather conditions and local forecast information.</p>
                                <p class="text-sm text-blue-600 mt-2">${currentDate}</p>
                                <div class="mt-3 text-sm text-blue-700">
                                    <p>• Current conditions are being monitored</p>
                                    <p>• Local weather patterns show typical seasonal behavior</p>
                                    <p>• No significant weather events expected</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-green-50 border border-green-200 rounded-lg p-6 shadow-sm">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0">
                                <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                    <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-medium text-green-900">Weather Outlook</h3>
                                <p class="text-green-700 mt-1">Extended forecast and seasonal outlook for ${locationName}.</p>
                                <p class="text-sm text-green-600 mt-2">${currentDate}</p>
                            </div>
                        </div>
                    </div>
                `;
                
            case 'climate':
                return `
                    <div class="bg-purple-50 border border-purple-200 rounded-lg p-6 shadow-sm">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0">
                                <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                                    <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-medium text-purple-900">Climate Update for ${locationName}</h3>
                                <p class="text-purple-700 mt-1">Long-term climate trends and seasonal patterns in your area.</p>
                                <p class="text-sm text-purple-600 mt-2">${currentDate}</p>
                                <div class="mt-3 text-sm text-purple-700">
                                    <p>• Seasonal temperature trends are within normal ranges</p>
                                    <p>• Precipitation patterns following historical averages</p>
                                    <p>• Climate monitoring continues for long-term analysis</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
            case 'safety':
                return `
                    <div class="bg-orange-50 border border-orange-200 rounded-lg p-6 shadow-sm">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0">
                                <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                                    <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-medium text-orange-900">Weather Safety Tips for ${locationName}</h3>
                                <p class="text-orange-700 mt-1">Important safety information for current weather conditions.</p>
                                <p class="text-sm text-orange-600 mt-2">${currentDate}</p>
                                <div class="mt-3 text-sm text-orange-700">
                                    <p><strong>General Safety Tips:</strong></p>
                                    <p>• Stay informed about weather conditions</p>
                                    <p>• Keep emergency supplies readily available</p>
                                    <p>• Monitor weather alerts and warnings</p>
                                    <p>• Plan outdoor activities according to weather</p>
                                    <p>• Have a communication plan for severe weather</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-gray-50 border border-gray-200 rounded-lg p-6 shadow-sm">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0">
                                <div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                                    <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="flex-1">
                                <h3 class="text-lg font-medium text-gray-900">Emergency Preparedness</h3>
                                <p class="text-gray-700 mt-1">Be prepared for weather emergencies in ${locationName}.</p>
                                <p class="text-sm text-gray-600 mt-2">${currentDate}</p>
                            </div>
                        </div>
                    </div>
                `;
                
            default:
                return '<div class="text-center p-8 text-gray-500">No news available for this category.</div>';
        }
    }
    
    /**
     * Switch news category
     * @param {string} categoryId - ID of the category button
     */
    switchNewsCategory(categoryId) {
        // Update button styles
        const newsButtons = document.querySelectorAll('.news-category-btn');
        newsButtons.forEach(btn => {
            btn.className = 'news-category-btn px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300 transition-colors';
        });
        
        const activeButton = document.getElementById(categoryId);
        if (activeButton) {
            let bgColor = 'bg-blue-500 hover:bg-blue-600';
            if (categoryId === 'news-alerts') bgColor = 'bg-red-500 hover:bg-red-600';
            else if (categoryId === 'news-local') bgColor = 'bg-blue-500 hover:bg-blue-600';
            else if (categoryId === 'news-climate') bgColor = 'bg-green-500 hover:bg-green-600';
            else if (categoryId === 'news-safety') bgColor = 'bg-orange-500 hover:bg-orange-600';
            
            activeButton.className = `news-category-btn active px-4 py-2 ${bgColor} text-white rounded-lg text-sm transition-colors`;
        }
        
        // Load news for selected category
        const category = categoryId.replace('news-', '');
        this.loadWeatherNews(category);
    }
    
    /**
     * Get the currently active tab
     * @returns {string} Active tab name
     */
    getActiveTab() {
        return this.activeTab;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('Weather Web Service initialized');
    
    // Initialize components
    const searchInterface = new SearchInterface('search-input', 'autocomplete-suggestions');
    const geolocationHandler = new GeolocationHandler();
    const weatherDisplay = new WeatherDisplay();
    const tabManager = new TabManager();
    
    // Also handle header search input
    const headerSearchInput = document.getElementById('header-search-input');
    if (headerSearchInput) {
        // Create a simple search handler for header input
        headerSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && headerSearchInput.value.trim()) {
                e.preventDefault();
                // Copy search to main input and trigger search
                const mainInput = document.getElementById('search-input');
                if (mainInput) {
                    mainInput.value = headerSearchInput.value.trim();
                    handleSearch(headerSearchInput.value.trim());
                }
            }
        });
    }
    
    // Handle search function
    async function handleSearch(location) {
        // Switch to Today tab when searching
        tabManager.switchTab('today');
        
        weatherDisplay.showLoading();
        
        try {
            const data = await fetchWeather(location);
            weatherDisplay.showWeather(data);
            
            // Update location for all tabs
            tabManager.updateLocation(data);
        } catch (error) {
            weatherDisplay.showError(error.message, () => {
                handleSearch(location);
            });
        }
    }
    
    // Handle search submissions from main search
    searchInterface.onSearch(handleSearch);
    
    // Handle current location button
    const currentLocationBtn = document.getElementById('current-location-btn');
    if (currentLocationBtn) {
        currentLocationBtn.addEventListener('click', () => {
            // Switch to Today tab when using current location
            tabManager.switchTab('today');
            
            weatherDisplay.showLoading();
            
            geolocationHandler.onSuccess(async (lat, lon) => {
                try {
                    const data = await fetchWeatherByCoordinates(lat, lon);
                    weatherDisplay.showWeather(data);
                    
                    // Update location for all tabs
                    tabManager.updateLocation(data);
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
    
    // Handle settings button (placeholder)
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            alert('Settings functionality coming soon!');
        });
    }
    
    // Focus search input on page load
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.focus();
    }
    
    // Initialize with Today tab active
    tabManager.switchTab('today');
});
