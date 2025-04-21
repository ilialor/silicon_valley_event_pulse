
MEETUP_API_KEY = "YOUR_MEETUP_API_KEY"
EVENTBRITE_API_KEY = "YOUR_EVENTBRITE_API_KEY"

# Database configuration
DATABASE_URL = "sqlite:///events.db"

# Scraping configuration
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

# Rate limiting (requests per minute)
RATE_LIMITS = {
    "meetup": 30,
    "eventbrite": 30,
    "default": 10
}
