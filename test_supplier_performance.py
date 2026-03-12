"""
Unit Tests for Supplier Performance Analyzer
=============================================
Tests for supply_chain_intelligence.py SupplierPerformanceAnalyzer class

Run with: pytest tests/test_supplier_performance.py -v
"""

import pytest
import pandas as pd
import numpy as np
from supply_chain_intelligence import (
    SupplierPerformanceAnalyzer,
    SupplierPerformance,
    SupplierTier,
    SupplyChainConfig
)


class TestSupplierPerformanceAnalyzer:
    """Test suite for SupplierPerformanceAnalyzer class"""
    
    @pytest.fixture
    def sample_orders(self):
        """Create sample order data"""
        np.random.seed(42)
        n_orders = 1000
        
        return pd.DataFrame({
            'order_id': [f'ORD-{i:06d}' for i in range(n_orders)],
            'supplier_id': np.random.choice(['SUP-001', 'SUP-002', 'SUP-003'], n_orders),
            'product_type': np.random.choice(['Electronics', 'Components'], n_orders),
            'region': np.random.choice(['North America', 'Europe', 'Asia'], n_orders),
            'order_date': pd.date_range('2023-01-01', periods=n_orders, freq='6h'),
            'promised_lead_time': np.random.randint(5, 30, n_orders),
            'actual_lead_time': np.random.randint(5, 35, n_orders),
            'order_quantity': np.random.randint(10, 1000, n_orders),
            'unit_cost': np.random.uniform(10, 500, n_orders)
        })
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return SupplyChainConfig(
            supplier_column='supplier_id',
            promised_lead_time_column='promised_lead_time',
            lead_time_column='actual_lead_time',
            otdr_target=0.95,
            max_acceptable_delay=3
        )
    
    def test_calculate_otdr(self, sample_orders, config):
        """Test on-time delivery rate calculation"""
        analyzer = SupplierPerformanceAnalyzer()
        
        otdr = analyzer.calculate_otdr(sample_orders, config)
        
        assert isinstance(otdr, dict)
        assert len(otdr) > 0
        assert all(0 <= rate <= 1 for rate in otdr.values())
        assert 'SUP-001' in otdr
    
    def test_calculate_otdr_perfect_supplier(self, config):
        """Test OTDR for perfect supplier (all on-time)"""
        analyzer = SupplierPerformanceAnalyzer()
        
        df = pd.DataFrame({
            'supplier_id': ['SUP-PERFECT'] * 100,
            'promised_lead_time': [10] * 100,
            'actual_lead_time': [10] * 100  # Always on time
        })
        
        otdr = analyzer.calculate_otdr(df, config)
        
        assert otdr['SUP-PERFECT'] == 1.0
    
    def test_calculate_otdr_poor_supplier(self, config):
        """Test OTDR for poor supplier (always late)"""
        analyzer = SupplierPerformanceAnalyzer()
        
        df = pd.DataFrame({
            'supplier_id': ['SUP-POOR'] * 100,
            'promised_lead_time': [10] * 100,
            'actual_lead_time': [20] * 100  # Always 10 days late
        })
        
        otdr = analyzer.calculate_otdr(df, config)
        
        assert otdr['SUP-POOR'] == 0.0
    
    def test_calculate_reliability_score(self):
        """Test reliability score calculation"""
        analyzer = SupplierPerformanceAnalyzer()
        
        # Perfect supplier
        score = analyzer.calculate_reliability_score(
            otdr=0.95,
            lead_time_variance=0.05,
            defect_rate=0.01,
            delay_frequency=0.05
        )
        
        assert 0 <= score <= 100
        assert score >= 80  # Should be high
    
    def test_calculate_reliability_score_poor(self):
        """Test reliability score for poor supplier"""
        analyzer = SupplierPerformanceAnalyzer()
        
        score = analyzer.calculate_reliability_score(
            otdr=0.60,
            lead_time_variance=0.30,
            defect_rate=0.10,
            delay_frequency=0.40
        )
        
        assert 0 <= score <= 100
        assert score < 60  # Should be low
    
    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        analyzer = SupplierPerformanceAnalyzer()
        
        # Low risk supplier
        low_risk = analyzer.calculate_risk_score(
            lead_time_variance=0.05,
            delay_frequency=0.05,
            single_source=False,
            region_risk=0.1
        )
        
        # High risk supplier
        high_risk = analyzer.calculate_risk_score(
            lead_time_variance=0.30,
            delay_frequency=0.40,
            single_source=True,
            region_risk=0.8
        )
        
        assert 0 <= low_risk <= 100
        assert 0 <= high_risk <= 100
        assert high_risk > low_risk
    
    def test_classify_supplier_tier_strategic(self):
        """Test strategic tier classification"""
        analyzer = SupplierPerformanceAnalyzer()
        
        tier = analyzer.classify_supplier_tier(
            reliability_score=90,
            risk_score=20,
            total_orders=100
        )
        
        assert tier == SupplierTier.STRATEGIC
    
    def test_classify_supplier_tier_probation(self):
        """Test probation tier classification"""
        analyzer = SupplierPerformanceAnalyzer()
        
        tier = analyzer.classify_supplier_tier(
            reliability_score=50,
            risk_score=75,
            total_orders=100
        )
        
        assert tier == SupplierTier.PROBATION
    
    def test_classify_supplier_tier_new_supplier(self):
        """Test classification for new supplier with few orders"""
        analyzer = SupplierPerformanceAnalyzer()
        
        tier = analyzer.classify_supplier_tier(
            reliability_score=85,
            risk_score=30,
            total_orders=5  # Very few orders
        )
        
        assert tier == SupplierTier.APPROVED  # Default for new suppliers
    
    def test_analyze_supplier_performance(self, sample_orders, config):
        """Test full supplier performance analysis"""
        analyzer = SupplierPerformanceAnalyzer()
        
        performance = analyzer.analyze_supplier_performance(
            sample_orders,
            config,
            'SUP-001'
        )
        
        assert isinstance(performance, SupplierPerformance)
        assert performance.supplier_id == 'SUP-001'
        assert performance.total_orders > 0
        assert 0 <= performance.otdr <= 1
        assert 0 <= performance.reliability_score <= 100
        assert 0 <= performance.risk_score <= 100
        assert performance.tier in SupplierTier
    
    def test_analyze_supplier_performance_invalid_supplier(self, sample_orders, config):
        """Test analysis with invalid supplier ID"""
        analyzer = SupplierPerformanceAnalyzer()
        
        with pytest.raises(ValueError, match="No data for supplier"):
            analyzer.analyze_supplier_performance(
                sample_orders,
                config,
                'SUP-INVALID'
            )
    
    def test_delay_metrics_calculation(self, config):
        """Test delay metrics calculation"""
        analyzer = SupplierPerformanceAnalyzer()
        
        df = pd.DataFrame({
            'supplier_id': ['SUP-TEST'] * 100,
            'promised_lead_time': [10] * 100,
            'actual_lead_time': [10, 15, 12, 20, 11] * 20  # Some delays
        })
        
        performance = analyzer.analyze_supplier_performance(df, config, 'SUP-TEST')
        
        assert performance.total_delay_days > 0
        assert performance.mean_delay > 0
        assert performance.max_delay >= performance.mean_delay
        assert 0 <= performance.delay_frequency <= 1
    
    def test_lead_time_variance_calculation(self, config):
        """Test lead time variance calculation"""
        analyzer = SupplierPerformanceAnalyzer()
        
        # Consistent supplier (low variance)
        consistent_df = pd.DataFrame({
            'supplier_id': ['SUP-CONSISTENT'] * 100,
            'actual_lead_time': [10, 11, 10, 11] * 25  # Very consistent
        })
        
        # Inconsistent supplier (high variance)
        inconsistent_df = pd.DataFrame({
            'supplier_id': ['SUP-INCONSISTENT'] * 100,
            'actual_lead_time': np.random.randint(5, 30, 100)  # Very variable
        })
        
        perf_consistent = analyzer.analyze_supplier_performance(
            consistent_df, config, 'SUP-CONSISTENT'
        )
        perf_inconsistent = analyzer.analyze_supplier_performance(
            inconsistent_df, config, 'SUP-INCONSISTENT'
        )
        
        assert perf_consistent.lead_time_variance < perf_inconsistent.lead_time_variance


class TestSupplierPerformanceIntegration:
    """Integration tests for supplier performance analysis"""
    
    def test_multi_supplier_analysis(self):
        """Test analyzing multiple suppliers"""
        np.random.seed(42)
        config = SupplyChainConfig()
        
        # Create data for 3 suppliers with different performance
        df = pd.DataFrame({
            'supplier_id': ['SUP-GOOD'] * 300 + ['SUP-OK'] * 300 + ['SUP-POOR'] * 300,
            'promised_lead_time': [10] * 900,
            'actual_lead_time': (
                [10, 11] * 150 +  # Good: mostly on time
                [10, 15] * 150 +  # OK: some delays
                [15, 20] * 150    # Poor: always late
            )
        })
        
        analyzer = SupplierPerformanceAnalyzer()
        
        # Analyze each
        good = analyzer.analyze_supplier_performance(df, config, 'SUP-GOOD')
        ok = analyzer.analyze_supplier_performance(df, config, 'SUP-OK')
        poor = analyzer.analyze_supplier_performance(df, config, 'SUP-POOR')
        
        # Verify ranking
        assert good.reliability_score > ok.reliability_score > poor.reliability_score
        assert good.otdr > ok.otdr > poor.otdr
    
    def test_tier_distribution(self):
        """Test realistic tier distribution"""
        np.random.seed(42)
        config = SupplyChainConfig()
        
        # Generate realistic supplier data
        suppliers = []
        for i in range(50):
            supplier_id = f'SUP-{i:03d}'
            
            # Most suppliers are good, some are poor
            if i < 10:  # Top 20%
                base_lead_time = 10
                variance = 1
            elif i < 35:  # Middle 50%
                base_lead_time = 12
                variance = 3
            else:  # Bottom 30%
                base_lead_time = 15
                variance = 5
            
            for _ in range(100):
                suppliers.append({
                    'supplier_id': supplier_id,
                    'promised_lead_time': 10,
                    'actual_lead_time': int(base_lead_time + np.random.normal(0, variance))
                })
        
        df = pd.DataFrame(suppliers)
        analyzer = SupplierPerformanceAnalyzer()
        
        # Analyze all suppliers
        tiers = []
        for i in range(50):
            perf = analyzer.analyze_supplier_performance(df, config, f'SUP-{i:03d}')
            tiers.append(perf.tier)
        
        # Check distribution makes sense
        tier_counts = pd.Series(tiers).value_counts()
        
        # Should have some of each tier
        assert len(tier_counts) >= 3
        # Strategic should be minority
        assert tier_counts.get(SupplierTier.STRATEGIC, 0) < 15


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
