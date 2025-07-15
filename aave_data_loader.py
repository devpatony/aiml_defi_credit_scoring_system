import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List

class AaveDataLoader:
    """
    Data loader specifically designed for Aave V2 transaction data format.
    Handles the specific JSON structure from user-wallet-transactions.json
    """
    
    def __init__(self):
        pass
    
    def load_and_transform(self, file_path: str) -> pd.DataFrame:
        """
        Load the Aave transaction data and transform it to the expected format.
        
        Args:
            file_path: Path to the JSON file with Aave transaction data
            
        Returns:
            DataFrame with standardized transaction data
        """
        print(f"Loading Aave transaction data from {file_path}...")
        
        try:
            transactions = []
            chunk_size = 10000
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"Loaded {len(data)} raw transactions")
            
            for i, tx in enumerate(data):
                if i % 10000 == 0:
                    print(f"Processing transaction {i+1}/{len(data)}")
                
                transformed_tx = self._transform_transaction(tx)
                if transformed_tx: 
                    transactions.append(transformed_tx)
            
            df = pd.DataFrame(transactions)
            print(f"Successfully transformed {len(df)} transactions for {df['wallet_address'].nunique() if len(df) > 0 else 0} unique wallets")
            
            return df
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def _transform_transaction(self, tx: dict) -> dict:
        """Transform a single transaction to the expected format."""
        
        try:
            wallet_address = tx.get('userWallet', '').lower()
            transaction_hash = tx.get('txHash', '')
            action = tx.get('action', '')
            
            timestamp = tx.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                timestamp_iso = dt.isoformat() + 'Z'
            else:
                timestamp_iso = None
            
            action_data = tx.get('actionData', {})
            amount = action_data.get('amount', '0')
            asset = action_data.get('assetSymbol', 'UNKNOWN')
            asset_price_usd = action_data.get('assetPriceUSD', '0')
            
            try:
                amount_numeric = float(amount) / 1e6 if amount else 0
                price_numeric = float(asset_price_usd) if asset_price_usd else 0
                usd_value = amount_numeric * price_numeric
            except:
                amount_numeric = 0
                usd_value = 0
            
            block_number = tx.get('blockNumber', 0)
            gas_used = self._estimate_gas_used(action)
            
            transformed = {
                'wallet_address': wallet_address,
                'transaction_hash': transaction_hash,
                'action': action,
                'amount': str(amount_numeric),
                'asset': asset,
                'timestamp': timestamp_iso,
                'gas_used': str(gas_used),
                'block_number': str(block_number),
                'usd_value': usd_value,
                'asset_price_usd': asset_price_usd
            }
            
            return transformed
            
        except Exception as e:
            print(f"Error transforming transaction: {e}")
            return None
    
    def _estimate_gas_used(self, action: str) -> int:
        """Estimate gas usage based on action type."""
        gas_estimates = {
            'deposit': 150000,
            'borrow': 180000,
            'repay': 160000,
            'redeemunderlying': 170000,
            'liquidationcall': 220000,
            'withdraw': 170000,
            'flashloan': 200000
        }
        
        return gas_estimates.get(action.lower(), 150000)
    
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """Get a summary of the loaded data."""
        
        if df.empty:
            return {"error": "No data loaded"}
        
        summary = {
            'total_transactions': len(df),
            'unique_wallets': df['wallet_address'].nunique(),
            'unique_assets': df['asset'].nunique(),
            'date_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            },
            'action_distribution': df['action'].value_counts().to_dict(),
            'total_usd_volume': df['usd_value'].sum(),
            'avg_transaction_usd': df['usd_value'].mean(),
            'top_assets': df['asset'].value_counts().head(10).to_dict()
        }
        
        return summary
