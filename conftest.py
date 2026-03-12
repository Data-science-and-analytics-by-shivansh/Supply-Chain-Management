"""
Pytest Configuration and Shared Fixtures
========================================
Shared test fixtures for Supply Chain Intelligence tests

This file is automatically loaded by pytest
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta


@pytest.fixture(scope="session")
def test_output_dir():
    """Create temporary directory for test outputs"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_supply_chain_data():
    """Generate realistic supply chain orders"""
    np.random.seed(42)
    n_orders = 1000
    
    suppliers = [f'SUP-{i:03d}' for i in range(1, 21)]
    products = ['Electronics', 'Components', 'Raw Materials', 'Finished Goods']
    regions = ['North America', 'Europe', 'Asia', 'South America']
    
    data = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(n_orders):
        supplier = np.random.choice(suppliers)
        
        # Different suppliers have different reliability
        supplier_num = int(supplier.split('-')[1])
        if supplier_num <= 5:  # Top 25% suppliers
            base_delay = 0
            delay_variance = 2
        elif supplier_num <= 15:  # Middle 50%
            base_delay = 2
            delay_variance = 4
        else:  # Bottom 25%
            base_delay = 5
            delay_variance = 7
        
        promised_lead_time = np.random.randint(10, 30)
        actual_delay = max(0, int(np.random.normal(base_delay, delay_variance)))
        actual_lead_time = promised_lead_time + actual_delay
        
        order_date = start_date + timedelta(days=np.random.randint(0, 365))
        delivery_date = order_date + timedelta(days=actual_lead_time)
        
        data.append({
            'order_id': f'ORD-{i+1:06d}',
            'supplier_id': supplier,
            'product_type': np.random.choice(products),
            'region': np.random.choice(regions),
            'order_date': order_date,
            'promised_lead_time': promised_lead_time,
            'actual_lead_time': actual_lead_time,
            'delivery_date': delivery_date,
            'order_quantity': np.random.randint(10, 1000),
            'unit_cost': np.random.uniform(10, 500),
            'defect_rate': np.random.uniform(0.01, 0.05) if supplier_num > 15 else np.random.uniform(0.001, 0.02),
            'return_rate': np.random.uniform(0.005, 0.02) if supplier_num > 15 else np.random.uniform(0.001, 0.01)
        })
    
    df = pd.DataFrame(data)
    df['total_cost'] = df['order_quantity'] * df['unit_cost']
    
    return df


@pytest.fixture
def high_quality_suppliers():
    """Generate data for high-performing suppliers"""
    np.random.seed(42)
    n_orders = 500
    
    return pd.DataFrame({
        'order_id': [f'ORD-Q-{i:05d}' for i in range(n_orders)],
        'supplier_id': np.random.choice(['SUP-EXCELLENT-A', 'SUP-EXCELLENT-B'], n_orders),
        'product_type': ['Electronics'] * n_orders,
        'region': ['North America'] * n_orders,
        'order_date': pd.date_range('2023-01-01', periods=n_orders, freq='D'),
        'promised_lead_time': np.random.randint(10, 15, n_orders),
        'actual_lead_time': np.random.randint(10, 16, n_orders),  # Mostly on time
        'order_quantity': np.random.randint(50, 500, n_orders),
        'unit_cost': np.random.uniform(100, 200, n_orders),
        'defect_rate': np.random.uniform(0.001, 0.005, n_orders),
        'return_rate': np.random.uniform(0.001, 0.005, n_orders)
    })


@pytest.fixture
def poor_quality_suppliers():
    """Generate data for poor-performing suppliers"""
    np.random.seed(42)
    n_orders = 500
    
    return pd.DataFrame({
        'order_id': [f'ORD-P-{i:05d}' for i in range(n_orders)],
        'supplier_id': np.random.choice(['SUP-POOR-A', 'SUP-POOR-B'], n_orders),
        'product_type': ['Components'] * n_orders,
        'region': ['Asia'] * n_orders,
        'order_date': pd.date_range('2023-01-01', periods=n_orders, freq='D'),
        'promised_lead_time': np.random.randint(15, 25, n_orders),
        'actual_lead_time': np.random.randint(20, 40, n_orders),  # Always late
        'order_quantity': np.random.randint(10, 100, n_orders),
        'unit_cost': np.random.uniform(50, 150, n_orders),
        'defect_rate': np.random.uniform(0.05, 0.15, n_orders),
        'return_rate': np.random.uniform(0.02, 0.10, n_orders)
    })


@pytest.fixture
def seasonal_supply_chain_data():
    """Generate data with clear seasonal patterns"""
    np.random.seed(42)
    
    dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
    n_orders = len(dates)
    
    data = []
    for i, date in enumerate(dates):
        # Seasonal effect: longer lead times in winter
        month = date.month
        if month in [11, 12, 1, 2]:  # Winter
            base_lead_time = 20
            delay_variance = 5
        elif month in [3, 4, 5]:  # Spring
            base_lead_time = 15
            delay_variance = 3
        elif month in [6, 7, 8]:  # Summer
            base_lead_time = 12
            delay_variance = 2
        else:  # Fall
            base_lead_time = 14
            delay_variance = 3
        
        actual_lead_time = max(5, int(np.random.normal(base_lead_time, delay_variance)))
        
        data.append({
            'order_id': f'ORD-S-{i:05d}',
            'supplier_id': 'SUP-SEASONAL',
            'product_type': 'Seasonal Product',
            'region': 'Global',
            'order_date': date,
            'promised_lead_time': 15,
            'actual_lead_time': actual_lead_time,
            'order_quantity': np.random.randint(50, 200)
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def mock_config():
    """Mock supply chain configuration"""
    from supply_chain_intelligence import SupplyChainConfig
    
    return SupplyChainConfig(
        supplier_column='supplier_id',
        product_column='product_type',
        region_column='region',
        lead_time_column='actual_lead_time',
        promised_lead_time_column='promised_lead_time',
        order_date_column='order_date',
        otdr_target=0.95,
        max_acceptable_delay=3
    )


@pytest.fixture
def trained_lead_time_predictor(sample_supply_chain_data, mock_config):
    """Pre-trained lead time predictor"""
    from supply_chain_intelligence import LeadTimePredictor
    
    predictor = LeadTimePredictor(mock_config)
    predictor.train(sample_supply_chain_data)
    
    return predictor


@pytest.fixture
def trained_anomaly_detector(sample_supply_chain_data):
    """Pre-trained anomaly detector"""
    from supply_chain_intelligence import AnomalyDetector
    
    detector = AnomalyDetector(contamination=0.05)
    detector.fit(sample_supply_chain_data)
    
    return detector


@pytest.fixture
def large_supply_chain_dataset():
    """Generate large dataset for performance testing"""
    np.random.seed(42)
    n_orders = 10000
    
    return pd.DataFrame({
        'order_id': [f'ORD-L-{i:06d}' for i in range(n_orders)],
        'supplier_id': np.random.choice([f'SUP-{i:03d}' for i in range(1, 51)], n_orders),
        'product_type': np.random.choice(['Electronics', 'Components'], n_orders),
        'region': np.random.choice(['NA', 'EU', 'ASIA'], n_orders),
        'order_date': pd.date_range('2022-01-01', periods=n_orders, freq='4h'),
        'promised_lead_time': np.random.randint(5, 30, n_orders),
        'actual_lead_time': np.random.randint(5, 40, n_orders),
        'order_quantity': np.random.randint(10, 1000, n_orders)
    })


# Helper classes
class Helpers:
    """Helper methods for supply chain tests"""
    
    @staticmethod
    def calculate_otdr(df, promised_col, actual_col, tolerance=3):
        """Calculate on-time delivery rate"""
        delays = df[actual_col] - df[promised_col]
        on_time = (delays <= tolerance).sum()
        total = len(df)
        return on_time / total if total > 0 else 0.0
    
    @staticmethod
    def calculate_delay_metrics(df, promised_col, actual_col):
        """Calculate delay statistics"""
        delays = df[actual_col] - df[promised_col]
        delayed = delays[delays > 0]
        
        return {
            'mean_delay': delayed.mean() if len(delayed) > 0 else 0,
            'max_delay': delays.max(),
            'total_delay_days': delayed.sum() if len(delayed) > 0 else 0,
            'delay_frequency': len(delayed) / len(df) if len(df) > 0 else 0
        }
    
    @staticmethod
    def is_valid_supplier_tier(tier):
        """Check if supplier tier is valid"""
        from supply_chain_intelligence import SupplierTier
        return isinstance(tier, SupplierTier)
    
    @staticmethod
    def generate_delay_pattern(n_samples=100, pattern='consistent'):
        """Generate data with specific delay patterns"""
        np.random.seed(42)
        
        if pattern == 'consistent':
            # Low variance, mostly on time
            return pd.DataFrame({
                'promised_lead_time': [10] * n_samples,
                'actual_lead_time': np.random.normal(10, 1, n_samples).astype(int)
            })
        elif pattern == 'variable':
            # High variance
            return pd.DataFrame({
                'promised_lead_time': [10] * n_samples,
                'actual_lead_time': np.random.normal(15, 5, n_samples).astype(int)
            })
        elif pattern == 'always_late':
            # Consistently delayed
            return pd.DataFrame({
                'promised_lead_time': [10] * n_samples,
                'actual_lead_time': np.random.randint(15, 25, n_samples)
            })
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
    
    @staticmethod
    def calculate_cost_metrics(df):
        """Calculate cost-related metrics"""
        if 'unit_cost' not in df or 'order_quantity' not in df:
            return None
        
        total_cost = (df['unit_cost'] * df['order_quantity']).sum()
        avg_order_value = total_cost / len(df)
        
        return {
            'total_cost': total_cost,
            'avg_order_value': avg_order_value,
            'total_orders': len(df)
        }


@pytest.fixture
def helpers():
    """Provide helper methods to tests"""
    return Helpers()


# Pytest hooks
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "supply_chain: marks tests specific to supply chain logic"
    )
    config.addinivalue_line(
        "markers", "performance: marks performance/benchmark tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "supply_chain" in item.nodeid or "supplier" in item.nodeid:
            item.add_marker(pytest.mark.supply_chain)
        if "performance" in item.nodeid or "large" in item.nodeid:
            item.add_marker(pytest.mark.slow)


# Session-level data
@pytest.fixture(scope="session")
def reference_suppliers():
    """Reference supplier cases for validation"""
    return {
        'excellent_supplier': {
            'otdr': 0.98,
            'mean_lead_time': 11.2,
            'reliability_score': 92,
            'expected_tier': 'STRATEGIC'
        },
        'good_supplier': {
            'otdr': 0.88,
            'mean_lead_time': 13.5,
            'reliability_score': 78,
            'expected_tier': 'PREFERRED'
        },
        'average_supplier': {
            'otdr': 0.75,
            'mean_lead_time': 16.0,
            'reliability_score': 65,
            'expected_tier': 'APPROVED'
        },
        'poor_supplier': {
            'otdr': 0.55,
            'mean_lead_time': 22.0,
            'reliability_score': 45,
            'expected_tier': 'PROBATION'
        }
    }
