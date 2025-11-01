#!/usr/bin/env python3
"""
Additional tests to achieve 95%+ coverage for ACE Causal Inference Service
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


class TestAdditionalCoverage(unittest.TestCase):
    """Additional tests to improve coverage."""

    def setUp(self):
        """Set up test service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CausalInferenceService(self.temp_db.name)

    def tearDown(self):
        """Clean up test service."""
        os.unlink(self.temp_db.name)

    def test_run_causal_analysis_instrumental_variable(self):
        """Test run_causal_analysis with instrumental_variable method - line 629."""
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
            name="Test IV",
            description="Test instrumental variable",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )

        model = self.service.run_causal_analysis(
            dataset_id=dataset.dataset_id,
            method="instrumental_variable",
            parameters={"instrument": "instrument"}
        )

        self.assertEqual(model.status, "completed")
        self.assertEqual(model.method, "instrumental_variable")

    def test_run_causal_analysis_regression_discontinuity(self):
        """Test run_causal_analysis with regression_discontinuity method - line 631."""
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
            name="Test RD",
            description="Test regression discontinuity",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment'
        )

        model = self.service.run_causal_analysis(
            dataset_id=dataset.dataset_id,
            method="regression_discontinuity",
            parameters={"running_variable": "running_var", "cutoff": 0.0}
        )

        self.assertEqual(model.status, "completed")
        self.assertEqual(model.method, "regression_discontinuity")

    def test_run_causal_analysis_difference_in_differences(self):
        """Test run_causal_analysis with difference_in_differences method - line 633."""
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
            name="Test DiD",
            description="Test difference-in-differences",
            data=data,
            target_variable='outcome',
            treatment_variable='group'
        )

        model = self.service.run_causal_analysis(
            dataset_id=dataset.dataset_id,
            method="difference_in_differences",
            parameters={"time_variable": "time", "group_variable": "group"}
        )

        self.assertEqual(model.status, "completed")
        self.assertEqual(model.method, "difference_in_differences")

    def test_run_causal_analysis_exception(self):
        """Test run_causal_analysis exception handling - lines 659-661."""
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4],
            'treatment': [0, 1, 0, 1],
            'outcome': [10, 15, 12, 18]
        })

        dataset = self.service.create_dataset(
            name="Test",
            description="Test",
            data=data,
            target_variable='outcome',
            treatment_variable='treatment',
            features=['x1']
        )

        # Mock to raise exception
        with patch.object(self.service, 'propensity_score_matching', side_effect=Exception("Test exception")):
            model = self.service.run_causal_analysis(
                dataset_id=dataset.dataset_id,
                method="propensity_score_matching",
                parameters={"caliper": 0.1}
            )

            self.assertEqual(model.status, "failed")
            self.assertIn('error', model.results)

    def test_list_causal_models_with_dataset_id(self):
        """Test list_causal_models with dataset_id parameter - line 287."""
        # Create two datasets
        data1 = pd.DataFrame({
            'x1': [1, 2, 3],
            'treatment': [0, 1, 0],
            'outcome': [10, 15, 12]
        })
        dataset1 = self.service.create_dataset(
            name="Dataset 1",
            description="First dataset",
            data=data1,
            target_variable='outcome',
            treatment_variable='treatment'
        )

        data2 = pd.DataFrame({
            'x1': [4, 5, 6],
            'treatment': [1, 0, 1],
            'outcome': [20, 25, 22]
        })
        dataset2 = self.service.create_dataset(
            name="Dataset 2",
            description="Second dataset",
            data=data2,
            target_variable='outcome',
            treatment_variable='treatment'
        )

        # Create models for both datasets
        model1 = CausalModel(
            model_id="model_1",
            dataset_id=dataset1.dataset_id,
            method="propensity_score_matching",
            parameters={"caliper": 0.1},
            results={"treatment_effect": 1.0},
            created_at=datetime.now(),
            status="completed"
        )
        self.service.db.save_causal_model(model1)

        model2 = CausalModel(
            model_id="model_2",
            dataset_id=dataset2.dataset_id,
            method="propensity_score_matching",
            parameters={"caliper": 0.1},
            results={"treatment_effect": 2.0},
            created_at=datetime.now(),
            status="completed"
        )
        self.service.db.save_causal_model(model2)

        # List models for dataset1 only (line 287)
        models = self.service.db.list_causal_models(dataset_id=dataset1.dataset_id)
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].dataset_id, dataset1.dataset_id)

    def test_list_causal_models_exception_with_dataset_id(self):
        """Test list_causal_models exception handling with dataset_id - lines 312-314."""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database error")

            # Call with dataset_id to trigger the specific exception path
            result = self.service.db.list_causal_models(dataset_id="test_dataset")
            self.assertEqual(result, [])

    def test_instrumental_variable_exception(self):
        """Test instrumental_variable exception handling - lines 519-520."""
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4],
            'treatment': [0, 1, 0, 1],
            'outcome': [10, 15, 12, 18]
        })

        dataset = Dataset(
            dataset_id="test",
            name="Test",
            description="Test",
            features=['x1'],
            target_variable='outcome',
            treatment_variable='treatment',
            data=data,
            created_at=datetime.now(),
            metadata={}
        )

        # Try with non-existent instrument to trigger exception
        result = self.service.instrumental_variable(dataset, instrument='nonexistent')
        self.assertIn('error', result)

    def test_difference_in_differences_exception(self):
        """Test difference_in_differences exception handling - lines 600-601."""
        data = pd.DataFrame({
            'x1': [1, 2, 3, 4],
            'treatment': [0, 1, 0, 1],
            'outcome': [10, 15, 12, 18]
        })

        dataset = Dataset(
            dataset_id="test",
            name="Test",
            description="Test",
            features=['x1'],
            target_variable='outcome',
            treatment_variable='treatment',
            data=data,
            created_at=datetime.now(),
            metadata={}
        )

        # Try with non-existent variables to trigger exception
        result = self.service.difference_in_differences(
            dataset, time_variable='nonexistent', group_variable='nonexistent'
        )
        self.assertIn('error', result)

    def test_propensity_score_matching_exception_details(self):
        """Test propensity_score_matching exception handling - lines 475-476."""
        # Create invalid dataset that will cause exception
        data = pd.DataFrame({
            'treatment': [0, 1, 0],
            'outcome': [10, 15, 12]
        })

        dataset = Dataset(
            dataset_id="test",
            name="Test",
            description="Test",
            features=['nonexistent_feature'],  # Feature that doesn't exist
            target_variable='outcome',
            treatment_variable='treatment',
            data=data,
            created_at=datetime.now(),
            metadata={}
        )

        result = self.service.propensity_score_matching(dataset, caliper=0.1)
        self.assertIn('error', result)
        self.assertEqual(result['method'], 'propensity_score_matching')


class TestFlaskAPIAdditionalCoverage(unittest.TestCase):
    """Additional Flask API tests for coverage."""

    def setUp(self):
        """Set up Flask test client."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.service = CausalInferenceService(self.temp_db.name)

        # Set up Flask test client
        import ace_causal_inference_service as ace_service
        ace_service.ace_causal_inference_service = self.service
        app = ace_service.app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_list_datasets_exception_line_741(self):
        """Test list_datasets Flask endpoint exception - line 741."""
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
        self.client.post('/datasets', json=data)

        # Mock list_datasets to return a dataset with broken created_at that causes exception
        def mock_broken_list():
            from ace_causal_inference_service import Dataset
            import pandas as pd
            broken_dataset = Dataset(
                dataset_id="test",
                name="Test",
                description="Test",
                features=['x1'],
                target_variable='outcome',
                treatment_variable='treatment',
                data=pd.DataFrame({'x1': [1], 'outcome': [1], 'treatment': [0]}),
                created_at="not_a_datetime",  # This will cause error on .isoformat()
                metadata={}
            )
            return [broken_dataset]

        with patch.object(self.service.db, 'list_datasets', side_effect=mock_broken_list):
            import ace_causal_inference_service as ace_service
            ace_service.ace_causal_inference_service.db = self.service.db

            response = self.client.get('/datasets')

            # Should return 400 error
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_list_models_exception_line_834(self):
        """Test list_models Flask endpoint exception - line 834."""
        # Mock list_causal_models to raise exception directly
        with patch.object(self.service.db, 'list_causal_models', side_effect=Exception("Database error")):
            import ace_causal_inference_service as ace_service
            ace_service.ace_causal_inference_service.db = self.service.db

            response = self.client.get('/models')

            # Should return 400 error
            result = response.get_json()
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_list_models_for_loop_line_834(self):
        """Test list_models Flask endpoint to hit line 834 (for loop)."""
        # Create a dataset and model to ensure the for loop executes
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

        # Run analysis to create a model
        analysis_data = {
            'dataset_id': dataset_id,
            'method': 'propensity_score_matching',
            'parameters': {'caliper': 0.1}
        }
        self.client.post('/models', json=analysis_data)

        # List models - this should hit line 834 (the for loop)
        response = self.client.get('/models')
        self.assertEqual(response.status_code, 200)

        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertIn('models', result)
        self.assertGreater(len(result['models']), 0)


if __name__ == '__main__':
    unittest.main()
