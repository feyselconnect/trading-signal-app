from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client
import requests
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
from ict_analysis import ICTAnalysis
from entry_systems import EntrySystems

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
BASE_URL = 'https://www.alphavantage.co/query'

# Timeframes to fetch
TIMEFRAMES = {
    '1m': '1min',
    '5m': '5min',
    '15m': '15min',
    '1h': '60min',
    '4h': '240min',
    '1d': 'daily'
}

# Assets to fetch
ASSETS = {
    'XAUUSD': 'FOREX',
    'NASDAQ': 'INDEX'
}

def fetch_market_data(asset, timeframe, retries=3, delay=5):
    """Fetch market data from Alpha Vantage with retry logic"""
    for attempt in range(retries):
        try:
            if asset == 'XAUUSD':
                function = 'FX_INTRADAY'
                from_symbol = 'XAU'
                to_symbol = 'USD'
            else:  # NASDAQ
                function = 'TIME_SERIES_INTRADAY'
                symbol = '^NDX'

            params = {
                'function': function,
                'apikey': ALPHA_VANTAGE_API_KEY,
                'interval': TIMEFRAMES[timeframe],
                'outputsize': 'compact'
            }

            if asset == 'XAUUSD':
                params.update({
                    'from_symbol': from_symbol,
                    'to_symbol': to_symbol
                })
            else:
                params['symbol'] = symbol

            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Process and store data
            if asset == 'XAUUSD':
                time_series = data.get(f'Time Series FX ({TIMEFRAMES[timeframe]})', {})
            else:
                time_series = data.get(f'Time Series ({TIMEFRAMES[timeframe]})', {})

            for timestamp, values in time_series.items():
                market_data = {
                    'timestamp': timestamp,
                    'asset': asset,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(float(values['5. volume']))
                }
                
                # Store in Supabase
                supabase.table('market_data').upsert(market_data).execute()

            return True

        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            print(f"Error fetching data for {asset} {timeframe}: {str(e)}")
            return False

@app.route('/market-data', methods=['GET'])
def get_market_data():
    """Endpoint to fetch and store market data"""
    results = {}
    
    for asset in ASSETS:
        results[asset] = {}
        for timeframe in TIMEFRAMES:
            success = fetch_market_data(asset, timeframe)
            results[asset][timeframe] = 'success' if success else 'failed'
            # Respect rate limit (5 calls per minute)
            time.sleep(12)  # 12 seconds between calls to stay under limit
    
    return jsonify(results)

@app.route('/signals', methods=['GET'])
def get_signals():
    """Endpoint to generate ICT analysis signals"""
    results = {}
    
    for asset in ASSETS:
        results[asset] = {}
        for timeframe in TIMEFRAMES:
            try:
                # Fetch data from Supabase
                response = supabase.table('market_data')\
                    .select('*')\
                    .eq('asset', asset)\
                    .order('timestamp', desc=True)\
                    .limit(1000)\
                    .execute()
                
                if not response.data:
                    results[asset][timeframe] = {'error': 'No data available'}
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(response.data)
                
                # Generate signals
                analysis = ICTAnalysis(df)
                signals = analysis.generate_signals()
                
                # Store signals in Supabase
                signal_data = {
                    'asset': asset,
                    'timeframe': timeframe,
                    'bias': signals['bias'],
                    'liquidity_zones': signals['liquidity_zones'],
                    'events': signals['events'],
                    'timestamp': datetime.now().isoformat()
                }
                
                supabase.table('trade_signals').upsert(signal_data).execute()
                
                results[asset][timeframe] = signals
                
            except Exception as e:
                results[asset][timeframe] = {'error': str(e)}
    
    return jsonify(results)

@app.route('/entries', methods=['GET'])
def get_entries():
    """Endpoint to generate entry signals"""
    results = {}
    
    for asset in ASSETS:
        results[asset] = {}
        for timeframe in TIMEFRAMES:
            try:
                # Fetch data from Supabase
                response = supabase.table('market_data')\
                    .select('*')\
                    .eq('asset', asset)\
                    .order('timestamp', desc=True)\
                    .limit(1000)\
                    .execute()
                
                if not response.data:
                    results[asset][timeframe] = {'error': 'No data available'}
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(response.data)
                
                # Generate ICT analysis
                ict_analysis = ICTAnalysis(df)
                
                # Generate entry signals
                entry_systems = EntrySystems(df, ict_analysis)
                entries = entry_systems.generate_entries()
                
                if entries:
                    # Store entries in Supabase
                    for system, entry in entries.items():
                        entry_data = {
                            'asset': asset,
                            'timeframe': timeframe,
                            'system': system,
                            'direction': entry['direction'],
                            'entry_price': entry['entry_price'],
                            'stop_loss': entry['stop_loss'],
                            'take_profit': entry['take_profit'],
                            'invalidation_point': entry['invalidation_point'],
                            'timestamp': entry['timestamp'].isoformat()
                        }
                        
                        supabase.table('trade_signals').upsert(entry_data).execute()
                
                results[asset][timeframe] = entries
                
            except Exception as e:
                results[asset][timeframe] = {'error': str(e)}
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 