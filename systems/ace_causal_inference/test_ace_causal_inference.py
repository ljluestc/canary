#!/usr/bin/env python3
"""
Tests for ACE Causal Inference Service
"""

import os
import sys
import unittest
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ace_causal_inference_service import (
    CausalInferenceService, CausalInferenceDatabase,
    Dataset, CausalModel, TreatmentEffect
)

class TestDataset(unittest.TestCase):
    """Test Dataset class."""
    
    def test_dataset_creation(self):
        """Test creating a Dataset."""
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [0.1, 0.2, 0.3, 0.4, 0.5],
            'treatment': [0, 1, 0, 1, 0],
            'outcome': [10, 15, 12, 18, 14]
        })
        
        dataset = Dataset(
            dataset_id="test_dataset",
            name="Test Dataset",
            description="A test dataset",
            features=['x1', 'x2'],
            target_variable='outcome',
            treatment_variable='treatment',
            data=data,
            created_at=datetime.now(),
            metadata={"n_samples": 5}
        )
        
        self.assertEqual(dataset.dataset_id, "test_dataset")
        self.assertEqual(dataset.name, "Test Dataset")
        self.assertEqual(len(dataset.features), 2)
        self.assertEqual(dataset.target_variable, "outcome")
        self.assertEqual(dataset.treatment_variable, "treatment")

class TestCausalModel(unittest.TestCase):
    """Test CausalModel class."""
    
    def test_causal_model_creation(self):
        """Test creating a CausalModel."""
        model = CausalModel(
            model_id="test_model",
            dataset_id="test_dataset",
            method="propensity_score_matching",
            parameters={"caliper": 0.1},
            results={"treatment_effect": 2.5},
            created_at=datetime.now(),
            status="completed"
        )
        
        self.assertEqual(model.model_id, "test_model")
        self.assertEqual(model.method, "propensity_score_matching")
        self.assertEqual(model.status, "completed")

class TestTreatmentEffect(unittest.TestCase):
    """Test TreatmentEffect class."""
    
    def test_treatment_effect_creation(self):
        """Test creating a TreatmentEffect."""
        effect = TreatmentEffect(
            effect_id="test_effect",
            model_id="test_model",
            treatment_effect=2.5,
            confidence_interval=(1.0, 4.0),
            p_value=0.05,
            standard_error=0.5,
            method="propensity_score_matching",
            created_at=datetime.now()
        )
        
        self.assertEqual(effect.effect_id, "test_effect")
        self.assertEqual(effect.treatment_effect, 2.5)
        self.assertEqual(effect.confidence_interval, (1.0, 4.0))

class TestCausalInferenceDatabase(unittest.TestCase):
    """Test CausalInferenceDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = CausalInferenceDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization."""
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_and_get_dataset(self):
        """Test saving and retrieving datasets."""
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [0.1, 0.2, 0.3, 0.4, 0.5],
            'treatment': [0, 1, 0, 1, 0],
            'outcome': [10, 15, 12, 18, 14]
        })
        
        dataset = Dataset(
            dataset_id="test_dataset",
            name="Test Dataset",
            description="A test dataset",
            features=['x1', 'x2'],
            target_variable='outcome',
            treatment_variable='treatment',
            data=data,
            created_at=datetime.now(),
            metadata={"n_samples": 5}
        )
        
        # Save dataset
        success = self.db.save_dataset(dataset)
        self.assertTrue(success)
        
        # Retrieve dataset
        retrieved = self.db.get_dataset("test_dataset")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Dataset")
        self.assertEqual(len(retrieved.features), 2)
    
    def test_save_and_get_causal_model(self):
        """Test saving and retrieving causal models."""
        model = CausalModel(
            model_id="test_model",
            dataset_id="test_dataset",
            method="propensity_score_matching",
            parameters={"caliper": 0.1},
            results={"treatment_effect": 2.5},
            created_at=datetime.now(),
            status="completed"
        )
        
        # Save model
        success = self.db.save_causal_model(model)
        self.assertTrue(success)
        
        # Retrieve model
        retrieved = self.db.get_causal_model("test_model")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.method, "propensity_score_matching")
        self.assertEqual(retrieved.status, "completed")
    
    def test_save_and_get_treatment_effect(self):
        """Test saving and retrieving treatment effects."""
        effect = TreatmentEffect(
            effect_id="test_effect",
            model_id="test_model",
            treatment_effect=2.5,
            confidence_interval=(1.0, 4.0),
            p_value=0.05,
            standard_error=0.5,
            method="propensity_score_matching",
            created_at=datetime.now()
        )
        
        # Save effect
        success = self.db.save_treatment_effect(effect)
        self.assertTrue(success)
        
        # Retrieve effects
        effects = self.db.get_treatment_effects("test_model")
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].treatment_effect, 2.5)
    
    def test_list_datasets(self):
        """Test listing datasets."""
        # Create test datasets
        for i in range(3):
            data = pd.DataFrame({
                'x1': [1, 2, 3],
                'treatment': [0, 1, 0],
                'outcome': [10, 15, 12]
            })
            
            dataset = Dataset(
                dataset_id=f"dataset_{i}",
                name=f"Dataset {i}",
                description=f"Test dataset {i}",
                features=['x1'],
                target_variable='outcome',
                treatment_variable='treatment',
                data=data,
                created_at=datetime.now(),
                metadata={"n_samples": 3}
            )
            
            self.db.save_dataset(dataset)
        
        # List datasets
        datasets = self.db.list_datasets()
        self.assertEqual(len(datasets), 3)
        self.assertEqual(datasets[0].name, "Dataset 2")  # Most recent first
    
    def test_list_causal_models(self):
        """Test listing causal models."""
        # Create test models
        for i in range(3):
            model = CausalModel(
                model_id=f"model_{i}",
                dataset_id="test_dataset",
                method="propensity_score_matching",
                parameters={"caliper": 0.1},
                results={"treatment_effect": 2.5},
                created_at=datetime.now(),
                status="completed"
            )
            
            self.db.save_causal_model(model)
        
        # List models
        models = self.db.list_causal_models()
        self.assertEqual(len(models), 3)
        self.assertEqual(models[0].model_id, "model_2")  # Most recent first

class TestCausalInferenceService(unittest.TestCase):
    """Test CausalInferenceService class."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CausalInferenceService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_generate_id(self):
        """Test ID generation."""
        import time
        
        id1 = self.service.generate_id("test")
        time.sleep(0.001)  # Small delay to ensure different timestamps
        id2 = self.service.generate_id("test")
        
        self.assertTrue(id1.startswith("test_"))
        self.assertTrue(id2.startswith("test_"))
        self.assertNotEqual(id1, id2)
    
    def test_create_dataset(self):
        """Test creating a dataset."""
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [0.1, 0.2, 0.3, 0.4, 0.5],
            'treatment': [0, 1, 0, 1, 0],
            'outcome': [10, 15, 12, 18, 14]
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.name, "Test Dataset")
        self.assertEqual(len(dataset.features), 2)
        
        # Verify it's saved to database
        retrieved = self.service.db.get_dataset(dataset.dataset_id)
        self.assertIsNotNone(retrieved)
    
    def test_propensity_score_matching(self):
        """Test propensity score matching."""
        # Create test dataset
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
            'treatment': np.random.binomial(1, 0.5, n),
            'outcome': np.random.normal(0, 1, n)
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        # Run propensity score matching
        results = self.service.propensity_score_matching(dataset, caliper=0.1)
        
        self.assertIn("method", results)
        self.assertEqual(results["method"], "propensity_score_matching")
        self.assertIn("treatment_effect", results)
    
    def test_instrumental_variable(self):
        """Test instrumental variable analysis."""
        # Create test dataset
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
            'instrument': np.random.normal(0, 1, n),
            'treatment': np.random.binomial(1, 0.5, n),
            'outcome': np.random.normal(0, 1, n)
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        # Run instrumental variable analysis
        results = self.service.instrumental_variable(dataset, instrument='instrument')
        
        self.assertIn("method", results)
        self.assertEqual(results["method"], "instrumental_variable")
        self.assertIn("treatment_effect", results)
    
    def test_regression_discontinuity(self):
        """Test regression discontinuity analysis."""
        # Create test dataset
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
            'running_var': np.random.normal(0, 1, n),
            'treatment': (np.random.normal(0, 1, n) > 0).astype(int),
            'outcome': np.random.normal(0, 1, n)
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        # Run regression discontinuity analysis
        results = self.service.regression_discontinuity(
            dataset, running_variable='running_var', cutoff=0.0
        )
        
        self.assertIn("method", results)
        self.assertEqual(results["method"], "regression_discontinuity")
        self.assertIn("treatment_effect", results)
    
    def test_difference_in_differences(self):
        """Test difference-in-differences analysis."""
        # Create test dataset
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
            'time': np.random.binomial(1, 0.5, n),
            'group': np.random.binomial(1, 0.5, n),
            'outcome': np.random.normal(0, 1, n)
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='group'
        )
        
        # Run difference-in-differences analysis
        results = self.service.difference_in_differences(
            dataset, time_variable='time', group_variable='group'
        )
        
        self.assertIn("method", results)
        self.assertEqual(results["method"], "difference_in_differences")
        self.assertIn("treatment_effect", results)
    
    def test_run_causal_analysis(self):
        """Test running causal analysis."""
        # Create test dataset
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [0.1, 0.2, 0.3, 0.4, 0.5],
            'treatment': [0, 1, 0, 1, 0],
            'outcome': [10, 15, 12, 18, 14]
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        # Run analysis
        model = self.service.run_causal_analysis(
            dataset_id=dataset.dataset_id,
            method="propensity_score_matching",
            parameters={"caliper": 0.1}
        )
        
        self.assertIsNotNone(model)
        self.assertEqual(model.method, "propensity_score_matching")
        self.assertEqual(model.dataset_id, dataset.dataset_id)
        
        # Verify it's saved to database
        retrieved = self.service.db.get_causal_model(model.model_id)
        self.assertIsNotNone(retrieved)
    
    def test_get_model_results(self):
        """Test getting model results."""
        # Create test dataset and model
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'treatment': [0, 1, 0, 1, 0],
            'outcome': [10, 15, 12, 18, 14]
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        model = self.service.run_causal_analysis(
            dataset_id=dataset.dataset_id,
            method="propensity_score_matching",
            parameters={"caliper": 0.1}
        )
        
        # Get results
        results = self.service.get_model_results(model.model_id)
        self.assertIsNotNone(results)
        self.assertIn("method", results)
    
    def test_list_available_methods(self):
        """Test listing available methods."""
        methods = self.service.list_available_methods()
        
        self.assertIsInstance(methods, list)
        self.assertGreater(len(methods), 0)
        
        method_names = [method["method"] for method in methods]
        self.assertIn("propensity_score_matching", method_names)
        self.assertIn("instrumental_variable", method_names)
        self.assertIn("regression_discontinuity", method_names)
        self.assertIn("difference_in_differences", method_names)

class TestFlaskApp(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create service with temp database
        self.service = CausalInferenceService(self.temp_db.name)
        
        # Import and configure Flask app
        from ace_causal_inference_service import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Replace the global service instance used by Flask with our test service
        from ace_causal_inference_service import ace_causal_inference_service
        ace_causal_inference_service.db = self.service.db
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_health_check_api(self):
        """Test health check API."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['status'] == 'healthy')
    
    def test_create_dataset_api(self):
        """Test create dataset API."""
        data = {
            'name': 'Test Dataset',
            'description': 'A test dataset',
            'data': {
                'x1': [1, 2, 3, 4, 5],
                'x2': [0.1, 0.2, 0.3, 0.4, 0.5],
                'treatment': [0, 1, 0, 1, 0],
                'outcome': [10, 15, 12, 18, 14]
            },
            'target_variable': 'outcome',
            'treatment_variable': 'treatment',
            'features': ['x1', 'x2']
        }
        
        response = self.client.post('/datasets', json=data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('dataset_id', result)
    
    def test_list_datasets_api(self):
        """Test list datasets API."""
        response = self.client.get('/datasets')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('datasets', data)
    
    def test_get_dataset_api(self):
        """Test get dataset API."""
        # First create a dataset
        data = {
            'name': 'Test Dataset',
            'description': 'A test dataset',
            'data': {
                'x1': [1, 2, 3],
                'treatment': [0, 1, 0],
                'outcome': [10, 15, 12]
            },
            'target_variable': 'outcome',
            'treatment_variable': 'treatment'
        }
        
        create_response = self.client.post('/datasets', json=data)
        dataset_id = create_response.get_json()['dataset_id']
        
        # Now get the dataset
        response = self.client.get(f'/datasets/{dataset_id}')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('dataset', result)
    
    def test_run_analysis_api(self):
        """Test run analysis API."""
        # First create a dataset
        data = {
            'name': 'Test Dataset',
            'description': 'A test dataset',
            'data': {
                'x1': [1, 2, 3],
                'treatment': [0, 1, 0],
                'outcome': [10, 15, 12]
            },
            'target_variable': 'outcome',
            'treatment_variable': 'treatment'
        }
        
        create_response = self.client.post('/datasets', json=data)
        dataset_id = create_response.get_json()['dataset_id']
        
        # Run analysis
        analysis_data = {
            'dataset_id': dataset_id,
            'method': 'propensity_score_matching',
            'parameters': {'caliper': 0.1}
        }
        
        response = self.client.post('/models', json=analysis_data)
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('model_id', result)
    
    def test_get_model_results_api(self):
        """Test get model results API."""
        # First create a dataset and run analysis
        data = {
            'name': 'Test Dataset',
            'description': 'A test dataset',
            'data': {
                'x1': [1, 2, 3],
                'treatment': [0, 1, 0],
                'outcome': [10, 15, 12]
            },
            'target_variable': 'outcome',
            'treatment_variable': 'treatment'
        }
        
        create_response = self.client.post('/datasets', json=data)
        dataset_id = create_response.get_json()['dataset_id']
        
        analysis_data = {
            'dataset_id': dataset_id,
            'method': 'propensity_score_matching',
            'parameters': {'caliper': 0.1}
        }
        
        analysis_response = self.client.post('/models', json=analysis_data)
        model_id = analysis_response.get_json()['model_id']
        
        # Get model results
        response = self.client.get(f'/models/{model_id}')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('model', result)
    
    def test_list_models_api(self):
        """Test list models API."""
        response = self.client.get('/models')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('models', data)
    
    def test_list_methods_api(self):
        """Test list methods API."""
        response = self.client.get('/methods')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('methods', data)
        
        methods = data['methods']
        method_names = [method['method'] for method in methods]
        self.assertIn('propensity_score_matching', method_names)
    
    def test_get_treatment_effects_api(self):
        """Test get treatment effects API."""
        # First create a dataset and run analysis
        data = {
            'name': 'Test Dataset',
            'description': 'A test dataset',
            'data': {
                'x1': [1, 2, 3],
                'treatment': [0, 1, 0],
                'outcome': [10, 15, 12]
            },
            'target_variable': 'outcome',
            'treatment_variable': 'treatment'
        }
        
        create_response = self.client.post('/datasets', json=data)
        dataset_id = create_response.get_json()['dataset_id']
        
        analysis_data = {
            'dataset_id': dataset_id,
            'method': 'propensity_score_matching',
            'parameters': {'caliper': 0.1}
        }
        
        analysis_response = self.client.post('/models', json=analysis_data)
        model_id = analysis_response.get_json()['model_id']
        
        # Get treatment effects
        response = self.client.get(f'/effects/{model_id}')
        self.assertEqual(response.status_code, 200)
        
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('effects', result)

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CausalInferenceService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_get_nonexistent_dataset(self):
        """Test getting non-existent dataset."""
        dataset = self.service.db.get_dataset("nonexistent")
        self.assertIsNone(dataset)
    
    def test_get_nonexistent_model(self):
        """Test getting non-existent model."""
        model = self.service.db.get_causal_model("nonexistent")
        self.assertIsNone(model)
    
    def test_run_analysis_nonexistent_dataset(self):
        """Test running analysis on non-existent dataset."""
        with self.assertRaises(ValueError):
            self.service.run_causal_analysis(
                dataset_id="nonexistent",
                method="propensity_score_matching",
                parameters={}
            )
    
    def test_invalid_method(self):
        """Test running analysis with invalid method."""
        # Create test dataset
        data = pd.DataFrame({
            'x1': [1, 2, 3],
            'treatment': [0, 1, 0],
            'outcome': [10, 15, 12]
        })
        
        dataset = self.service.create_dataset(
            name="Test Dataset",
            description="A test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        # Run analysis with invalid method
        model = self.service.run_causal_analysis(
            dataset_id=dataset.dataset_id,
            method="invalid_method",
            parameters={}
        )
        
        self.assertEqual(model.status, "failed")
        self.assertIn("error", model.results)

class TestPerformance(unittest.TestCase):
    """Test performance and scalability."""
    
    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CausalInferenceService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)
    
    def test_large_dataset_performance(self):
        """Test performance with large dataset."""
        import time
        
        # Create large dataset
        np.random.seed(42)
        n = 1000
        data = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
            'treatment': np.random.binomial(1, 0.5, n),
            'outcome': np.random.normal(0, 1, n)
        })
        
        dataset = self.service.create_dataset(
            name="Large Dataset",
            description="A large test dataset",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )
        
        # Test propensity score matching performance
        start_time = time.time()
        results = self.service.propensity_score_matching(dataset, caliper=0.1)
        end_time = time.time()
        
        self.assertLess(end_time - start_time, 10.0)  # Should complete within 10 seconds
        self.assertIn("method", results)
    
    def test_memory_usage(self):
        """Test memory usage with multiple datasets."""
        # Create multiple datasets
        for i in range(10):
            data = pd.DataFrame({
                'x1': np.random.normal(0, 1, 100),
                'treatment': np.random.binomial(1, 0.5, 100),
                'outcome': np.random.normal(0, 1, 100)
            })
            
            dataset = self.service.create_dataset(
                name=f"Dataset {i}",
                description=f"Test dataset {i}",
                data=data,
                target_variable='outcome',
                treatment_variable='treatment'
            )
            
            # Verify each dataset was created
            retrieved = self.service.db.get_dataset(dataset.dataset_id)
            self.assertIsNotNone(retrieved)
        
        # List all datasets
        datasets = self.service.db.list_datasets()
        self.assertEqual(len(datasets), 10)
        
        # Verify all datasets are accessible
        for dataset in datasets:
            retrieved = self.service.db.get_dataset(dataset.dataset_id)
            self.assertIsNotNone(retrieved)

class TestCausalInferenceErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CausalInferenceService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_database_error_handling_save_dataset(self):
        """Test database error handling when saving dataset."""
        # Create test data
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [0.1, 0.2, 0.3, 0.4, 0.5],
            'treatment': [0, 1, 0, 1, 0],
            'outcome': [10, 15, 12, 18, 14]
        })
        
        # Mock database error
        with patch.object(self.service.db, 'save_dataset', side_effect=Exception("Database error")):
            result = self.service.create_dataset(
                name="Error Dataset",
                description="Error description",
                features=['x1', 'x2'],
                target_variable='outcome',
                treatment_variable='treatment',
                data=data
            )
            self.assertIsNone(result)
    
    def test_invalid_dataset_lookup(self):
        """Test invalid dataset lookup."""
        # Test getting non-existent dataset
        result = self.service.get_dataset("non_existent_dataset")
        self.assertIsNone(result)
    
    def test_invalid_model_lookup(self):
        """Test invalid model lookup."""
        # Test getting non-existent model
        result = self.service.get_model("non_existent_model")
        self.assertIsNone(result)
    
    def test_invalid_treatment_effect_lookup(self):
        """Test invalid treatment effect lookup."""
        # Test getting non-existent treatment effect
        result = self.service.get_treatment_effect("non_existent_effect")
        self.assertIsNone(result)
    
    def test_invalid_dataset_for_model(self):
        """Test creating model with invalid dataset."""
        result = self.service.create_model(
            dataset_id="non_existent_dataset",
            model_type="propensity_score_matching",
            parameters={"caliper": 0.1}
        )
        self.assertIsNone(result)
    
    def test_invalid_model_for_treatment_effect(self):
        """Test estimating treatment effect with invalid model."""
        result = self.service.estimate_treatment_effect(
            model_id="non_existent_model",
            confidence_level=0.95
        )
        self.assertIsNone(result)
    
    def test_invalid_data_format(self):
        """Test creating dataset with invalid data format."""
        # Test with non-DataFrame data
        result = self.service.create_dataset(
            name="Invalid Dataset",
            description="Invalid description",
            features=['x1', 'x2'],
            target_variable='outcome',
            treatment_variable='treatment',
            data="not_a_dataframe"
        )
        self.assertIsNone(result)
    
    def test_missing_columns_in_data(self):
        """Test creating dataset with missing columns."""
        # Test with data missing required columns
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [0.1, 0.2, 0.3, 0.4, 0.5]
            # Missing treatment and outcome columns
        })
        
        result = self.service.create_dataset(
            name="Missing Columns Dataset",
            description="Missing columns description",
            features=['x1', 'x2'],
            target_variable='outcome',
            treatment_variable='treatment',
            data=data
        )
        self.assertIsNone(result)
    
    def test_empty_dataset(self):
        """Test creating model with empty dataset."""
        # Create empty dataset
        data = pd.DataFrame()
        dataset = self.service.create_dataset(
            name="Empty Dataset",
            description="Empty description",
            features=[],
            target_variable='outcome',
            treatment_variable='treatment',
            data=data
        )
        
        if dataset:
            result = self.service.create_model(
                dataset_id=dataset.dataset_id,
                model_type="propensity_score_matching",
                parameters={"caliper": 0.1}
            )
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
