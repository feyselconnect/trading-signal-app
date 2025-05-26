# Trading Signal Dashboard

A React.js dashboard for displaying real-time trading signals, market data, and portfolio metrics.

## Features

- Real-time XAUUSD and NASDAQ price charts
- Trade signals with detailed information
- Portfolio metrics and risk management
- User-configurable account balance and risk parameters
- Multiple timeframe support (1m, 5m, 15m, 1h, 4h, 1d)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file in the frontend directory with your Supabase credentials:
```
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
```

3. Start the development server:
```bash
npm start
```

## Technologies Used

- React.js 18
- TypeScript
- Tailwind CSS
- Chart.js
- Supabase
- Headless UI
- Heroicons

## Project Structure

- `src/App.tsx`: Main application component
- `src/index.tsx`: Application entry point
- `src/index.css`: Global styles and Tailwind imports

## API Integration

The dashboard connects to Supabase tables:
- `market_data`: OHLC price data
- `trade_signals`: Trading signals and analysis
- `portfolio_metrics`: Risk and performance metrics

## Development

To run the development server:
```bash
npm start
```

To build for production:
```bash
npm run build
``` 