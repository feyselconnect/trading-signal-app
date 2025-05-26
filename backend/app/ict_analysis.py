import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class ICTAnalysis:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data.set_index('timestamp', inplace=True)
        self.data.sort_index(inplace=True)
        
    def calculate_sma_slope(self, period: int = 20) -> float:
        """Calculate the slope of the 20-period SMA"""
        sma = self.data['close'].rolling(window=period).mean()
        if len(sma) < 2:
            return 0
        return (sma.iloc[-1] - sma.iloc[-2]) / sma.iloc[-2]

    def get_quarterly_levels(self) -> Dict[str, float]:
        """Calculate quarterly levels based on the current year's data"""
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31)
        
        yearly_data = self.data[year_start:year_end]
        
        if len(yearly_data) == 0:
            return {
                'q1_high': 0, 'q1_low': 0,
                'q2_high': 0, 'q2_low': 0,
                'q3_high': 0, 'q3_low': 0,
                'q4_high': 0, 'q4_low': 0
            }
        
        quarters = {
            'q1': (datetime(current_year, 1, 1), datetime(current_year, 3, 31)),
            'q2': (datetime(current_year, 4, 1), datetime(current_year, 6, 30)),
            'q3': (datetime(current_year, 7, 1), datetime(current_year, 9, 30)),
            'q4': (datetime(current_year, 10, 1), datetime(current_year, 12, 31))
        }
        
        levels = {}
        for q, (start, end) in quarters.items():
            quarter_data = yearly_data[start:end]
            if len(quarter_data) > 0:
                levels[f'{q}_high'] = quarter_data['high'].max()
                levels[f'{q}_low'] = quarter_data['low'].min()
            else:
                levels[f'{q}_high'] = 0
                levels[f'{q}_low'] = 0
                
        return levels

    def determine_bias(self) -> str:
        """Determine market bias based on quarterly theory and SMA slope"""
        levels = self.get_quarterly_levels()
        current_price = self.data['close'].iloc[-1]
        sma_slope = self.calculate_sma_slope()
        
        if current_price > levels['q2_high'] and sma_slope > 0:
            return 'bullish'
        elif current_price < levels['q3_low'] and sma_slope < 0:
            return 'bearish'
        return 'neutral'

    def find_liquidity_pools(self, lookback: int = 20, threshold: float = 0.005) -> Dict[str, List[Dict]]:
        """Identify stop-loss clusters and PD arrays"""
        recent_data = self.data.tail(lookback)
        
        # Find stop-loss clusters
        clusters = {
            'highs': [],
            'lows': []
        }
        
        # Check for equal highs
        for i in range(len(recent_data) - 2):
            high1 = recent_data['high'].iloc[i]
            count = 1
            for j in range(i + 1, len(recent_data)):
                if abs(recent_data['high'].iloc[j] - high1) / high1 <= threshold:
                    count += 1
            if count >= 3:
                clusters['highs'].append({
                    'price': high1,
                    'count': count,
                    'timestamp': recent_data.index[i]
                })
        
        # Check for equal lows
        for i in range(len(recent_data) - 2):
            low1 = recent_data['low'].iloc[i]
            count = 1
            for j in range(i + 1, len(recent_data)):
                if abs(recent_data['low'].iloc[j] - low1) / low1 <= threshold:
                    count += 1
            if count >= 3:
                clusters['lows'].append({
                    'price': low1,
                    'count': count,
                    'timestamp': recent_data.index[i]
                })
        
        # Calculate PD arrays
        price_range = recent_data['high'].max() - recent_data['low'].min()
        premium_level = recent_data['high'].max() - (price_range * 0.25)
        discount_level = recent_data['low'].min() + (price_range * 0.25)
        
        pd_arrays = {
            'premium': premium_level,
            'equilibrium': (premium_level + discount_level) / 2,
            'discount': discount_level
        }
        
        return {
            'clusters': clusters,
            'pd_arrays': pd_arrays
        }

    def detect_liquidity_events(self, lookback: int = 20) -> Dict[str, List[Dict]]:
        """Detect liquidity sweeps and runs"""
        recent_data = self.data.tail(lookback + 3)  # Extra candles for sweep detection
        avg_volume = recent_data['volume'].mean()
        
        events = {
            'sweeps': [],
            'runs': []
        }
        
        # Detect sweeps
        for i in range(lookback, len(recent_data) - 1):
            # Bullish sweep
            if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-20:i].max() and
                recent_data['close'].iloc[i+1] < recent_data['open'].iloc[i] and
                recent_data['volume'].iloc[i] > 2 * avg_volume):
                events['sweeps'].append({
                    'type': 'bullish',
                    'price': recent_data['high'].iloc[i],
                    'timestamp': recent_data.index[i]
                })
            
            # Bearish sweep
            if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-20:i].min() and
                recent_data['close'].iloc[i+1] > recent_data['open'].iloc[i] and
                recent_data['volume'].iloc[i] > 2 * avg_volume):
                events['sweeps'].append({
                    'type': 'bearish',
                    'price': recent_data['low'].iloc[i],
                    'timestamp': recent_data.index[i]
                })
        
        # Detect runs
        liquidity_zones = self.find_liquidity_pools(lookback)['pd_arrays']
        current_zone = None
        
        for i in range(lookback, len(recent_data) - 5):
            price = recent_data['close'].iloc[i]
            
            # Determine current zone
            if price >= liquidity_zones['premium']:
                zone = 'premium'
            elif price <= liquidity_zones['discount']:
                zone = 'discount'
            else:
                zone = 'equilibrium'
            
            if zone != current_zone:
                # Check if price sustains in new zone
                if all(recent_data['close'].iloc[i:i+5] > liquidity_zones['premium'] if zone == 'premium'
                      else recent_data['close'].iloc[i:i+5] < liquidity_zones['discount'] if zone == 'discount'
                      else (recent_data['close'].iloc[i:i+5] < liquidity_zones['premium'] and
                            recent_data['close'].iloc[i:i+5] > liquidity_zones['discount'])):
                    
                    if recent_data['volume'].iloc[i:i+5].mean() > 1.5 * avg_volume:
                        events['runs'].append({
                            'type': zone,
                            'start_price': price,
                            'end_price': recent_data['close'].iloc[i+4],
                            'start_timestamp': recent_data.index[i],
                            'end_timestamp': recent_data.index[i+4]
                        })
            
            current_zone = zone
        
        return events

    def generate_signals(self) -> Dict:
        """Generate complete ICT analysis signals"""
        bias = self.determine_bias()
        liquidity = self.find_liquidity_pools()
        events = self.detect_liquidity_events()
        
        return {
            'bias': bias,
            'liquidity_zones': {
                'clusters': liquidity['clusters'],
                'pd_arrays': liquidity['pd_arrays']
            },
            'events': events
        } 