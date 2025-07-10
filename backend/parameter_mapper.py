"""Parameter mapping module for translating sentiment scores to visual parameters."""

from typing import Dict, List, Tuple, Optional
import numpy as np


class ParameterMapper:
    """Maps sentiment analysis scores to visual generation parameters."""
    
    def __init__(self):
        """Initialize the parameter mapper."""
        pass
    
    def get_all_parameters(self, sentiment_scores: Dict[str, float]) -> Dict[str, any]:
        """Get all visual parameters from sentiment scores.
        
        Args:
            sentiment_scores: Dictionary of sentiment dimension scores
            
        Returns:
            Dictionary of visual parameters for the art generator
        """
        # Validate and clamp scores
        validated_scores = {}
        for key in ["positiveness", "energy", "complexity", "conflictness"]:
            score = sentiment_scores.get(key, 0.5)
            validated_scores[key] = max(0.0, min(1.0, score))
        
        return {
            "sentiment_scores": validated_scores,
            "description": self.create_style_description(validated_scores)
        }
    
    def create_style_description(self, sentiment_scores: Dict[str, float]) -> str:
        """Generate a human-readable description of the visual style.
        
        Args:
            sentiment_scores: Dictionary of sentiment dimension scores
            
        Returns:
            String description of the visual style
        """
        descriptions = []
        
        # Temperature description
        positiveness = sentiment_scores.get("positiveness", 0.5)
        if positiveness > 0.7:
            descriptions.append("warm and inviting")
        elif positiveness < 0.3:
            descriptions.append("cool and contemplative")
        else:
            descriptions.append("neutral-toned")
        
        # Energy description
        energy = sentiment_scores.get("energy", 0.5)
        if energy > 0.7:
            descriptions.append("dynamic and turbulent")
        elif energy < 0.3:
            descriptions.append("calm and flowing")
        else:
            descriptions.append("moderately energetic")
        
        # Complexity description
        complexity = sentiment_scores.get("complexity", 0.5)
        if complexity > 0.8:
            descriptions.append("with intricate reaction-diffusion patterns")
        elif complexity > 0.6:
            descriptions.append("featuring cellular structures")
        elif complexity > 0.4:
            descriptions.append("with fractal noise patterns")
        elif complexity > 0.2:
            descriptions.append("using smooth Perlin noise")
        else:
            descriptions.append("with simple gradients")
        
        # Conflictness description
        conflictness = sentiment_scores.get("conflictness", 0.5)
        if conflictness > 0.7:
            descriptions.append("and highly varied, conflicting colors")
        elif conflictness > 0.3:
            descriptions.append("with some color variation")
        else:
            descriptions.append("in a unified color scheme")
        
        return "A " + ", ".join(descriptions) + " composition"


if __name__ == "__main__":
    # Test the mapper
    mapper = ParameterMapper()
    
    test_scores = [
        {
            "name": "Warm Calm Simple",
            "scores": {"positiveness": 0.8, "energy": 0.2, "complexity": 0.1, "conflictness": 0.1}
        },
        {
            "name": "Cold Chaotic Complex",
            "scores": {"positiveness": 0.1, "energy": 0.9, "complexity": 0.9, "conflictness": 0.8}
        },
        {
            "name": "Neutral Conflicted",
            "scores": {"positiveness": 0.5, "energy": 0.5, "complexity": 0.5, "conflictness": 0.9}
        }
    ]
    
    for test in test_scores:
        print(f"\n{test['name']}:")
        params = mapper.get_all_parameters(test['scores'])
        print(f"Description: {params['description']}")
        print("Scores:", params['sentiment_scores']) 