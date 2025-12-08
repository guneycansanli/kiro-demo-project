# Requirements Document

## Introduction

This document specifies the requirements for a cross-platform command-line weather script that retrieves and displays current weather information for a given zip code. The script will scrape weather data from a public website, support command-line arguments for zip code input, cache the last used zip code, and display formatted weather information including temperature, chance of rain, humidity, wind speed, and current conditions.

## Glossary

- **Weather Script**: The command-line application that retrieves and displays weather information
- **Zip Code**: A 5-digit US postal code used to identify a geographic location
- **Default Zip Code**: The zip code value of 07610 used when no command-line argument is provided
- **Cached Zip Code**: The most recently used zip code stored locally for future use
- **Weather Data**: Information including temperature, chance of rain, humidity, wind speed, and conditions
- **Weather Advisory**: An official alert issued for hazardous weather conditions such as heat, cold, wind, or other severe weather
- **Public Weather Website**: A publicly accessible weather information website that can be scraped without authentication

## Requirements

### Requirement 1

**User Story:** As a user, I want to run the script without arguments and see weather for my default location, so that I can quickly check my local weather.

#### Acceptance Criteria

1. WHEN the user executes the Weather Script without command-line arguments, THE Weather Script SHALL use the Default Zip Code 07610
2. WHEN the Weather Script uses the Default Zip Code, THE Weather Script SHALL retrieve and display weather information for that location
3. WHEN the Weather Script completes successfully, THE Weather Script SHALL display the weather data in a formatted output

### Requirement 2

**User Story:** As a traveler, I want to specify a different zip code via command-line argument, so that I can check weather for locations I'm visiting.

#### Acceptance Criteria

1. WHEN the user provides a zip code as a command-line argument, THE Weather Script SHALL use the provided zip code instead of the Default Zip Code
2. WHEN the user provides a zip code argument, THE Weather Script SHALL validate that the zip code is exactly 5 digits
3. IF the provided zip code is not exactly 5 digits, THEN THE Weather Script SHALL display an error message and exit with a non-zero status code
4. WHEN a valid zip code is provided, THE Weather Script SHALL cache the zip code for future use

### Requirement 3

**User Story:** As a frequent user, I want the script to remember my last used zip code, so that I don't have to re-enter it every time.

#### Acceptance Criteria

1. WHEN the Weather Script successfully retrieves weather data for a zip code, THE Weather Script SHALL store the zip code as the Cached Zip Code
2. WHEN the user executes the Weather Script without arguments and a Cached Zip Code exists, THE Weather Script SHALL use the Cached Zip Code instead of the Default Zip Code
3. WHEN the Weather Script stores the Cached Zip Code, THE Weather Script SHALL persist the value to a local file in the user's home directory
4. WHEN the Weather Script reads the Cached Zip Code, THE Weather Script SHALL validate that the cached value is exactly 5 digits before using it

### Requirement 4

**User Story:** As a user, I want to see comprehensive weather information, so that I can make informed decisions about my day.

#### Acceptance Criteria

1. WHEN the Weather Script retrieves weather data, THE Weather Script SHALL extract the current temperature in both Fahrenheit and Celsius
2. WHEN the Weather Script retrieves weather data, THE Weather Script SHALL extract today's chance of rain as a percentage
3. WHEN the Weather Script retrieves weather data, THE Weather Script SHALL extract the current humidity level
4. WHEN the Weather Script retrieves weather data, THE Weather Script SHALL extract the current wind speed
5. WHEN the Weather Script retrieves weather data, THE Weather Script SHALL extract the current weather conditions description

### Requirement 5

**User Story:** As a user, I want the weather information displayed in a clear and readable format, so that I can quickly understand the current conditions.

#### Acceptance Criteria

1. WHEN the Weather Script displays weather data, THE Weather Script SHALL format the output with labeled fields for each weather metric
2. WHEN the Weather Script displays temperature, THE Weather Script SHALL show both Fahrenheit and Celsius values
3. WHEN the Weather Script displays the output, THE Weather Script SHALL include the zip code being queried
4. WHEN the Weather Script displays the output, THE Weather Script SHALL use clear visual separation between different weather metrics

### Requirement 6

**User Story:** As a user, I want the script to handle errors gracefully, so that I understand what went wrong when issues occur.

#### Acceptance Criteria

1. IF the Weather Script cannot connect to the Public Weather Website, THEN THE Weather Script SHALL display a network error message and exit with a non-zero status code
2. IF the Weather Script cannot parse weather data from the website, THEN THE Weather Script SHALL display a parsing error message and exit with a non-zero status code
3. IF the provided zip code returns no weather data, THEN THE Weather Script SHALL display an invalid location error message and exit with a non-zero status code
4. WHEN the Weather Script encounters an error, THE Weather Script SHALL provide a clear description of the problem to the user

### Requirement 7

**User Story:** As a cross-platform user, I want the script to work on macOS, Windows, and Linux, so that I can use it regardless of my operating system.

#### Acceptance Criteria

1. THE Weather Script SHALL execute successfully on macOS without modification
2. THE Weather Script SHALL execute successfully on Windows without modification
3. THE Weather Script SHALL execute successfully on Linux without modification
4. WHEN the Weather Script stores the Cached Zip Code, THE Weather Script SHALL use platform-appropriate file paths for the cache file
5. THE Weather Script SHALL use only cross-platform compatible libraries and language features

### Requirement 8

**User Story:** As a user, I want to see active weather advisories for my area, so that I can be aware of potentially hazardous conditions.

#### Acceptance Criteria

1. WHEN the Weather Script retrieves weather data, THE Weather Script SHALL check for active Weather Advisories in the queried location
2. IF a Weather Advisory is active, THEN THE Weather Script SHALL display the advisory prominently in the output
3. WHEN displaying a Weather Advisory, THE Weather Script SHALL show the advisory type and full description including severity and timing
4. IF multiple Weather Advisories are active, THEN THE Weather Script SHALL display only the most severe advisory
5. WHEN no Weather Advisory is active, THE Weather Script SHALL display a message indicating no active advisories

### Requirement 9

**User Story:** As a user, I want the script to scrape weather data from a public website, so that I don't need to manage API keys or accounts.

#### Acceptance Criteria

1. WHEN the Weather Script retrieves weather data, THE Weather Script SHALL make HTTP requests to a Public Weather Website
2. WHEN the Weather Script processes the response, THE Weather Script SHALL parse HTML content to extract weather information
3. THE Weather Script SHALL not require API keys, authentication tokens, or user accounts
4. WHEN the Weather Script makes HTTP requests, THE Weather Script SHALL include appropriate user-agent headers to identify itself
