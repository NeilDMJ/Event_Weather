"""
Functional Climate Predictor
A functional approach to climate prediction with simplified ML models.
"""

import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FunctionalClimatePredictor:
    """
    A functional climate predictor that provides simplified prediction capabilities.
    This serves as a fallback or alternative to the enhanced database-backed predictor.
    """
    
    def __init__(self, models_dir: str = "/app/models/trained"):
        """
        Initialize the functional climate predictor.
        
        Args:
            models_dir: Directory containing the trained models
        """
        self.models_dir = Path(models_dir)
        self.models = {}
        self.model_info = {}
        self.load_available_models()
    
    def load_available_models(self):
        """Load all available models from the models directory."""
        try:
            if not self.models_dir.exists():
                logger.warning(f"Models directory {self.models_dir} does not exist")
                return
            
            # Find all .joblib files
            model_files = list(self.models_dir.glob("*.joblib"))
            
            for model_file in model_files:
                try:
                    # Extract variable and timestamp from filename
                    filename = model_file.stem
                    if filename.startswith("model_"):
                        parts = filename.split("_")
                        if len(parts) >= 4:
                            variable = "_".join(parts[1:-2])  # Everything between "model_" and timestamp
                            timestamp = "_".join(parts[-2:])
                            
                            # Load the model
                            model = joblib.load(model_file)
                            model_key = f"{variable}_{timestamp}"
                            self.models[model_key] = model
                            
                            # Try to load corresponding model info
                            info_file = self.models_dir / f"model_info_{variable}_{timestamp}.txt"
                            if info_file.exists():
                                with open(info_file, 'r') as f:
                                    self.model_info[model_key] = f.read()
                            
                            logger.info(f"Loaded model: {model_key}")
                
                except Exception as e:
                    logger.error(f"Error loading model {model_file}: {e}")
            
            logger.info(f"Loaded {len(self.models)} models successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def get_available_variables(self) -> List[str]:
        """Get list of available climate variables."""
        variables = set()
        for model_key in self.models.keys():
            # Extract variable name (everything before the last two underscore-separated parts)
            parts = model_key.split("_")
            if len(parts) >= 3:
                variable = "_".join(parts[:-2])
                variables.add(variable)
        return list(variables)
    
    def get_latest_model_for_variable(self, variable: str) -> Optional[Any]:
        """Get the latest model for a specific variable."""
        matching_models = [key for key in self.models.keys() if key.startswith(f"{variable}_")]
        
        if not matching_models:
            return None
        
        # Sort by timestamp (assuming format is consistent)
        latest_model_key = sorted(matching_models)[-1]
        return self.models[latest_model_key]
    
    def predict_single_variable(self, variable: str, features: Dict[str, float]) -> Optional[float]:
        """
        Predict a single climate variable.
        
        Args:
            variable: Climate variable to predict
            features: Input features for prediction
            
        Returns:
            Predicted value or None if prediction fails
        """
        try:
            model = self.get_latest_model_for_variable(variable)
            if model is None:
                logger.warning(f"No model found for variable: {variable}")
                return None
            
            # Create feature array - this is a simplified approach
            # In a real implementation, you'd need to ensure feature order matches training
            feature_values = list(features.values())
            
            if not feature_values:
                logger.warning("No features provided for prediction")
                return None
            
            # Make prediction
            prediction = model.predict([feature_values])[0]
            return float(prediction)
            
        except Exception as e:
            logger.error(f"Error predicting {variable}: {e}")
            return None
    
    def predict_all_variables(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Predict all available climate variables.
        
        Args:
            features: Input features for prediction
            
        Returns:
            Dictionary of predictions for each variable
        """
        predictions = {}
        
        for variable in self.get_available_variables():
            prediction = self.predict_single_variable(variable, features)
            if prediction is not None:
                predictions[variable] = prediction
        
        return predictions
    
    def predict(self, 
                latitude: float, 
                longitude: float, 
                **kwargs) -> Dict[str, Any]:
        """
        Main prediction method.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            **kwargs: Additional parameters
            
        Returns:
            Prediction results
        """
        try:
            # Create basic features from coordinates
            features = {
                'latitude': latitude,
                'longitude': longitude,
                'lat_squared': latitude ** 2,
                'lon_squared': longitude ** 2,
                'lat_lon_interaction': latitude * longitude
            }
            
            # Add any additional features from kwargs
            features.update(kwargs)
            
            # Get predictions for all variables
            predictions = self.predict_all_variables(features)
            
            # Format results
            result = {
                'success': True,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'predictions': predictions,
                'model_type': 'functional',
                'models_used': len(predictions)
            }
            
            logger.info(f"Functional prediction completed for ({latitude}, {longitude})")
            return result
            
        except Exception as e:
            logger.error(f"Error in functional prediction: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_type': 'functional'
            }
    
    def get_model_info(self, variable: str) -> Optional[str]:
        """Get information about a specific model."""
        matching_keys = [key for key in self.model_info.keys() if key.startswith(f"{variable}_")]
        if matching_keys:
            latest_key = sorted(matching_keys)[-1]
            return self.model_info[latest_key]
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the predictor."""
        return {
            'status': 'healthy',
            'models_loaded': len(self.models),
            'variables_available': self.get_available_variables(),
            'predictor_type': 'functional'
        }


# Convenience function for direct usage
def create_functional_predictor(models_dir: str = "/app/models/trained") -> FunctionalClimatePredictor:
    """Create and return a functional climate predictor instance."""
    return FunctionalClimatePredictor(models_dir)


# For backward compatibility
def predict_climate(latitude: float, 
                   longitude: float, 
                   models_dir: str = "/app/models/trained") -> Dict[str, Any]:
    """
    Standalone function for climate prediction.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        models_dir: Directory containing trained models
        
    Returns:
        Prediction results
    """
    predictor = create_functional_predictor(models_dir)
    return predictor.predict(latitude, longitude)