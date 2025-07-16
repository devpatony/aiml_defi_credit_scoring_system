# DeFi Credit Scoring for Aave V2 Protocol

A production-ready machine learning system that assigns credit scores (0-1000) to wallet addresses based on their historical transaction behavior in the Aave V2 protocol. Successfully processed **100,000 transactions** from **3,497 unique wallets** with comprehensive behavioral analysis.

## Overview

This project implements an end-to-end credit scoring pipeline that analyzes DeFi transaction patterns to evaluate wallet creditworthiness. The system distinguishes between responsible users and risky/bot-like behavior through sophisticated feature engineering, ensemble machine learning, and domain-specific heuristics.

### Key Results
- **Average Credit Score**: 598/1000 across analyzed wallets
- **Risk Differentiation**: 22.7% excellent performers (700+), 9.5% high-risk (400-)
- **Behavioral Insights**: Clear patterns distinguishing sophisticated vs. risky DeFi usage

## Method Selection & Rationale

### Why Weighted Feature Ensemble Approach?

We chose a **hybrid ML approach** combining weighted feature scoring with unsupervised learning techniques for several key reasons:

1. **Domain Expertise Integration**: Traditional credit scoring relies heavily on expert knowledge of risk factors. Our weighted feature approach allows incorporation of DeFi-specific domain expertise while maintaining ML flexibility.

2. **Unsupervised Learning Necessity**: Unlike traditional finance, DeFi lacks labeled "good" vs "bad" borrowers. We use unsupervised techniques (anomaly detection, clustering) to identify risk patterns without requiring training labels.

3. **Interpretability Requirements**: Credit scoring demands explainable results for regulatory compliance and business understanding. Our feature-weight approach provides clear reasoning for score components.

4. **Scalability & Real-time Capability**: The model architecture supports real-time scoring of new transactions without requiring model retraining.

### Alternative Methods Considered

- **Pure Supervised Learning**: Rejected due to lack of labeled DeFi credit outcomes
- **Graph Neural Networks**: Considered for wallet interaction patterns but deemed overly complex for initial implementation
- **Time Series Models**: Evaluated for temporal patterns but incorporated as features instead of primary methodology

## Complete Technical Architecture

### System Components Overview

<img width="856" height="408" alt="image" src="https://github.com/user-attachments/assets/6290e112-bed8-4c44-a797-c02684541242" />

### 1. Data Processing Layer ('aave_data_loader.py')

**Purpose**: Transform raw Aave V2 transaction data into standardized format for ML consumption.

**Key Functions**:
- **'load_and_transform()'**: Processes large JSON files (91MB+) with memory-efficient chunking
- **'_transform_transaction()'**: Standardizes transaction schema and normalizes amounts
- **'_estimate_gas_used()'**: Estimates gas costs based on transaction type for sophistication scoring

**Input Format Handling**:
```json
{
  "userWallet": "0x...",
  "txHash": "0x...", 
  "action": "deposit",
  "timestamp": 1629178166,
  "actionData": {
    "amount": "2000000000",
    "assetSymbol": "USDC",
    "assetPriceUSD": "0.9938"
  }
}
```
**Output Schema**:
```python
{
  'wallet_address': '0x...',
  'transaction_hash': '0x...',
  'action': 'deposit',
  'amount': '2000.0',  # Normalized
  'asset': 'USDC',
  'timestamp': '2021-08-16T22:29:26Z',  # ISO format
  'gas_used': '150000',  # Estimated
  'usd_value': 1987.64   # Calculated
}
```
### 2. Feature Engineering Layer ('feature_engineering.py')

**Purpose**: Extract 60+ behavioral indicators across four key dimensions of DeFi creditworthiness.

#### Financial Behavior Features (25 features)
- **Volume Patterns**: 'total_volume', 'avg_transaction_size', 'transaction_std'
- **Portfolio Management**: 'asset_concentration_hhi', 'unique_assets', 'avg_position_size'
- **Liquidity Behavior**: 'net_deposit_volume', 'leverage_ratio', 'repay_ratio'

#### Risk Assessment Features (15 features)  
- **Liquidation Analysis**: 'liquidation_frequency', 'liquidation_volume_ratio', 'has_liquidations'
- **Repayment Behavior**: 'repay_consistency_score', 'repay_count', 'borrow_count'
- **Position Risk**: 'position_size_variance', 'max_single_position_ratio'

#### Temporal Features (12 features)
- **Activity Patterns**: 'activity_frequency', 'activity_consistency_cv', 'days_active'
- **Protocol Engagement**: 'tenure_days', 'max_inactive_days'
- **Timing Analysis**: 'avg_time_between_tx_hours', 'weekend_activity_ratio'

#### Network Behavior Features (8 features)
- **Sophistication Indicators**: 'gas_optimization_score', 'transaction_complexity_score'
- **Bot Detection**: 'bot_like_regularity', 'action_diversity_score'
- **Technical Patterns**: 'gas_efficiency_score', 'unique_gas_prices'

**Key Algorithms**:
# Asset concentration using Herfindahl-Hirschman Index
def _calculate_asset_concentration(self, df):
    asset_volumes = df.groupby('asset')['amount'].sum()
    shares = asset_volumes / asset_volumes.sum()
    hhi = (shares ** 2).sum()  # Higher = more concentrated
    return hhi

# Bot detection through transaction regularity
def _detect_bot_like_patterns(self, df):
    time_intervals = df['timestamp'].diff().dt.total_seconds()
    interval_cv = time_intervals.std() / time_intervals.mean()
    bot_score = max(0, 1 - interval_cv * 2)  # Lower CV = more bot-like
    return bot_score

### 3. Machine Learning Scoring Engine ('credit_scorer.py')

**Purpose**: Combine multiple ML techniques with domain expertise to generate robust credit scores.

#### Ensemble ML Architecture

**1. Weighted Feature Scoring** ('_calculate_weighted_score()')

# Feature weights based on credit importance
feature_weights = {
    # Reliability (40% total weight)
    'repay_consistency_score': 0.15,  
    'liquidation_frequency': -0.10,   
    'has_liquidations': -0.10,
    'activity_consistency_cv': -0.05,
    
    # Sophistication (25% total weight)  
    'action_diversity_score': 0.08,
    'gas_optimization_score': 0.07,
    'transaction_complexity_score': 0.05,
    'asset_concentration_hhi': -0.05,
    
    # Volume & Tenure (20% total weight)
    'total_volume': 0.08,
    'tenure_days': 0.07,
    'total_transactions': 0.05,
    
    # Risk Management (15% total weight)
    'leverage_ratio': -0.05,
    'position_size_variance': -0.05,
    'bot_like_regularity': -0.05,
}

**2. Anomaly Detection** ('IsolationForest')
- Identifies outlier wallets with unusual behavior patterns
- 30% score penalty for detected anomalies
- Helps catch sophisticated exploits and bot farms

**3. Risk Clustering** ('KMeans, k=5')
- Segments wallets into behavioral risk groups
- Applies cluster-specific adjustments based on group characteristics
- Enables population-relative scoring

**4. Heuristic Bonuses** ('_apply_heuristic_bonuses()')
python
if tenure_days > 365: bonus += 50        # Long-term user bonus
if total_transactions > 50: bonus += 30   # Activity bonus  
if repay_ratio >= 1.0: bonus += 40       # Perfect repayment
if liquidation_count > 0: bonus -= 30    # Liquidation penalty
if bot_like_regularity > 0.7: bonus -= 100  # Bot penalty

#### Score Normalization Process

1. **Feature Scaling**: 'RobustScaler' for outlier resilience
2. **Outlier Clipping**: 1st-99th percentile bounds
3. **Range Normalization**: Linear scaling to 0-1000
4. **Hard Constraints**: Minimum caps for high-risk wallets

### 4. Analysis & Visualization Layer ('analysis_generator.py')

**Purpose**: Generate comprehensive analysis reports and interactive visualizations.

**Automated Analysis**:
- Score distribution across population segments
- Behavioral pattern identification for high/low scoring wallets
- Risk factor analysis and success factor identification
- Statistical validation of scoring methodology

**Interactive Visualizations**:
- 'score_distribution.html': Population score breakdown by ranges
- 'score_histogram.html': Detailed distribution with percentile markers
- 'behavior_comparison.html': High vs low scorer behavioral comparison

## Detailed Processing Flow

### Phase 1: Data Ingestion & Transformation

<img width="570" height="193" alt="image" src="https://github.com/user-attachments/assets/1f8d4a59-a412-4a61-ac57-2742648f6bd9" />

### Phase 2: Feature Engineering

<img width="655" height="224" alt="image" src="https://github.com/user-attachments/assets/3a0eb879-b45f-47ef-bdff-cb0d740d1215" />

### Phase 3: ML Scoring Pipeline

<img width="604" height="269" alt="image" src="https://github.com/user-attachments/assets/b7752892-3032-4c84-be0d-639efb429e8e" />

### Phase 4: Analysis & Output

<img width="694" height="169" alt="image" src="https://github.com/user-attachments/assets/b68974d2-61bc-4286-b15c-42dc44c8a6de" />

## Implementation Workflow

### Step-by-Step Execution
1. **Data Loading**: 'scorer.load_data(file_path)' processes raw JSON
2. **Feature Extraction**: 'feature_engineer.extract_features(df)' creates behavioral matrix
3. **Base Scoring**: '_calculate_base_scores()' applies weighted feature model
4. **Risk Adjustment**: '_apply_risk_adjustments()' adds ML-based corrections
5. **Normalization**: '_normalize_scores()' scales to 0-1000 range
6. **Analysis Generation**: 'analysis_generator.py' creates comprehensive reports

### Performance Characteristics
- **Processing Speed**: ~10K transactions/minute on standard hardware
- **Memory Usage**: Efficient chunked processing for large datasets
- **Scalability**: Linear scaling with transaction volume
- **Accuracy**: Strong correlation between scores and expected risk patterns

## Quick Start

### Prerequisites
- Python 3.8+
- Required packages (install via 'pip install -r requirements.txt')
- Required packages (install via 'pip install -r requirements.txt')

### Usage

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run Credit Scoring**:
```bash
python credit_scorer.py --input user-wallet-transactions.json --output wallet_scores.csv
```

3. **Generate Analysis Report**:
```bash
python analysis_generator.py --scores wallet_scores.csv
```

### Input Data Format

Expected JSON structure:
```json
[
  {
    "userWallet": "0x...",
    "txHash": "0x...",
    "action": "deposit|borrow|repay|redeemunderlying|liquidationcall",
    "timestamp": 1629178166,
    "actionData": {
      "amount": "2000000000",
      "assetSymbol": "USDC",
      "assetPriceUSD": "0.9938"
    }
  }
]
```

## Credit Scoring Methodology

### Score Ranges
- **900-1000**: Excellent - Highly reliable, sophisticated DeFi users
- **700-899**: Good - Responsible users with minor risk factors
- **500-699**: Fair - Average users with moderate risk patterns
- **300-499**: Poor - High-risk behavior or limited positive history
- **0-299**: Very Poor - Bot-like behavior, exploitation patterns, or high liquidation risk

### Key Scoring Factors

1. **Reliability (40% weight)**
   - Repayment consistency
   - Low liquidation rate
   - Stable activity patterns

2. **Sophistication (25% weight)**
   - Portfolio diversification
   - Optimal gas usage
   - Complex transaction patterns

3. **Volume & Tenure (20% weight)**
   - Total transaction volume
   - Length of protocol usage
   - Growth in activity

4. **Risk Management (15% weight)**
   - Conservative leverage ratios
   - Timely position management
   - Market timing awareness

## Files Structure

├── credit_scorer.py       
├── feature_engineering.py   
├── analysis_generator.py    
├── user-wallet-transactions.json

├── requirements.txt         
├── README.md                
└── analysis.md         

## Model Validation

The model is validated through:
- **Behavioral Consistency**: Scores align with expected risk patterns
- **Edge Case Handling**: Proper treatment of new wallets, inactive accounts
- **Expert Review**: Manual validation of extreme scores
- **Temporal Stability**: Score consistency over time for stable wallets

## Extensibility

The system is designed for easy extension:
- **New Features**: Add features in 'feature_engineering.py'
- **Model Updates**: Modify scoring logic in 'credit_scorer.py'
- **Asset Support**: Extend to new DeFi protocols
- **Real-time Scoring**: Adapt for streaming transaction data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Submit a pull request
## Production Results Summary

### Dataset Processed
- **File Size**: 91MB JSON dataset ('user-wallet-transactions.json')
- **Transaction Volume**: 100,000 Aave V2 transactions
- **Wallet Population**: 3,497 unique wallet addresses
- **Asset Coverage**: 9 different cryptocurrencies (USDC, DAI, USDT, WETH, etc.)
- **Time Period**: March 2021 to September 2021

### Score Distribution Results
- **Average Credit Score**: 598.0 out of 1000
- **Excellent Performers (900-1000)**: 137 wallets (3.9%)
- **Good Credit (700-899)**: 657 wallets (18.8%)
- **Fair Credit (500-699)**: 2,024 wallets (57.9%)
- **Poor Credit (300-499)**: 425 wallets (12.2%)
- **High Risk (0-299)**: 254 wallets (7.3%)

### Key Behavioral Insights
- **High-scoring wallets**: Zero liquidations, 89% repayment consistency
- **Low-scoring wallets**: 0.73 average liquidations, 53% repayment consistency
- **Risk differentiation**: Clear behavioral patterns distinguishing credit tiers


## Production Deployment Guide

### Environment Setup

# Create virtual environment
python -m venv defi_scoring_env
source defi_scoring_env/bin/activate  # Linux/Mac
# or
defi_scoring_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

### Running the System

# Score all wallets from transaction data
python credit_scorer.py --input user-wallet-transactions.json --output wallet_scores.csv

# Generate comprehensive analysis
python analysis_generator.py --scores wallet_scores.csv --output analysis.md


from credit_scorer import DeFiCreditScorer

scorer = DeFiCreditScorer()
# Real-time scoring for new transactions
score = scorer.score_single_wallet(wallet_address, transaction_history)

