"""
Unit Tests for Lead Time Predictor
==================================
Tests for supply_chain_intelligence.py LeadTimePredictor class

Run with: pytest tests/test_lead_time_predictor.py -v
"""

import pytest
import pandas as pd
import numpy as np
from supply_chain_intelligence import (
    LeadTimePredictor,
    SupplyChainConfig
)


class TestLeadTimePredictor:
    """Test suite for LeadTimePredictor class"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        n_samples = 1000
        
        return pd.DataFrame({
            'order_id': [f'ORD-{i:06d}' for i in range(n_samples)],
            'supplier_id': np.random.choice(['SUP-A', 'SUP-B', 'SUP-C'], n_samples),
            'product_type': np.random.choice(['Electronics', 'Components'], n_samples),
            'region': np.random.choice(['North America', 'Europe', 'Asia'], n_samples),
            'order_date': pd.date_range('2023-01-01', periods=n_samples, freq='8h'),
            'promised_lead_time': np.random.randint(5, 30, n_samples),
            'actual_lead_time': np.random.randint(5, 35, n_samples),
            'order_quantity': np.random.randint(10, 1000, n_samples)
        })
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return SupplyChainConfig(
            supplier_column='supplier_id',
            product_column='product_type',
            region_column='region',
            order_date_column='order_date',
            lead_time_column='actual_lead_time',
            promised_lead_time_column='promised_lead_time'
        )
    
    def test_predictor_initialization(self, config):
        """Test predictor initialization"""
        predictor = LeadTimePredictor(config)
        
        assert predictor.config == config
        assert predictor.models is not None
        assert len(predictor.models) > 0
        assert predictor.scaler is not None
        assert not predictor.is_fitted
    
    def test_engineer_features(self, sample_data, config):
        """Test feature engineering"""
        predictor = LeadTimePredictor(config)
        
        X, feature_names = predictor.engineer_features(sample_data, fit=True)
        
        assert X.shape[0] == len(sample_data)
        assert X.shape[1] > 0
        assert len(feature_names) == X.shape[1]
        assert predictor.feature_names is not None
    
    def test_engineer_features_temporal(self, sample_data, config):
        """Test temporal feature extraction"""
        predictor = LeadTimePredictor(config)
        
        X, feature_names = predictor.engineer_features(sample_data, fit=True)
        
        # Should have temporal features
        assert 'order_month' in feature_names
        assert 'order_quarter' in feature_names
        assert 'order_day_of_week' in feature_names
    
    def test_train_basic(self, sample_data, config):
        """Test basic training"""
        predictor = LeadTimePredictor(config)
        
        metrics = predictor.train(sample_data)
        
        assert predictor.is_fitted
        assert 'model_metrics' in metrics
        assert 'ensemble_mae' in metrics
        assert 'ensemble_r2' in metrics
        assert metrics['ensemble_mae'] > 0
    
    def test_train_insufficient_data(self, config):
        """Test training with insufficient data"""
        predictor = LeadTimePredictor(config)
        
        # Very small dataset
        df = pd.DataFrame({
            'supplier_id': ['SUP-A'],
            'product_type': ['Electronics'],
            'region': ['Asia'],
            'promised_lead_time': [10],
            'actual_lead_time': [12]
        })
        
        with pytest.raises(ValueError):
            predictor.train(df)
    
    def test_predict_before_training(self, sample_data, config):
        """Test prediction before training raises error"""
        predictor = LeadTimePredictor(config)
        
        with pytest.raises(ValueError, match="must be fitted first"):
            predictor.predict(sample_data)
    
    def test_predict_basic(self, sample_data, config):
        """Test basic prediction"""
        predictor = LeadTimePredictor(config)
        
        # Split data
        train_data = sample_data[:800]
        test_data = sample_data[800:]
        
        # Train
        predictor.train(train_data)
        
        # Predict
        predictions = predictor.predict(test_data)
        
        assert len(predictions) == len(test_data)
        assert all(pred > 0 for pred in predictions)
    
    def test_predict_with_confidence(self, sample_data, config):
        """Test prediction with confidence intervals"""
        predictor = LeadTimePredictor(config)
        
        train_data = sample_data[:800]
        test_data = sample_data[800:810]
        
        predictor.train(train_data)
        
        predictions, confidence_intervals = predictor.predict(
            test_data,
            return_confidence=True
        )
        
        assert len(predictions) == len(test_data)
        assert confidence_intervals.shape == (len(test_data), 2)
        
        # Confidence intervals should bracket predictions
        for i in range(len(test_data)):
            assert confidence_intervals[i, 0] <= predictions[i] <= confidence_intervals[i, 1]
    
    def test_ensemble_models(self, sample_data, config):
        """Test that all ensemble models are trained"""
        predictor = LeadTimePredictor(config)
        
        predictor.train(sample_data)
        
        # Check all models are fitted
        assert 'ridge' in predictor.models
        assert 'random_forest' in predictor.models
        assert 'gradient_boosting' in predictor.models
    
    def test_model_weights(self, config):
        """Test model weight configuration"""
        predictor = LeadTimePredictor(config)
        
        assert 'ridge' in predictor.model_weights
        assert 'random_forest' in predictor.model_weights
        assert 'gradient_boosting' in predictor.model_weights
        
        # Weights should sum to 1
        total_weight = sum(predictor.model_weights.values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_prediction_consistency(self, sample_data, config):
        """Test that predictions are consistent for same input"""
        predictor = LeadTimePredictor(config)
        
        predictor.train(sample_data[:800])
        
        test_sample = sample_data[800:810]
        
        # Predict twice
        pred1 = predictor.predict(test_sample)
        pred2 = predictor.predict(test_sample)
        
        # Should be identical
        np.testing.assert_array_almost_equal(pred1, pred2)
    
    def test_handle_new_categories(self, sample_data, config):
        """Test handling of unseen categorical values"""
        predictor = LeadTimePredictor(config)
        
        train_data = sample_data[sample_data['supplier_id'] != 'SUP-C']
        predictor.train(train_data)
        
        # Test data with new supplier
        test_data = sample_data[sample_data['supplier_id'] == 'SUP-C'].head(10)
        
        # Should handle gracefully
        predictions = predictor.predict(test_data)
        assert len(predictions) == len(test_data)
    
    def test_prediction_reasonable_range(self, sample_data, config):
        """Test that predictions are in reasonable range"""
        predictor = LeadTimePredictor(config)
        
        predictor.train(sample_data)
        
        predictions = predictor.predict(sample_data.head(100))
        
        # Predictions should be positive
        assert all(pred > 0 for pred in predictions)
        
        # Predictions should be reasonable (not extreme)
        assert all(pred < 100 for pred in predictions)  # Less than 100 days


class TestLeadTimePredictorIntegration:
    """Integration tests for lead time prediction"""
    
    def test_end_to_end_prediction_workflow(self):
        """Test complete prediction workflow"""
        np.random.seed(42)
        
        # Generate realistic data
        n_samples = 2000
        df = pd.DataFrame({
            'supplier_id': np.random.choice(['SUP-FAST', 'SUP-SLOW'], n_samples),
            'product_type': np.random.choice(['Type-A', 'Type-B'], n_samples),
            'region': np.random.choice(['Region-1', 'Region-2'], n_samples),
            'order_date': pd.date_range('2023-01-01', periods=n_samples, freq='6h'),
            'promised_lead_time': np.random.randint(10, 20, n_samples),
            'order_quantity': np.random.randint(10, 500, n_samples)
        })
        
        # Create target: fast supplier = 12 days, slow = 18 days
        df['actual_lead_time'] = df['supplier_id'].map({
            'SUP-FAST': 12,
            'SUP-SLOW': 18
        }) + np.random.normal(0, 2, n_samples)
        
        config = SupplyChainConfig()
        predictor = LeadTimePredictor(config)
        
        # Train/test split
        train_df = df[:1600]
        test_df = df[1600:]
        
        # Train
        metrics = predictor.train(train_df)
        
        assert metrics['ensemble_mae'] < 5  # Should predict reasonably well
        
        # Predict
        predictions = predictor.predict(test_df)
        
        # Predictions for fast supplier should be lower
        fast_preds = predictions[test_df['supplier_id'] == 'SUP-FAST']
        slow_preds = predictions[test_df['supplier_id'] == 'SUP-SLOW']
        
        assert fast_preds.mean() < slow_preds.mean()
    
    def test_model_performance_comparison(self):
        """Test performance of different models in ensemble"""
        np.random.seed(42)
        
        # Generate data with clear pattern
        n_samples = 1000
        df = pd.DataFrame({
            'supplier_id': ['SUP-A'] * n_samples,
            'product_type': ['Product'] * n_samples,
            'region': ['Region'] * n_samples,
            'order_date': pd.date_range('2023-01-01', periods=n_samples, freq='12h'),
            'promised_lead_time': np.random.randint(10, 15, n_samples),
            'order_quantity': np.random.randint(10, 100, n_samples)
        })
        
        # Simple linear relationship
        df['actual_lead_time'] = df['promised_lead_time'] * 1.2 + np.random.normal(0, 1, n_samples)
        
        config = SupplyChainConfig()
        predictor = LeadTimePredictor(config)
        
        metrics = predictor.train(df)
        
        # All models should have reasonable performance
        for model_name, model_metrics in metrics['model_metrics'].items():
            assert model_metrics['mae'] < 10
            assert model_metrics['r2'] > 0
    
    def test_seasonal_pattern_detection(self):
        """Test detection of seasonal patterns"""
        np.random.seed(42)
        
        # Generate data with seasonal pattern
        dates = pd.date_range('2023-01-01', periods=1000, freq='12h')
        df = pd.DataFrame({
            'supplier_id': ['SUP-A'] * 1000,
            'product_type': ['Product'] * 1000,
            'region': ['Region'] * 1000,
            'order_date': dates,
            'promised_lead_time': [10] * 1000,
            'order_quantity': [100] * 1000
        })
        
        # Add seasonal effect (longer in winter months)
        month = df['order_date'].dt.month
        seasonal_effect = np.where((month >= 11) | (month <= 2), 5, 0)
        df['actual_lead_time'] = 10 + seasonal_effect + np.random.normal(0, 1, 1000)
        
        config = SupplyChainConfig()
        predictor = LeadTimePredictor(config)
        
        predictor.train(df)
        
        # Test winter vs summer predictions
        winter_test = df[df['order_date'].dt.month == 12].head(10)
        summer_test = df[df['order_date'].dt.month == 7].head(10)
        
        winter_preds = predictor.predict(winter_test)
        summer_preds = predictor.predict(summer_test)
        
        # Winter should have longer predicted lead times
        assert winter_preds.mean() > summer_preds.mean()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
