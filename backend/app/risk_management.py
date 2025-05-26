import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from entry_systems import EntrySystems

class RiskManagement:
    def __init__(self, data: pd.DataFrame, entry_systems: EntrySystems):
        self.data = data
        self.entry_systems = entry_systems
        self.atr_period = 20
        self.default_balance = 10000
        self.default_risk_percent = 0.01
        self.max_daily_risk = 0.05
        
        # Asset-specific pip values
        self.pip_values = {
            'XAUUSD': 0.01,  # Gold moves in $0.01 increments
            'NASDAQ': 1.0    # NASDAQ moves in 1.0 point increments
        }
    
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

    def calculate_position_size(self, asset: str, entry_price: float, stop_loss: float, 
                              balance: float = None, risk_percent: float = None) -> Dict:
        """Calculate position size based on risk parameters"""
        if balance is None:
            balance = self.default_balance
        if risk_percent is None:
            risk_percent = self.default_risk_percent
            
        # Ensure risk is within limits
        risk_percent = min(risk_percent, 0.02)  # Max 2% risk per trade
        
        # Calculate stop loss distance in pips
        stop_loss_distance = abs(entry_price - stop_loss)
        pip_value = self.pip_values[asset]
        
        # Calculate position size
        risk_amount = balance * risk_percent
        position_size = risk_amount / (stop_loss_distance * pip_value)
        
        return {
            'position_size': position_size,
            'risk_amount': risk_amount,
            'stop_loss_distance': stop_loss_distance,
            'pip_value': pip_value
        }

    def calculate_dynamic_stop_loss(self, entry_price: float, direction: str, 
                                  timeframe: str) -> float:
        """Calculate dynamic stop loss based on timeframe and ATR"""
        atr = self.calculate_atr()
        
        # Adjust ATR multiplier based on timeframe
        if timeframe in ['1m', '5m', '15m']:
            atr_multiplier = 1.5  # Scalping
        else:
            atr_multiplier = 2.0  # Intraday/Weekly
        
        if direction == 'long':
            return entry_price - (atr * atr_multiplier)
        else:
            return entry_price + (atr * atr_multiplier)

    def calculate_trailing_stop(self, entry_price: float, current_price: float, 
                              direction: str, atr: float) -> float:
        """Calculate trailing stop based on price movement"""
        if direction == 'long':
            profit = current_price - entry_price
            if profit >= atr:  # Move to breakeven after 1x ATR profit
                return max(entry_price, current_price - atr)
            return entry_price - (1.5 * atr)  # Initial stop
        else:
            profit = entry_price - current_price
            if profit >= atr:  # Move to breakeven after 1x ATR profit
                return min(entry_price, current_price + atr)
            return entry_price + (1.5 * atr)  # Initial stop

    def calculate_portfolio_metrics(self, signals: List[Dict]) -> Dict:
        """Calculate portfolio metrics from trade signals"""
        if not signals:
            return {
                'win_rate': 0,
                'avg_risk_reward': 0,
                'max_drawdown': 0,
                'total_trades': 0
            }
        
        # Calculate win rate
        winning_trades = sum(1 for signal in signals if signal.get('result') == 'win')
        total_trades = len(signals)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate risk-reward ratios
        risk_rewards = []
        for signal in signals:
            if 'take_profit' in signal and 'stop_loss' in signal:
                risk = abs(signal['entry_price'] - signal['stop_loss'])
                reward = abs(signal['take_profit'] - signal['entry_price'])
                if risk > 0:
                    risk_rewards.append(reward / risk)
        
        avg_risk_reward = np.mean(risk_rewards) if risk_rewards else 0
        
        # Calculate drawdown
        equity_curve = []
        current_equity = self.default_balance
        
        for signal in signals:
            if 'result' in signal and 'risk_amount' in signal:
                if signal['result'] == 'win':
                    current_equity += signal['risk_amount'] * signal.get('risk_reward', 1)
                else:
                    current_equity -= signal['risk_amount']
                equity_curve.append(current_equity)
        
        if equity_curve:
            peak = np.maximum.accumulate(equity_curve)
            drawdown = (peak - equity_curve) / peak
            max_drawdown = np.max(drawdown)
        else:
            max_drawdown = 0
        
        return {
            'win_rate': win_rate,
            'avg_risk_reward': avg_risk_reward,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades
        }

    def generate_risk_metrics(self, asset: str, timeframe: str, 
                            balance: float = None) -> Dict:
        """Generate comprehensive risk metrics for a trade"""
        # Get latest entry signal
        entries = self.entry_systems.generate_entries()
        if not entries:
            return {'error': 'No entry signals available'}
        
        # Get the first available entry signal
        entry = next(iter(entries.values()))
        
        # Calculate position size
        position = self.calculate_position_size(
            asset=asset,
            entry_price=entry['entry_price'],
            stop_loss=entry['stop_loss'],
            balance=balance
        )
        
        # Calculate dynamic stop loss
        dynamic_stop = self.calculate_dynamic_stop_loss(
            entry_price=entry['entry_price'],
            direction=entry['direction'],
            timeframe=timeframe
        )
        
        # Calculate trailing stop
        atr = self.calculate_atr()
        trailing_stop = self.calculate_trailing_stop(
            entry_price=entry['entry_price'],
            current_price=self.data['close'].iloc[-1],
            direction=entry['direction'],
            atr=atr
        )
        
        # Calculate risk-reward ratio
        risk = abs(entry['entry_price'] - entry['stop_loss'])
        reward = abs(entry['take_profit'] - entry['entry_price'])
        risk_reward = reward / risk if risk > 0 else 0
        
        return {
            'position_size': position['position_size'],
            'risk_amount': position['risk_amount'],
            'dynamic_stop_loss': dynamic_stop,
            'trailing_stop': trailing_stop,
            'risk_reward_ratio': risk_reward,
            'atr': atr,
            'pip_value': position['pip_value']
        }

    def check_daily_risk_limit(self, signals: List[Dict], 
                             balance: float = None) -> Dict:
        """Check if daily risk limit is exceeded"""
        if balance is None:
            balance = self.default_balance
        
        # Get today's signals
        today = datetime.now().date()
        today_signals = [
            signal for signal in signals 
            if datetime.fromisoformat(signal['timestamp']).date() == today
        ]
        
        # Calculate total risk for today
        total_risk = sum(
            signal.get('risk_amount', 0) 
            for signal in today_signals
        )
        
        daily_risk_percent = total_risk / balance
        risk_limit_exceeded = daily_risk_percent > self.max_daily_risk
        
        return {
            'daily_risk_percent': daily_risk_percent,
            'risk_limit_exceeded': risk_limit_exceeded,
            'remaining_risk': max(0, (self.max_daily_risk * balance) - total_risk),
            'today_signals': len(today_signals)
        } 