# ACE Causal Inference Service PRD

## Overview
Build a comprehensive causal inference service that implements multiple methods for estimating causal effects from observational data, including propensity score matching, instrumental variables, regression discontinuity design, and difference-in-differences.

## Core Functionality

### 1. Dataset Management
- Create and store datasets with treatment and outcome variables
- Support multiple feature types and data formats
- Metadata tracking for analysis reproducibility

### 2. Causal Inference Methods
Implement four primary causal inference techniques:

#### Propensity Score Matching
- Calculate propensity scores using logistic regression
- Match treated and control units within specified caliper
- Compute average treatment effect on treated (ATT)

#### Instrumental Variables (IV)
- Two-stage least squares estimation
- First stage: predict treatment using instrument
- Second stage: estimate causal effect using predicted treatment

#### Regression Discontinuity Design (RDD)
- Identify treatment discontinuities at cutoff points
- Estimate local average treatment effect (LATE)
- Support both sharp and fuzzy designs

#### Difference-in-Differences (DiD)
- Compare treatment and control groups over time
- Control for time-invariant confounders
- Estimate parallel trends assumption

### 3. Statistical Inference
For each method, provide:
- Point estimates of treatment effects
- Standard errors
- Confidence intervals
- P-values
- Model diagnostics and fit statistics

### 4. Model Management
- Save and retrieve causal models
- Track analysis parameters and results
- Support model comparison and validation

### 5. REST API
Flask-based API with endpoints for:
- `/health` - Health check
- `/datasets` - Create and list datasets
- `/datasets/<id>` - Get specific dataset
- `/models` - Run analysis and list models
- `/models/<id>` - Get model results
- `/methods` - List available methods
- `/effects/<model_id>` - Get treatment effects

## Technical Requirements

### Data Storage
- SQLite database for persistence
- Support for pandas DataFrames
- JSON serialization for complex objects

### Statistical Computing
- NumPy for numerical operations
- scikit-learn for machine learning models
- Pandas for data manipulation

### API Framework
- Flask for REST API
- JSON request/response format
- Error handling and validation

## Quality Requirements

### Testing
- Unit tests for all core functions
- Integration tests for API endpoints
- Edge case and error handling tests
- **Target: 95%+ code coverage**

### Performance
- Handle datasets with 1000+ observations
- Analysis completion within 10 seconds
- Efficient memory usage

### Robustness
- Graceful error handling
- Input validation
- Database transaction safety

## Success Metrics
- All four causal methods implemented and tested
- 95%+ test coverage achieved
- API functional with proper error handling
- Documentation complete
