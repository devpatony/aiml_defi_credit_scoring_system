import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class FeatureEngineering:
    """
    Comprehensive feature engineering for DeFi transaction data.
    Extracts behavioral patterns from Aave V2 protocol transactions.
    """
    
    def __init__(self):
        self.features = {}
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract all features for each wallet from transaction data.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with engineered features per wallet
        """

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        df['gas_used'] = pd.to_numeric(df['gas_used'], errors='coerce').fillna(0)
        
        wallet_features = []
        
        for wallet, wallet_df in df.groupby('wallet_address'):
            features = self._extract_wallet_features(wallet, wallet_df)
            wallet_features.append(features)
        
        return pd.DataFrame(wallet_features)
    
    def _extract_wallet_features(self, wallet_address: str, df: pd.DataFrame) -> Dict:
        """Extract comprehensive features for a single wallet."""
        
        features = {'wallet_address': wallet_address}
        
        features.update(self._extract_basic_features(df))
        
        features.update(self._extract_financial_features(df))
        
        features.update(self._extract_risk_features(df))
        
        features.update(self._extract_temporal_features(df))
        
        features.update(self._extract_network_features(df))
        
        return features
    
    def _extract_basic_features(self, df: pd.DataFrame) -> Dict:
        """Extract basic transaction statistics."""
        return {
            'total_transactions': len(df),
            'total_volume': df['amount'].sum(),
            'avg_transaction_size': df['amount'].mean(),
            'median_transaction_size': df['amount'].median(),
            'max_transaction_size': df['amount'].max(),
            'min_transaction_size': df['amount'].min(),
            'transaction_std': df['amount'].std(),
            'unique_assets': df['asset'].nunique(),
            'total_gas_used': df['gas_used'].sum(),
            'avg_gas_per_tx': df['gas_used'].mean()
        }
    
    def _extract_financial_features(self, df: pd.DataFrame) -> Dict:
        """Extract financial behavior patterns."""
        action_counts = df['action'].value_counts()
        action_volumes = df.groupby('action')['amount'].sum()
        
        deposits = action_volumes.get('deposit', 0)
        borrows = action_volumes.get('borrow', 0)
        repays = action_volumes.get('repay', 0)
        redeems = action_volumes.get('redeemunderlying', 0)
        
        asset_concentration = self._calculate_asset_concentration(df)
        
        net_deposits = deposits - redeems
        repay_ratio = repays / borrows if borrows > 0 else 0
        
        return {
            'deposit_count': action_counts.get('deposit', 0),
            'borrow_count': action_counts.get('borrow', 0),
            'repay_count': action_counts.get('repay', 0),
            'redeem_count': action_counts.get('redeemunderlying', 0),
            'liquidation_count': action_counts.get('liquidationcall', 0),
            'deposit_volume': deposits,
            'borrow_volume': borrows,
            'repay_volume': repays,
            'redeem_volume': redeems,
            'net_deposit_volume': net_deposits,
            'leverage_ratio': borrows / deposits if deposits > 0 else 0,
            'repay_ratio': repay_ratio,
            'asset_concentration_hhi': asset_concentration,
            'avg_position_size': df.groupby('asset')['amount'].sum().mean(),
        }
    
    def _extract_risk_features(self, df: pd.DataFrame) -> Dict:
        """Extract risk-related behavioral indicators."""
        liquidations = df[df['action'] == 'liquidationcall']
        
        liquidation_frequency = len(liquidations) / len(df) if len(df) > 0 else 0
        liquidation_volume_ratio = liquidations['amount'].sum() / df['amount'].sum() if df['amount'].sum() > 0 else 0
        
        repay_df = df[df['action'] == 'repay']
        borrow_df = df[df['action'] == 'borrow']
        
        repay_consistency = self._calculate_repay_consistency(borrow_df, repay_df)
        
        position_size_variance = df.groupby('asset')['amount'].sum().var()
        
        return {
            'liquidation_frequency': liquidation_frequency,
            'liquidation_volume_ratio': liquidation_volume_ratio,
            'has_liquidations': len(liquidations) > 0,
            'repay_consistency_score': repay_consistency,
            'position_size_variance': position_size_variance,
            'max_single_position_ratio': df.groupby('asset')['amount'].sum().max() / df['amount'].sum() if df['amount'].sum() > 0 else 0,
        }
    
    def _extract_temporal_features(self, df: pd.DataFrame) -> Dict:
        """Extract time-based behavioral patterns."""
        df_sorted = df.sort_values('timestamp')
        
        first_tx = df_sorted['timestamp'].min()
        last_tx = df_sorted['timestamp'].max()
        tenure_days = (last_tx - first_tx).days
        
        daily_activity = df.groupby(df['timestamp'].dt.date).size()
        activity_consistency = daily_activity.std() / daily_activity.mean() if daily_activity.mean() > 0 else 0
        
        time_intervals = df_sorted['timestamp'].diff().dt.total_seconds().dropna()
    
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        weekend_ratio = len(df[df['day_of_week'].isin([5, 6])]) / len(df)
        
        return {
            'tenure_days': tenure_days,
            'activity_frequency': len(df) / max(tenure_days, 1),
            'activity_consistency_cv': activity_consistency,
            'avg_time_between_tx_hours': time_intervals.mean() / 3600 if len(time_intervals) > 0 else 0,
            'median_time_between_tx_hours': time_intervals.median() / 3600 if len(time_intervals) > 0 else 0,
            'weekend_activity_ratio': weekend_ratio,
            'days_active': daily_activity.count(),
            'max_inactive_days': self._calculate_max_inactive_period(df_sorted),
        }
    
    def _extract_network_features(self, df: pd.DataFrame) -> Dict:
        """Extract network and technical behavior indicators."""
        
        gas_efficiency = df['amount'] / df['gas_used'] if df['gas_used'].sum() > 0 else 0
        gas_optimization_score = self._calculate_gas_optimization(df)
        
        action_diversity = df['action'].nunique() / 5
        
        regularity_score = self._detect_bot_like_patterns(df)
        
        return {
            'gas_efficiency_score': gas_efficiency.mean() if hasattr(gas_efficiency, 'mean') else 0,
            'gas_optimization_score': gas_optimization_score,
            'action_diversity_score': action_diversity,
            'bot_like_regularity': regularity_score,
            'unique_gas_prices': df['gas_used'].nunique(),
            'transaction_complexity_score': self._calculate_complexity_score(df),
        }
    
    def _calculate_asset_concentration(self, df: pd.DataFrame) -> float:
        """Calculate Herfindahl-Hirschman Index for asset concentration."""
        asset_volumes = df.groupby('asset')['amount'].sum()
        total_volume = asset_volumes.sum()
        
        if total_volume == 0:
            return 0
            
        shares = asset_volumes / total_volume
        hhi = (shares ** 2).sum()
        return hhi
    
    def _calculate_repay_consistency(self, borrow_df: pd.DataFrame, repay_df: pd.DataFrame) -> float:
        """Calculate repayment consistency score."""
        if len(borrow_df) == 0:
            return 1.0
        
        if len(repay_df) == 0:
            return 0.0
        
        repay_ratio = repay_df['amount'].sum() / borrow_df['amount'].sum()
        return min(repay_ratio, 1.0)
    
    def _calculate_max_inactive_period(self, df_sorted: pd.DataFrame) -> int:
        """Calculate maximum consecutive days without activity."""
        if len(df_sorted) <= 1:
            return 0
        
        dates = df_sorted['timestamp'].dt.date.unique()
        dates = sorted(dates)
        
        max_gap = 0
        current_gap = 0
        
        for i in range(1, len(dates)):
            gap_days = (dates[i] - dates[i-1]).days - 1
            if gap_days > 0:
                current_gap += gap_days
                max_gap = max(max_gap, current_gap)
            else:
                current_gap = 0
        
        return max_gap
    
    def _calculate_gas_optimization(self, df: pd.DataFrame) -> float:
        """Calculate gas optimization score based on efficiency patterns."""
        if df['gas_used'].sum() == 0:
            return 0.5
        
        gas_cv = df['gas_used'].std() / df['gas_used'].mean() if df['gas_used'].mean() > 0 else 1
        optimization_score = max(0, 1 - gas_cv)
        return optimization_score
    
    def _detect_bot_like_patterns(self, df: pd.DataFrame) -> float:
        """Detect bot-like regular transaction patterns."""
        if len(df) < 3:
            return 0.0
        
        df_sorted = df.sort_values('timestamp')
        time_intervals = df_sorted['timestamp'].diff().dt.total_seconds().dropna()
        
        if len(time_intervals) == 0:
            return 0.0
        
        interval_cv = time_intervals.std() / time_intervals.mean() if time_intervals.mean() > 0 else 1
        
        bot_score = max(0, 1 - interval_cv * 2)
        return bot_score
    
    def _calculate_complexity_score(self, df: pd.DataFrame) -> float:
        """Calculate transaction complexity score."""
        action_variety = df['action'].nunique() / 5
        asset_variety = df['asset'].nunique() / max(df['asset'].nunique(), 1)
        amount_variety = 1 - (df['amount'].std() / df['amount'].mean()) if df['amount'].mean() > 0 else 0
        
        complexity = (action_variety + asset_variety + max(0, amount_variety)) / 3
        return complexity
