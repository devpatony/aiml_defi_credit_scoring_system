import json
import pandas as pd
import numpy as np
import argparse
from datetime import datetime
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from feature_engineering import FeatureEngineering
from aave_data_loader import AaveDataLoader
import warnings
warnings.filterwarnings('ignore')

class DeFiCreditScorer:
    """
    Machine Learning-based credit scoring system for DeFi wallets.
    Assigns scores from 0-1000 based on transaction behavior patterns.
    """
    
    def __init__(self):
        self.feature_engineer = FeatureEngineering()
        self.data_loader = AaveDataLoader()
        self.scaler = RobustScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.risk_clusterer = KMeans(n_clusters=5, random_state=42)
        self.feature_weights = self._define_feature_weights()
        
    def _define_feature_weights(self) -> dict:
        """Define weights for different feature categories based on importance."""
        return {
            'repay_consistency_score': 0.15,
            'liquidation_frequency': -0.10, 
            'activity_consistency_cv': -0.05,
            'has_liquidations': -0.10,
            
            'action_diversity_score': 0.08,
            'asset_concentration_hhi': -0.05,
            'gas_optimization_score': 0.07,
            'transaction_complexity_score': 0.05,
            
            'total_volume': 0.08,
            'tenure_days': 0.07,
            'total_transactions': 0.05,
            
            'leverage_ratio': -0.05,  
            'position_size_variance': -0.05,
            'bot_like_regularity': -0.05,
        }
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load transaction data from JSON file using the Aave data loader."""
        try:
            df = self.data_loader.load_and_transform(file_path)
            
            if not df.empty:
                summary = self.data_loader.get_data_summary(df)
                print("\n=== DATA SUMMARY ===")
                print(f"Total transactions: {summary['total_transactions']:,}")
                print(f"Unique wallets: {summary['unique_wallets']:,}")
                print(f"Unique assets: {summary['unique_assets']}")
                print(f"Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
                print(f"Total USD volume: ${summary['total_usd_volume']:,.2f}")
                print(f"Average transaction USD: ${summary['avg_transaction_usd']:.2f}")
                
                print("\nAction distribution:")
                for action, count in summary['action_distribution'].items():
                    print(f"  {action}: {count:,}")
                
                print("\nTop 5 assets:")
                for asset, count in list(summary['top_assets'].items())[:5]:
                    print(f"  {asset}: {count:,} transactions")
            
            return df
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def score_wallets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate credit scores for all wallets in the dataset.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with wallet addresses and their credit scores
        """
        print("Extracting features...")
        features_df = self.feature_engineer.extract_features(df)
        
        if features_df.empty:
            print("No features extracted. Check input data.")
            return pd.DataFrame()
        
        print(f"Extracted features for {len(features_df)} wallets")
        
        print("Calculating base credit scores...")
        scores_df = self._calculate_base_scores(features_df)
        
        print("Applying risk adjustments...")
        scores_df = self._apply_risk_adjustments(scores_df, features_df)
        
        print("Normalizing scores...")
        scores_df = self._normalize_scores(scores_df)
        
        result_df = scores_df.merge(features_df, on='wallet_address', how='left')
        
        print(f"Credit scoring complete for {len(result_df)} wallets")
        return result_df
    
    def _calculate_base_scores(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate base credit scores using weighted feature approach."""
        
        feature_cols = [col for col in features_df.columns if col != 'wallet_address']
        X = features_df[feature_cols].fillna(0)
        
        X = X.replace([np.inf, -np.inf], 0)
        
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=feature_cols, index=features_df.index)
        
        scores = []
        for idx, row in X_scaled_df.iterrows():
            score = self._calculate_weighted_score(row, features_df.iloc[idx])
            scores.append(score)
        
        result_df = pd.DataFrame({
            'wallet_address': features_df['wallet_address'],
            'base_score': scores
        })
        
        return result_df
    
    def _calculate_weighted_score(self, scaled_features: pd.Series, raw_features: pd.Series) -> float:
        """Calculate weighted score for a single wallet."""
        
        score = 500
        
        for feature, weight in self.feature_weights.items():
            if feature in scaled_features.index:
                feature_value = np.clip(scaled_features[feature], -3, 3)
                score += weight * feature_value * 100
        
        score += self._apply_heuristic_bonuses(raw_features)
        
        return score
    
    def _apply_heuristic_bonuses(self, features: pd.Series) -> float:
        """Apply domain-specific heuristic bonuses/penalties."""
        bonus = 0
        
        if features.get('tenure_days', 0) > 365:
            bonus += 50 
        elif features.get('tenure_days', 0) > 180:
            bonus += 25
            
        if features.get('total_transactions', 0) > 50:
            bonus += 30
        elif features.get('total_transactions', 0) > 20:
            bonus += 15
            
        if features.get('unique_assets', 0) > 5:
            bonus += 20
        elif features.get('unique_assets', 0) > 3:
            bonus += 10
        
        if features.get('repay_ratio', 0) >= 1.0 and features.get('borrow_count', 0) > 0:
            bonus += 40
            
        if features.get('liquidation_count', 0) > 0:
            bonus -= features.get('liquidation_count', 0) * 30
            
        if features.get('bot_like_regularity', 0) > 0.7:
            bonus -= 100
            
        return bonus
    
    def _apply_risk_adjustments(self, scores_df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
        """Apply ML-based risk adjustments using anomaly detection."""
        
        feature_cols = [col for col in features_df.columns if col != 'wallet_address']
        X = features_df[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
        
        anomaly_scores = self.anomaly_detector.fit_predict(self.scaler.transform(X))
        
        scores_df['risk_adjusted_score'] = scores_df['base_score'].copy()
        anomaly_mask = anomaly_scores == -1
        scores_df.loc[anomaly_mask, 'risk_adjusted_score'] *= 0.7
        
        risk_clusters = self.risk_clusterer.fit_predict(self.scaler.transform(X))
        
        for cluster in range(5):
            cluster_mask = risk_clusters == cluster
            cluster_features = features_df[cluster_mask]
            
            if len(cluster_features) > 0:
                avg_liquidations = cluster_features['liquidation_frequency'].mean()
                if avg_liquidations > 0.1:  
                    scores_df.loc[cluster_mask, 'risk_adjusted_score'] *= 0.8
                elif avg_liquidations < 0.01:  
                    scores_df.loc[cluster_mask, 'risk_adjusted_score'] *= 1.1
        
        return scores_df
    
    def _normalize_scores(self, scores_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize scores to 0-1000 range with proper distribution."""
        
        scores = scores_df['risk_adjusted_score'].values
        
        q1, q99 = np.percentile(scores, [1, 99])
        scores_clipped = np.clip(scores, q1, q99)
        
        min_score, max_score = scores_clipped.min(), scores_clipped.max()
        if max_score > min_score:
            normalized_scores = 1000 * (scores_clipped - min_score) / (max_score - min_score)
        else:
            normalized_scores = np.full_like(scores_clipped, 500)
        
        final_scores = []
        for i, (_, row) in enumerate(scores_df.iterrows()):
            score = normalized_scores[i]
            
            if row.get('base_score', 500) < 200: 
                score = min(score, 300)
            elif row.get('base_score', 500) > 800:
                score = max(score, 700)
            
            final_scores.append(max(0, min(1000, score)))
        
        scores_df['credit_score'] = final_scores
        scores_df['score_category'] = scores_df['credit_score'].apply(self._categorize_score)
        
        return scores_df
    
    def _categorize_score(self, score: float) -> str:
        """Categorize scores into risk buckets."""
        if score >= 900:
            return "Excellent (900-1000)"
        elif score >= 700:
            return "Good (700-899)"
        elif score >= 500:
            return "Fair (500-699)"
        elif score >= 300:
            return "Poor (300-499)"
        else:
            return "Very Poor (0-299)"
    
    def save_results(self, results_df: pd.DataFrame, output_path: str):
        """Save scoring results to CSV file."""
        
        output_cols = ['wallet_address', 'credit_score', 'score_category', 'base_score', 
                      'risk_adjusted_score', 'total_transactions', 'total_volume', 
                      'tenure_days', 'liquidation_count', 'repay_consistency_score']
        
        output_df = results_df[output_cols].copy()
        output_df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")
        
        print("\n=== SCORING SUMMARY ===")
        print(f"Total wallets scored: {len(output_df)}")
        print(f"Average credit score: {output_df['credit_score'].mean():.1f}")
        print(f"Median credit score: {output_df['credit_score'].median():.1f}")
        print("\nScore distribution:")
        print(output_df['score_category'].value_counts().sort_index())

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='DeFi Credit Scoring System')
    parser.add_argument('--input', required=True, help='Input JSON file with transaction data')
    parser.add_argument('--output', default='wallet_scores.csv', help='Output CSV file for scores')
    
    args = parser.parse_args()
    
    print("=== DeFi Credit Scoring System ===")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    
    scorer = DeFiCreditScorer()
    
    df = scorer.load_data(args.input)
    if df.empty:
        print("Failed to load data. Exiting.")
        return
    
    results = scorer.score_wallets(df)
    if results.empty:
        print("Failed to generate scores. Exiting.")
        return
    scorer.save_results(results, args.output)
    
    print("\n=== Credit scoring completed successfully! ===")

if __name__ == "__main__":
    main()
