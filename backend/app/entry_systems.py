import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from ict_analysis import ICTAnalysis

class EntrySystems:
    def __init__(self, data: pd.DataFrame, ict_analysis: ICTAnalysis):
        self.data = data
        self.ict_analysis = ict_analysis
        self.atr_period = 20
        
    def calculate_atr(self) -> float:
        """Calculate Average True Range"""
        high = self.data['high']
        low = self.data['low']
        close = self.data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        
        return atr.iloc[-1]

    def is_volatile(self) -> bool:
        """Check if current volatility is above average"""
        current_atr = self.calculate_atr()
        avg_atr = self.data['high'].rolling(window=self.atr_period).max() - \
                 self.data['low'].rolling(window=self.atr_period).min()
        return current_atr > avg_atr.mean()

    def find_nearest_liquidity_pool(self, price: float, direction: str) -> float:
        """Find nearest liquidity pool in the specified direction"""
        liquidity = self.ict_analysis.find_liquidity_pools()
        
        if direction == 'up':
            # Find nearest level above price
            levels = [pool['price'] for pool in liquidity['clusters']['highs']] + \
                    [liquidity['pd_arrays']['premium']]
            return min([level for level in levels if level > price], default=price * 1.02)
        else:
            # Find nearest level below price
            levels = [pool['price'] for pool in liquidity['clusters']['lows']] + \
                    [liquidity['pd_arrays']['discount']]
            return max([level for level in levels if level < price], default=price * 0.98)

    def turtle_soup(self) -> Optional[Dict]:
        """Detect Turtle Soup patterns"""
        recent_data = self.data.tail(22)  # 20 candles + 2 for reversal
        avg_volume = recent_data['volume'].mean()
        atr = self.calculate_atr()
        
        # Check for bullish Turtle Soup
        if (recent_data['low'].iloc[-3] < recent_data['low'].iloc[-23:-3].min() and
            recent_data['close'].iloc[-1] > recent_data['open'].iloc[-1] and
            recent_data['volume'].iloc[-1] > 2 * avg_volume):
            
            entry_price = recent_data['close'].iloc[-1]
            stop_loss = recent_data['low'].iloc[-3] - (1.5 * atr)
            take_profit = self.find_nearest_liquidity_pool(entry_price, 'up')
            invalidation = recent_data['low'].iloc[-3]
            
            return {
                'system': 'turtle_soup',
                'direction': 'long',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'invalidation_point': invalidation,
                'timestamp': recent_data.index[-1]
            }
        
        # Check for bearish Turtle Soup
        if (recent_data['high'].iloc[-3] > recent_data['high'].iloc[-23:-3].max() and
            recent_data['close'].iloc[-1] < recent_data['open'].iloc[-1] and
            recent_data['volume'].iloc[-1] > 2 * avg_volume):
            
            entry_price = recent_data['close'].iloc[-1]
            stop_loss = recent_data['high'].iloc[-3] + (1.5 * atr)
            take_profit = self.find_nearest_liquidity_pool(entry_price, 'down')
            invalidation = recent_data['high'].iloc[-3]
            
            return {
                'system': 'turtle_soup',
                'direction': 'short',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'invalidation_point': invalidation,
                'timestamp': recent_data.index[-1]
            }
        
        return None

    def crt(self) -> Optional[Dict]:
        """Detect CRT (Constant Range Time) patterns"""
        recent_data = self.data.tail(6)
        avg_volume = recent_data['volume'].mean()
        atr = self.calculate_atr()
        
        # Check for consolidation
        price_range = (recent_data['high'].max() - recent_data['low'].min()) / recent_data['low'].min()
        volume_ratio = recent_data['volume'].mean() / self.data['volume'].rolling(window=20).mean().iloc[-1]
        
        if price_range <= 0.005 and volume_ratio < 0.5:
            range_high = recent_data['high'].max()
            range_low = recent_data['low'].min()
            range_mid = (range_high + range_low) / 2
            
            # Check for breakout
            if recent_data['close'].iloc[-1] > range_high:
                entry_price = recent_data['close'].iloc[-1]
                stop_loss = range_low - (1.5 * atr)
                take_profit = self.find_nearest_liquidity_pool(entry_price, 'up')
                invalidation = range_mid
                
                return {
                    'system': 'crt',
                    'direction': 'long',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'invalidation_point': invalidation,
                    'timestamp': recent_data.index[-1]
                }
            
            elif recent_data['close'].iloc[-1] < range_low:
                entry_price = recent_data['close'].iloc[-1]
                stop_loss = range_high + (1.5 * atr)
                take_profit = self.find_nearest_liquidity_pool(entry_price, 'down')
                invalidation = range_mid
                
                return {
                    'system': 'crt',
                    'direction': 'short',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'invalidation_point': invalidation,
                    'timestamp': recent_data.index[-1]
                }
        
        return None

    def market_maker_model(self) -> Optional[Dict]:
        """Detect Market Maker Model/IPDA patterns"""
        recent_data = self.data.tail(3)
        avg_volume = recent_data['volume'].mean()
        atr = self.calculate_atr()
        
        # Get quarterly levels and bias
        quarterly_levels = self.ict_analysis.get_quarterly_levels()
        bias = self.ict_analysis.determine_bias()
        
        # Check for entries in discount zone during Q2 markup
        if (bias == 'bullish' and
            recent_data['low'].iloc[-1] <= quarterly_levels['q2_low'] and
            recent_data['close'].iloc[-1] > recent_data['open'].iloc[-1] and
            recent_data['volume'].iloc[-1] > 1.5 * avg_volume):
            
            entry_price = recent_data['close'].iloc[-1]
            stop_loss = quarterly_levels['q2_low'] - (1.5 * atr)
            take_profit = self.find_nearest_liquidity_pool(entry_price, 'up')
            invalidation = quarterly_levels['q2_low']
            
            return {
                'system': 'market_maker',
                'direction': 'long',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'invalidation_point': invalidation,
                'timestamp': recent_data.index[-1]
            }
        
        # Check for entries in premium zone during Q3 distribution
        if (bias == 'bearish' and
            recent_data['high'].iloc[-1] >= quarterly_levels['q3_high'] and
            recent_data['close'].iloc[-1] < recent_data['open'].iloc[-1] and
            recent_data['volume'].iloc[-1] > 1.5 * avg_volume):
            
            entry_price = recent_data['close'].iloc[-1]
            stop_loss = quarterly_levels['q3_high'] + (1.5 * atr)
            take_profit = self.find_nearest_liquidity_pool(entry_price, 'down')
            invalidation = quarterly_levels['q3_high']
            
            return {
                'system': 'market_maker',
                'direction': 'short',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'invalidation_point': invalidation,
                'timestamp': recent_data.index[-1]
            }
        
        return None

    def generate_entries(self) -> Dict:
        """Generate entry signals based on market conditions"""
        entries = {}
        
        # Check volatility and generate signals
        if self.is_volatile():
            # Try Turtle Soup first (works well in volatile markets)
            turtle_soup = self.turtle_soup()
            if turtle_soup:
                entries['turtle_soup'] = turtle_soup
        
        # Try CRT (works in both volatile and ranging markets)
        crt = self.crt()
        if crt:
            entries['crt'] = crt
        
        # Try Market Maker Model (works best in trending markets)
        market_maker = self.market_maker_model()
        if market_maker:
            entries['market_maker'] = market_maker
        
        return entries 