# DeFi Credit Scoring for Aave V2 Protocol

A machine learning-based credit scoring system that assigns credit scores (0-1000) to wallet addresses based on their historical transaction behavior in the Aave V2 protocol.

## Overview

This project analyzes DeFi transaction patterns to evaluate wallet creditworthiness, distinguishing between responsible users and risky/bot-like behavior through comprehensive feature engineering and machine learning techniques.

## Architecture

### 1. Data Processing Pipeline
- **Raw Data Input**: JSON file containing transaction-level data
- **Feature Engineering**: Extract behavioral patterns from transaction history
- **Data Validation**: Ensure data quality and handle edge cases
- **Normalization**: Standardize features for ML model consumption

### 2. Feature Engineering Strategy

Our scoring model considers multiple dimensions of DeFi behavior:

#### Financial Behavior Features
- **Transaction Volume Patterns**: Total volume, average transaction size, volume consistency
- **Portfolio Diversification**: Number of different assets used, asset concentration
- **Liquidity Management**: Deposit/withdrawal ratios, holding periods

#### Risk Assessment Features  
- **Leverage Behavior**: Loan-to-deposit ratios, borrowing patterns
- **Liquidation History**: Frequency of liquidations, liquidation amounts
- **Repayment Reliability**: On-time repayments, repayment consistency

#### Temporal Features
- **Activity Consistency**: Transaction frequency over time, activity gaps
- **Protocol Tenure**: Length of engagement with Aave
- **Seasonal Patterns**: Activity during market volatility

#### Network Behavior Features
- **Transaction Timing**: Bot-like regular intervals vs. human-like patterns
- **Gas Optimization**: Evidence of sophisticated vs. amateur usage
- **Interaction Complexity**: Simple vs. complex transaction sequences

### 3. Machine Learning Model

- **Algorithm**: Ensemble approach combining multiple scoring models
- **Training**: Unsupervised learning with expert-defined risk indicators
- **Validation**: Cross-validation with behavioral consistency checks
- **Output**: Credit scores normalized to 0-1000 range

### 4. Processing Flow

Raw JSON Data → Feature Extraction → Risk Assessment → ML Scoring → Credit Score (0-1000)
     ↓                ↓                 ↓              ↓              ↓
Transaction       Behavioral        Risk Flags     Model          Final Score
 Records          Patterns         Detection      Prediction      & Analysis

## Quick Start

### Prerequisites
- Python 3.8+
- Required packages (install via `pip install -r requirements.txt`)

### Usage

1. **Install Dependencies**:
pip install -r requirements.txt

2. **Run Credit Scoring**:
python credit_scorer.py --input sample_transactions.json --output wallet_scores.csv

3. **Generate Analysis Report**:
python analysis_generator.py --scores wallet_scores.csv

### Input Data Format

Expected JSON structure:
   json
[
  {
    "wallet_address": "0x...",
    "transaction_hash": "0x...",
    "action": "deposit|borrow|repay|redeemunderlying|liquidationcall",
    "amount": "1000.5",
    "asset": "USDC",
    "timestamp": "2023-07-15T10:30:00Z",
    "gas_used": "150000",
    "block_number": "17500000"
  }
]

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

├── credit_scorer.py          # Main scoring engine
├── feature_engineering.py    # Feature extraction logic
├── analysis_generator.py     # Score analysis and visualization
├── sample_transactions.json  # Sample data file
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── analysis.md              # Generated analysis report

## Model Validation

The model is validated through:
- **Behavioral Consistency**: Scores align with expected risk patterns
- **Edge Case Handling**: Proper treatment of new wallets, inactive accounts
- **Expert Review**: Manual validation of extreme scores
- **Temporal Stability**: Score consistency over time for stable wallets

## Extensibility

The system is designed for easy extension:
- **New Features**: Add features in `feature_engineering.py`
- **Model Updates**: Modify scoring logic in `credit_scorer.py`
- **Asset Support**: Extend to new DeFi protocols
- **Real-time Scoring**: Adapt for streaming transaction data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Submit a pull request

