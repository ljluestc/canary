#!/usr/bin/env python3
"""
ACE Causal Inference Service

A comprehensive system for causal inference analysis using various methods
including propensity score matching, instrumental variables, and regression
discontinuity design.
"""

import os
import sys
import json
import sqlite3
import tempfile
import numpy as np
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any
from flask import Flask, request, jsonify
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class Dataset:
    """Dataset for causal inference analysis."""
    dataset_id: str
    name: str
    description: str
    features: List[str]
    target_variable: str
    treatment_variable: str
    data: pd.DataFrame
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class CausalModel:
    """Causal inference model."""
    model_id: str
    dataset_id: str
    method: str  # 'propensity_score', 'instrumental_variable', 'regression_discontinuity', 'difference_in_differences'
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    created_at: datetime
    status: str  # 'pending', 'running', 'completed', 'failed'

@dataclass
class TreatmentEffect:
    """Treatment effect estimation."""
    effect_id: str
    model_id: str
    treatment_effect: float
    confidence_interval: Tuple[float, float]
    p_value: float
    standard_error: float
    method: str
    created_at: datetime

class CausalInferenceDatabase:
    """Database for storing causal inference data."""
    
    def __init__(self, db_path: str):
        """Initialize database."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create datasets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                features TEXT,
                target_variable TEXT,
                treatment_variable TEXT,
                data TEXT,
                created_at TEXT,
                metadata TEXT
            )
        ''')
        
        # Create causal_models table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS causal_models (
                model_id TEXT PRIMARY KEY,
                dataset_id TEXT,
                method TEXT,
                parameters TEXT,
                results TEXT,
                created_at TEXT,
                status TEXT,
                FOREIGN KEY (dataset_id) REFERENCES datasets (dataset_id)
            )
        ''')
        
        # Create treatment_effects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS treatment_effects (
                effect_id TEXT PRIMARY KEY,
                model_id TEXT,
                treatment_effect REAL,
                confidence_interval_lower REAL,
                confidence_interval_upper REAL,
                p_value REAL,
                standard_error REAL,
                method TEXT,
                created_at TEXT,
                FOREIGN KEY (model_id) REFERENCES causal_models (model_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_dataset(self, dataset: Dataset) -> bool:
        """Save dataset to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO datasets 
                (dataset_id, name, description, features, target_variable, treatment_variable, 
                 data, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset.dataset_id,
                dataset.name,
                dataset.description,
                json.dumps(dataset.features),
                dataset.target_variable,
                dataset.treatment_variable,
                dataset.data.to_json(),
                dataset.created_at.isoformat(),
                json.dumps(dataset.metadata)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving dataset: {e}")
            return False
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT dataset_id, name, description, features, target_variable, 
                       treatment_variable, data, created_at, metadata
                FROM datasets WHERE dataset_id = ?
            ''', (dataset_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Dataset(
                    dataset_id=row[0],
                    name=row[1],
                    description=row[2],
                    features=json.loads(row[3]),
                    target_variable=row[4],
                    treatment_variable=row[5],
                    data=pd.read_json(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    metadata=json.loads(row[8])
                )
            return None
        except Exception as e:
            print(f"Error getting dataset: {e}")
            return None
    
    def list_datasets(self) -> List[Dataset]:
        """List all datasets."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT dataset_id, name, description, features, target_variable, 
                       treatment_variable, data, created_at, metadata
                FROM datasets ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            datasets = []
            for row in rows:
                datasets.append(Dataset(
                    dataset_id=row[0],
                    name=row[1],
                    description=row[2],
                    features=json.loads(row[3]),
                    target_variable=row[4],
                    treatment_variable=row[5],
                    data=pd.read_json(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    metadata=json.loads(row[8])
                ))
            return datasets
        except Exception as e:
            print(f"Error listing datasets: {e}")
            return []
    
    def save_causal_model(self, model: CausalModel) -> bool:
        """Save causal model to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO causal_models 
                (model_id, dataset_id, method, parameters, results, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                model.model_id,
                model.dataset_id,
                model.method,
                json.dumps(model.parameters),
                json.dumps(model.results),
                model.created_at.isoformat(),
                model.status
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving causal model: {e}")
            return False
    
    def get_causal_model(self, model_id: str) -> Optional[CausalModel]:
        """Get causal model by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT model_id, dataset_id, method, parameters, results, created_at, status
                FROM causal_models WHERE model_id = ?
            ''', (model_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return CausalModel(
                    model_id=row[0],
                    dataset_id=row[1],
                    method=row[2],
                    parameters=json.loads(row[3]),
                    results=json.loads(row[4]),
                    created_at=datetime.fromisoformat(row[5]),
                    status=row[6]
                )
            return None
        except Exception as e:
            print(f"Error getting causal model: {e}")
            return None
    
    def list_causal_models(self, dataset_id: Optional[str] = None) -> List[CausalModel]:
        """List causal models."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if dataset_id:
                cursor.execute('''
                    SELECT model_id, dataset_id, method, parameters, results, created_at, status
                    FROM causal_models WHERE dataset_id = ? ORDER BY created_at DESC
                ''', (dataset_id,))
            else:
                cursor.execute('''
                    SELECT model_id, dataset_id, method, parameters, results, created_at, status
                    FROM causal_models ORDER BY created_at DESC
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            models = []
            for row in rows:
                models.append(CausalModel(
                    model_id=row[0],
                    dataset_id=row[1],
                    method=row[2],
                    parameters=json.loads(row[3]),
                    results=json.loads(row[4]),
                    created_at=datetime.fromisoformat(row[5]),
                    status=row[6]
                ))
            return models
        except Exception as e:
            print(f"Error listing causal models: {e}")
            return []
    
    def save_treatment_effect(self, effect: TreatmentEffect) -> bool:
        """Save treatment effect to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO treatment_effects 
                (effect_id, model_id, treatment_effect, confidence_interval_lower, 
                 confidence_interval_upper, p_value, standard_error, method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                effect.effect_id,
                effect.model_id,
                effect.treatment_effect,
                effect.confidence_interval[0],
                effect.confidence_interval[1],
                effect.p_value,
                effect.standard_error,
                effect.method,
                effect.created_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving treatment effect: {e}")
            return False
    
    def get_treatment_effects(self, model_id: str) -> List[TreatmentEffect]:
        """Get treatment effects for a model."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT effect_id, model_id, treatment_effect, confidence_interval_lower,
                       confidence_interval_upper, p_value, standard_error, method, created_at
                FROM treatment_effects WHERE model_id = ? ORDER BY created_at DESC
            ''', (model_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            effects = []
            for row in rows:
                effects.append(TreatmentEffect(
                    effect_id=row[0],
                    model_id=row[1],
                    treatment_effect=row[2],
                    confidence_interval=(row[3], row[4]),
                    p_value=row[5],
                    standard_error=row[6],
                    method=row[7],
                    created_at=datetime.fromisoformat(row[8])
                ))
            return effects
        except Exception as e:
            print(f"Error getting treatment effects: {e}")
            return []

class CausalInferenceService:
    """Causal inference analysis service."""
    
    def __init__(self, db_path: str = "ace_causal_inference.db"):
        """Initialize service."""
        self.db = CausalInferenceDatabase(db_path)
    
    def generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{int(datetime.now().timestamp() * 1000)}"
    
    def create_dataset(self, name: str, description: str, data: pd.DataFrame, 
                      target_variable: str, treatment_variable: str, 
                      features: Optional[List[str]] = None) -> Dataset:
        """Create a new dataset."""
        if features is None:
            features = [col for col in data.columns if col not in [target_variable, treatment_variable]]
        
        dataset = Dataset(
            dataset_id=self.generate_id("dataset"),
            name=name,
            description=description,
            features=features,
            target_variable=target_variable,
            treatment_variable=treatment_variable,
            data=data,
            created_at=datetime.now(),
            metadata={"n_samples": len(data), "n_features": len(features)}
        )
        
        self.db.save_dataset(dataset)
        return dataset
    
    def propensity_score_matching(self, dataset: Dataset, 
                                 caliper: float = 0.1) -> Dict[str, Any]:
        """Perform propensity score matching."""
        try:
            data = dataset.data.copy()
            
            # Prepare features for propensity score model
            X = data[dataset.features]
            y = data[dataset.treatment_variable]
            
            # Fit propensity score model
            ps_model = LogisticRegression(random_state=42)
            ps_model.fit(X, y)
            propensity_scores = ps_model.predict_proba(X)[:, 1]
            
            # Add propensity scores to data
            data['propensity_score'] = propensity_scores
            
            # Perform matching
            treated = data[data[dataset.treatment_variable] == 1]
            control = data[data[dataset.treatment_variable] == 0]
            
            matched_pairs = []
            for _, treated_row in treated.iterrows():
                # Find closest control unit within caliper
                distances = np.abs(control['propensity_score'] - treated_row['propensity_score'])
                min_distance = distances.min()
                
                if min_distance <= caliper:
                    closest_control_idx = distances.idxmin()
                    matched_pairs.append((treated_row.name, closest_control_idx))
            
            # Calculate treatment effect
            if matched_pairs:
                treated_outcomes = []
                control_outcomes = []
                
                for treated_idx, control_idx in matched_pairs:
                    treated_outcomes.append(data.loc[treated_idx, dataset.target_variable])
                    control_outcomes.append(data.loc[control_idx, dataset.target_variable])
                
                treatment_effect = np.mean(treated_outcomes) - np.mean(control_outcomes)
                
                # Calculate standard error (simplified)
                n_pairs = len(matched_pairs)
                se = np.sqrt(np.var(treated_outcomes) / n_pairs + np.var(control_outcomes) / n_pairs)
                
                return {
                    "method": "propensity_score_matching",
                    "treatment_effect": float(treatment_effect),
                    "standard_error": float(se),
                    "n_matched_pairs": len(matched_pairs),
                    "caliper": caliper,
                    "propensity_scores": propensity_scores.tolist()
                }
            else:
                return {
                    "method": "propensity_score_matching",
                    "treatment_effect": 0.0,
                    "standard_error": 0.0,
                    "n_matched_pairs": 0,
                    "caliper": caliper,
                    "error": "No matches found within caliper"
                }
        except Exception as e:
            return {
                "method": "propensity_score_matching",
                "error": str(e)
            }
    
    def instrumental_variable(self, dataset: Dataset, 
                            instrument: str) -> Dict[str, Any]:
        """Perform instrumental variable analysis."""
        try:
            data = dataset.data.copy()
            
            # Two-stage least squares
            # First stage: regress treatment on instrument
            X_first = data[[instrument] + dataset.features]
            y_first = data[dataset.treatment_variable]
            
            first_stage = LinearRegression()
            first_stage.fit(X_first, y_first)
            predicted_treatment = first_stage.predict(X_first)
            
            # Second stage: regress outcome on predicted treatment
            X_second = np.column_stack([predicted_treatment, data[dataset.features]])
            y_second = data[dataset.target_variable]
            
            second_stage = LinearRegression()
            second_stage.fit(X_second, y_second)
            
            # Calculate treatment effect and standard error
            treatment_effect = second_stage.coef_[0]
            
            # Simplified standard error calculation
            residuals = y_second - second_stage.predict(X_second)
            mse = np.mean(residuals ** 2)
            se = np.sqrt(mse / len(data))
            
            return {
                "method": "instrumental_variable",
                "treatment_effect": float(treatment_effect),
                "standard_error": float(se),
                "instrument": instrument,
                "first_stage_r2": first_stage.score(X_first, y_first),
                "second_stage_r2": second_stage.score(X_second, y_second)
            }
        except Exception as e:
            return {
                "method": "instrumental_variable",
                "error": str(e)
            }
    
    def regression_discontinuity(self, dataset: Dataset, 
                               running_variable: str, 
                               cutoff: float) -> Dict[str, Any]:
        """Perform regression discontinuity analysis."""
        try:
            data = dataset.data.copy()
            
            # Create treatment indicator based on cutoff
            data['above_cutoff'] = (data[running_variable] >= cutoff).astype(int)
            
            # Create interaction term
            data['running_treatment'] = data[running_variable] * data['above_cutoff']
            
            # Fit regression model
            X = data[[running_variable, 'above_cutoff', 'running_treatment'] + dataset.features]
            y = data[dataset.target_variable]
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Treatment effect is the coefficient of above_cutoff
            treatment_effect = model.coef_[1]
            
            # Calculate standard error (simplified)
            residuals = y - model.predict(X)
            mse = np.mean(residuals ** 2)
            se = np.sqrt(mse / len(data))
            
            return {
                "method": "regression_discontinuity",
                "treatment_effect": float(treatment_effect),
                "standard_error": float(se),
                "running_variable": running_variable,
                "cutoff": cutoff,
                "r2": model.score(X, y)
            }
        except Exception as e:
            return {
                "method": "regression_discontinuity",
                "error": str(e)
            }
    
    def difference_in_differences(self, dataset: Dataset, 
                                 time_variable: str, 
                                 group_variable: str) -> Dict[str, Any]:
        """Perform difference-in-differences analysis."""
        try:
            data = dataset.data.copy()
            
            # Create interaction term
            data['time_group'] = data[time_variable] * data[group_variable]
            
            # Fit regression model
            X = data[[time_variable, group_variable, 'time_group'] + dataset.features]
            y = data[dataset.target_variable]
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Treatment effect is the coefficient of time_group
            treatment_effect = model.coef_[2]
            
            # Calculate standard error (simplified)
            residuals = y - model.predict(X)
            mse = np.mean(residuals ** 2)
            se = np.sqrt(mse / len(data))
            
            return {
                "method": "difference_in_differences",
                "treatment_effect": float(treatment_effect),
                "standard_error": float(se),
                "time_variable": time_variable,
                "group_variable": group_variable,
                "r2": model.score(X, y)
            }
        except Exception as e:
            return {
                "method": "difference_in_differences",
                "error": str(e)
            }
    
    def run_causal_analysis(self, dataset_id: str, method: str, 
                           parameters: Dict[str, Any]) -> CausalModel:
        """Run causal analysis on a dataset."""
        dataset = self.db.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        model = CausalModel(
            model_id=self.generate_id("model"),
            dataset_id=dataset_id,
            method=method,
            parameters=parameters,
            results={},
            created_at=datetime.now(),
            status="running"
        )
        
        self.db.save_causal_model(model)
        
        try:
            if method == "propensity_score_matching":
                results = self.propensity_score_matching(dataset, **parameters)
            elif method == "instrumental_variable":
                results = self.instrumental_variable(dataset, **parameters)
            elif method == "regression_discontinuity":
                results = self.regression_discontinuity(dataset, **parameters)
            elif method == "difference_in_differences":
                results = self.difference_in_differences(dataset, **parameters)
            else:
                results = {"error": f"Unknown method: {method}"}
                model.status = "failed"
            
            model.results = results
            if "error" not in results:
                model.status = "completed"
            
            # Save treatment effect if successful
            if "treatment_effect" in results and "error" not in results:
                effect = TreatmentEffect(
                    effect_id=self.generate_id("effect"),
                    model_id=model.model_id,
                    treatment_effect=results["treatment_effect"],
                    confidence_interval=(
                        results["treatment_effect"] - 1.96 * results.get("standard_error", 0),
                        results["treatment_effect"] + 1.96 * results.get("standard_error", 0)
                    ),
                    p_value=0.05,  # Simplified
                    standard_error=results.get("standard_error", 0),
                    method=method,
                    created_at=datetime.now()
                )
                self.db.save_treatment_effect(effect)
            
        except Exception as e:
            model.results = {"error": str(e)}
            model.status = "failed"
        
        self.db.save_causal_model(model)
        return model
    
    def get_model_results(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a causal model."""
        model = self.db.get_causal_model(model_id)
        if model:
            return model.results
        return None
    
    def list_available_methods(self) -> List[Dict[str, str]]:
        """List available causal inference methods."""
        return [
            {
                "method": "propensity_score_matching",
                "description": "Match treated and control units based on propensity scores",
                "parameters": ["caliper"]
            },
            {
                "method": "instrumental_variable",
                "description": "Use instrumental variables to estimate causal effects",
                "parameters": ["instrument"]
            },
            {
                "method": "regression_discontinuity",
                "description": "Exploit discontinuities in treatment assignment",
                "parameters": ["running_variable", "cutoff"]
            },
            {
                "method": "difference_in_differences",
                "description": "Compare changes over time between treatment and control groups",
                "parameters": ["time_variable", "group_variable"]
            }
        ]

# Flask application
app = Flask(__name__)
ace_causal_inference_service = CausalInferenceService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "ace_causal_inference"})

@app.route('/datasets', methods=['POST'])
def create_dataset():
    """Create a new dataset."""
    try:
        data = request.get_json()
        
        # Convert data to DataFrame
        df = pd.DataFrame(data['data'])
        
        dataset = ace_causal_inference_service.create_dataset(
            name=data['name'],
            description=data['description'],
            data=df,
            target_variable=data['target_variable'],
            treatment_variable=data['treatment_variable'],
            features=data.get('features')
        )
        
        return jsonify({
            "success": True,
            "dataset_id": dataset.dataset_id,
            "message": "Dataset created successfully"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/datasets', methods=['GET'])
def list_datasets():
    """List all datasets."""
    try:
        datasets = ace_causal_inference_service.db.list_datasets()
        
        result = []
        for dataset in datasets:
            result.append({
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "description": dataset.description,
                "features": dataset.features,
                "target_variable": dataset.target_variable,
                "treatment_variable": dataset.treatment_variable,
                "created_at": dataset.created_at.isoformat(),
                "metadata": dataset.metadata
            })
        
        return jsonify({"success": True, "datasets": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/datasets/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """Get dataset by ID."""
    try:
        dataset = ace_causal_inference_service.db.get_dataset(dataset_id)
        if not dataset:
            return jsonify({"success": False, "error": "Dataset not found"}), 404
        
        return jsonify({
            "success": True,
            "dataset": {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "description": dataset.description,
                "features": dataset.features,
                "target_variable": dataset.target_variable,
                "treatment_variable": dataset.treatment_variable,
                "data": dataset.data.to_dict('records'),
                "created_at": dataset.created_at.isoformat(),
                "metadata": dataset.metadata
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/models', methods=['POST'])
def run_analysis():
    """Run causal analysis."""
    try:
        data = request.get_json()
        
        model = ace_causal_inference_service.run_causal_analysis(
            dataset_id=data['dataset_id'],
            method=data['method'],
            parameters=data.get('parameters', {})
        )
        
        return jsonify({
            "success": True,
            "model_id": model.model_id,
            "status": model.status,
            "message": "Analysis started"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/models/<model_id>', methods=['GET'])
def get_model_results(model_id):
    """Get model results."""
    try:
        model = ace_causal_inference_service.db.get_causal_model(model_id)
        if not model:
            return jsonify({"success": False, "error": "Model not found"}), 404
        
        return jsonify({
            "success": True,
            "model": {
                "model_id": model.model_id,
                "dataset_id": model.dataset_id,
                "method": model.method,
                "parameters": model.parameters,
                "results": model.results,
                "status": model.status,
                "created_at": model.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/models', methods=['GET'])
def list_models():
    """List all models."""
    try:
        dataset_id = request.args.get('dataset_id')
        models = ace_causal_inference_service.db.list_causal_models(dataset_id)
        
        result = []
        for model in models:
            result.append({
                "model_id": model.model_id,
                "dataset_id": model.dataset_id,
                "method": model.method,
                "status": model.status,
                "created_at": model.created_at.isoformat()
            })
        
        return jsonify({"success": True, "models": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/methods', methods=['GET'])
def list_methods():
    """List available methods."""
    try:
        methods = ace_causal_inference_service.list_available_methods()
        return jsonify({"success": True, "methods": methods})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/effects/<model_id>', methods=['GET'])
def get_treatment_effects(model_id):
    """Get treatment effects for a model."""
    try:
        effects = ace_causal_inference_service.db.get_treatment_effects(model_id)
        
        result = []
        for effect in effects:
            result.append({
                "effect_id": effect.effect_id,
                "model_id": effect.model_id,
                "treatment_effect": effect.treatment_effect,
                "confidence_interval": effect.confidence_interval,
                "p_value": effect.p_value,
                "standard_error": effect.standard_error,
                "method": effect.method,
                "created_at": effect.created_at.isoformat()
            })
        
        return jsonify({"success": True, "effects": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
