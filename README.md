# Silicon Valley Events Collector

A comprehensive data collection and processing system for tech events in Silicon Valley. This system automatically gathers event information from multiple sources including Meetup, Eventbrite, LinkedIn, and Stanford Events.

## Features

- Multi-source event collection (APIs and web scraping)
- Automated data processing and storage
- Calendar view functionality
- Rate limiting and error handling
- Comprehensive logging

## Installation

1. Clone the repository
2. python -m venv venv
venv\Scripts\activate
3.  Install required packages:
pip install -r requirements.txt
pip install -e .
python -m main


3. Set up configuration:
   - Copy `config/settings.py.example` to `config/settings.py`
   - Add your API keys and credentials

## Configuration

The following environment variables need to be set in `config/settings.py`:

- `MEETUP_API_KEY`: Your Meetup API key
- `EVENTBRITE_API_KEY`: Your Eventbrite API key
- `LINKEDIN_EMAIL`: LinkedIn account email
- `LINKEDIN_PASSWORD`: LinkedIn account password
- `DATABASE_URL`: Database connection URL (default: sqlite:///events.db)

## Usage

### Running the Collector

```bash
python main.py
```

This will:
1. Validate all data sources
2. Collect events from all configured sources
3. Store events in the database
4. Generate logs of the collection process

### Using the Calendar View

```python
from silicon_valley_events.models.database import EventStorage
from datetime import datetime, timedelta

# Initialize storage
storage = EventStorage()

# Get events for next 30 days
start_date = datetime.now()
end_date = start_date + timedelta(days=30)
events = storage.get_events(start_date, end_date)
```

## Project Structure

```
silicon_valley_events/
├── api_clients/         # API client implementations
├── scrapers/           # Web scraper implementations
├── models/             # Data models and database
├── utils/              # Utility functions
├── config/             # Configuration files
└── main.py            # Main orchestration script
```

## Error Handling

The system includes comprehensive error handling:
- Rate limiting for API requests
- Automatic retries for failed requests
- Detailed error logging
- Source validation before collection

## Development

### Adding New Sources

1. Create a new source class implementing `EventSource`
2. Add the source to `EventCollector` in main.py
3. Update configuration as needed

### Database Migrations

Use Alembic for database migrations:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## License

MIT License

## Contributors

- Initial implementation by David

## Support

For support, please raise an issue in the repository.