# Market Data Backend

This Flask backend service fetches market data from Alpha Vantage and stores it in Supabase.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the backend directory with the following variables:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

3. Run the application:
```bash
python app.py
```

## Features

- Fetches OHLC data for XAUUSD and NASDAQ
- Supports multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Implements retry logic (3 attempts, 5s delay)
- Handles Alpha Vantage rate limits (5 calls/min)
- Stores data in Supabase market_data table
- Exposes /market-data endpoint for frontend consumption

## API Endpoints

### GET /market-data
Fetches and stores market data for all configured assets and timeframes.

Response format:
```json
{
    "XAUUSD": {
        "1m": "success",
        "5m": "success",
        ...
    },
    "NASDAQ": {
        "1m": "success",
        "5m": "success",
        ...
    }
}
``` 