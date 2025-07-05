# Shared Resources
*Common Tools, Libraries, and Best Practices*

## Overview
This directory contains shared resources, utilities, and best practices that can be used across all 10 projects to ensure consistency, quality, and professional standards.

## Resource Categories

### 1. Development Environment Setup
- Python environment management
- Package management with Poetry/pip
- IDE configuration (VS Code, PyCharm)
- Git workflows and best practices

### 2. Common Libraries and Utilities
- Data processing utilities
- Model evaluation frameworks
- Visualization templates
- API development patterns

### 3. Code Quality Standards
- Linting and formatting configurations
- Testing frameworks and patterns
- Documentation standards
- Security best practices

### 4. Project Templates
- Repository structure templates
- README templates
- Documentation templates
- Deployment configurations

## Directory Structure

```
shared-resources/
├── environment-setup/
│   ├── requirements/
│   ├── docker/
│   └── conda/
├── utilities/
│   ├── data-processing/
│   ├── model-evaluation/
│   ├── visualization/
│   └── api-helpers/
├── code-quality/
│   ├── linting/
│   ├── testing/
│   ├── documentation/
│   └── security/
├── templates/
│   ├── project-structure/
│   ├── readme-templates/
│   ├── api-documentation/
│   └── presentation/
└── best-practices/
    ├── ml-ops/
    ├── data-science/
    ├── software-engineering/
    └── deployment/
```

## Development Environment Setup

### Python Environment Management

#### Using Poetry (Recommended)
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Initialize new project
poetry init
poetry add streamlit pandas scikit-learn
poetry add pytest black flake8 --group dev

# Activate environment
poetry shell
```

#### Using Conda
```bash
# Create environment
conda create -n ai-portfolio python=3.9
conda activate ai-portfolio

# Install packages
conda install pandas numpy scikit-learn matplotlib seaborn
pip install streamlit fastapi uvicorn
```

#### Requirements Template
```txt
# requirements.txt
# Core ML/AI libraries
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
matplotlib==3.7.1
seaborn==0.12.2
plotly==5.15.0

# Deep Learning (choose one)
torch==2.0.1
# tensorflow==2.13.0

# NLP
transformers==4.30.2
# spacy==3.6.0

# Web frameworks
streamlit==1.25.0
fastapi==0.100.1
uvicorn==0.23.1

# Utilities
requests==2.31.0
python-dotenv==1.0.0
pydantic==2.0.3

# Development
pytest==7.4.0
black==23.7.0
flake8==6.0.0
mypy==1.4.1
```

### IDE Configuration

#### VS Code Settings (.vscode/settings.json)
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/venv": true,
        "**/.env": true
    }
}
```

## Common Utilities

### Data Processing Utilities

#### data_utils.py
```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Tuple, Optional

class DataProcessor:
    """Common data processing utilities for ML projects."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
    
    def load_and_clean_data(self, filepath: str) -> pd.DataFrame:
        """Load and perform basic cleaning on dataset."""
        df = pd.read_csv(filepath)
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
        
        categorical_columns = df.select_dtypes(include=['object']).columns
        df[categorical_columns] = df[categorical_columns].fillna(df[categorical_columns].mode().iloc[0])
        
        return df
    
    def split_features_target(self, df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Split dataframe into features and target."""
        X = df.drop(columns=[target_column])
        y = df[target_column]
        return X, y
    
    def encode_categorical_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features using label encoding."""
        X_encoded = X.copy()
        categorical_columns = X_encoded.select_dtypes(include=['object']).columns
        
        for column in categorical_columns:
            if column not in self.label_encoders:
                self.label_encoders[column] = LabelEncoder()
                X_encoded[column] = self.label_encoders[column].fit_transform(X_encoded[column])
            else:
                X_encoded[column] = self.label_encoders[column].transform(X_encoded[column])
        
        return X_encoded
    
    def scale_features(self, X: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Scale numerical features."""
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    
    def prepare_data(self, filepath: str, target_column: str, test_size: float = 0.2) -> Tuple:
        """Complete data preparation pipeline."""
        # Load and clean data
        df = self.load_and_clean_data(filepath)
        
        # Split features and target
        X, y = self.split_features_target(df, target_column)
        
        # Encode categorical features
        X_encoded = self.encode_categorical_features(X)
        
        # Scale features
        X_scaled = self.scale_features(X_encoded)
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )
        
        return X_train, X_test, y_train, y_test
```

### Model Evaluation Framework

#### evaluation_utils.py
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
from sklearn.model_selection import cross_val_score
import plotly.express as px
import plotly.graph_objects as go

class ModelEvaluator:
    """Comprehensive model evaluation utilities."""
    
    def __init__(self, model, X_test, y_test, X_train=None, y_train=None):
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.X_train = X_train
        self.y_train = y_train
        self.y_pred = model.predict(X_test)
        
        if hasattr(model, 'predict_proba'):
            self.y_pred_proba = model.predict_proba(X_test)[:, 1]
        else:
            self.y_pred_proba = None
    
    def classification_metrics(self) -> dict:
        """Calculate comprehensive classification metrics."""
        metrics = {
            'accuracy': accuracy_score(self.y_test, self.y_pred),
            'precision': precision_score(self.y_test, self.y_pred, average='weighted'),
            'recall': recall_score(self.y_test, self.y_pred, average='weighted'),
            'f1_score': f1_score(self.y_test, self.y_pred, average='weighted')
        }
        
        if self.y_pred_proba is not None:
            metrics['auc_roc'] = roc_auc_score(self.y_test, self.y_pred_proba)
        
        return metrics
    
    def plot_confusion_matrix(self, figsize=(8, 6)):
        """Create confusion matrix heatmap."""
        cm = confusion_matrix(self.y_test, self.y_pred)
        
        plt.figure(figsize=figsize)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.show()
    
    def plot_roc_curve(self, figsize=(8, 6)):
        """Plot ROC curve if probability predictions available."""
        if self.y_pred_proba is None:
            print("ROC curve requires probability predictions")
            return
        
        fpr, tpr, _ = roc_curve(self.y_test, self.y_pred_proba)
        auc_score = roc_auc_score(self.y_test, self.y_pred_proba)
        
        plt.figure(figsize=figsize)
        plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc_score:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend()
        plt.grid(True)
        plt.show()
    
    def cross_validation_scores(self, cv=5) -> dict:
        """Perform cross-validation evaluation."""
        if self.X_train is None or self.y_train is None:
            print("Cross-validation requires training data")
            return {}
        
        cv_scores = {
            'accuracy': cross_val_score(self.model, self.X_train, self.y_train, cv=cv, scoring='accuracy'),
            'precision': cross_val_score(self.model, self.X_train, self.y_train, cv=cv, scoring='precision_weighted'),
            'recall': cross_val_score(self.model, self.X_train, self.y_train, cv=cv, scoring='recall_weighted'),
            'f1': cross_val_score(self.model, self.X_train, self.y_train, cv=cv, scoring='f1_weighted')
        }
        
        return {metric: {'mean': scores.mean(), 'std': scores.std()} 
                for metric, scores in cv_scores.items()}
    
    def generate_report(self) -> str:
        """Generate comprehensive evaluation report."""
        metrics = self.classification_metrics()
        cv_scores = self.cross_validation_scores()
        
        report = f"""
        Model Evaluation Report
        =====================
        
        Test Set Metrics:
        - Accuracy: {metrics['accuracy']:.4f}
        - Precision: {metrics['precision']:.4f}
        - Recall: {metrics['recall']:.4f}
        - F1-Score: {metrics['f1_score']:.4f}
        """
        
        if 'auc_roc' in metrics:
            report += f"- AUC-ROC: {metrics['auc_roc']:.4f}\n"
        
        if cv_scores:
            report += f"\nCross-Validation Scores (5-fold):\n"
            for metric, scores in cv_scores.items():
                report += f"- {metric.capitalize()}: {scores['mean']:.4f} (+/- {scores['std']*2:.4f})\n"
        
        return report
```

### Visualization Templates

#### viz_utils.py
```python
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class Visualizer:
    """Common visualization utilities for AI projects."""
    
    def __init__(self, style='seaborn-v0_8', figsize=(10, 6)):
        plt.style.use(style)
        self.figsize = figsize
    
    def plot_feature_importance(self, feature_names, importance_scores, title="Feature Importance"):
        """Plot feature importance scores."""
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance_scores
        }).sort_values('importance', ascending=True)
        
        fig = px.bar(importance_df, x='importance', y='feature', 
                     title=title, orientation='h')
        fig.update_layout(height=max(400, len(feature_names) * 25))
        return fig
    
    def plot_training_history(self, history, metrics=['accuracy', 'loss']):
        """Plot training history for deep learning models."""
        fig = make_subplots(rows=1, cols=len(metrics), 
                           subplot_titles=metrics)
        
        for i, metric in enumerate(metrics, 1):
            fig.add_trace(
                go.Scatter(y=history[metric], name=f'Train {metric}'),
                row=1, col=i
            )
            if f'val_{metric}' in history:
                fig.add_trace(
                    go.Scatter(y=history[f'val_{metric}'], name=f'Val {metric}'),
                    row=1, col=i
                )
        
        fig.update_layout(title="Training History")
        return fig
    
    def plot_prediction_distribution(self, y_true, y_pred, title="Prediction vs Actual"):
        """Plot prediction distribution for regression problems."""
        fig = go.Figure()
        
        # Scatter plot
        fig.add_trace(go.Scatter(
            x=y_true, y=y_pred,
            mode='markers',
            name='Predictions',
            opacity=0.6
        ))
        
        # Perfect prediction line
        min_val = min(min(y_true), min(y_pred))
        max_val = max(max(y_true), max(y_pred))
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Perfect Prediction',
            line=dict(dash='dash', color='red')
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Actual Values',
            yaxis_title='Predicted Values'
        )
        
        return fig
```

## Code Quality Standards

### Linting Configuration

#### .flake8
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, E266, E501, W503, F403, F401
max-complexity = 18
select = B,C,E,F,W,T4,B9
```

#### pyproject.toml (for black)
```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

### Testing Framework

#### test_template.py
```python
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from src.data_utils import DataProcessor
from src.evaluation_utils import ModelEvaluator

class TestDataProcessor:
    """Test cases for DataProcessor class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample dataset for testing."""
        return pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': ['A', 'B', 'A', 'C', 'B'],
            'target': [0, 1, 0, 1, 1]
        })
    
    def test_load_and_clean_data(self, sample_data):
        """Test data loading and cleaning."""
        processor = DataProcessor()
        # Add your test logic here
        assert len(sample_data) == 5
    
    def test_split_features_target(self, sample_data):
        """Test feature-target splitting."""
        processor = DataProcessor()
        X, y = processor.split_features_target(sample_data, 'target')
        
        assert X.shape[1] == 2  # Two features
        assert len(y) == 5      # Five samples
        assert 'target' not in X.columns

class TestModelEvaluator:
    """Test cases for ModelEvaluator class."""
    
    @pytest.fixture
    def mock_model(self):
        """Create mock model for testing."""
        model = Mock()
        model.predict.return_value = np.array([0, 1, 0, 1, 1])
        model.predict_proba.return_value = np.array([[0.8, 0.2], [0.3, 0.7], [0.9, 0.1], [0.4, 0.6], [0.2, 0.8]])
        return model
    
    def test_classification_metrics(self, mock_model):
        """Test classification metrics calculation."""
        X_test = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
        y_test = np.array([0, 1, 0, 1, 1])
        
        evaluator = ModelEvaluator(mock_model, X_test, y_test)
        metrics = evaluator.classification_metrics()
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 'auc_roc' in metrics
```

This shared resources structure ensures consistency, quality, and professionalism across all 10 portfolio projects.