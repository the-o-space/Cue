"""Sentiment analysis module using Claude API."""

import json
from typing import Dict, Optional
from anthropic import Anthropic
from config import (
    ANTHROPIC_API_KEY,
    MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE,
    SENTIMENT_DIMENSIONS,
    SENTIMENT_PROMPT_TEMPLATE
)


class SentimentAnalyzer:
    """Analyzes text sentiment across multiple dimensions using Claude API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the sentiment analyzer.
        
        Args:
            api_key: Anthropic API key. If not provided, uses config value.
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY in .env file.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.dimensions = SENTIMENT_DIMENSIONS
    
    def analyze(self, text: str, dimensions: Optional[list] = None) -> Dict[str, float]:
        """Analyze text sentiment across specified dimensions.
        
        Args:
            text: Text to analyze
            dimensions: List of dimensions to analyze. Uses default if not provided.
            
        Returns:
            Dictionary mapping dimension names to scores (0.0 to 1.0)
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Use provided dimensions or default
        dims = dimensions or self.dimensions
        
        # Create prompt
        prompt = SENTIMENT_PROMPT_TEMPLATE.format(text=text)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract JSON from response
            result_text = response.content[0].text.strip()
            
            # Parse JSON
            scores = json.loads(result_text)
            
            # Validate scores
            validated_scores = {}
            for dim in dims:
                if dim in scores:
                    score = float(scores[dim])
                    # Clamp to 0-1 range
                    validated_scores[dim] = max(0.0, min(1.0, score))
                else:
                    # Default to 0.5 if dimension missing
                    validated_scores[dim] = 0.5
            
            return validated_scores
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Claude response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Error calling Claude API: {e}")
    
    def analyze_batch(self, texts: list[str]) -> list[Dict[str, float]]:
        """Analyze multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of dictionaries with sentiment scores for each text
        """
        results = []
        for text in texts:
            try:
                scores = self.analyze(text)
                results.append(scores)
            except Exception as e:
                print(f"Error analyzing text: {e}")
                # Return neutral scores on error
                results.append({dim: 0.5 for dim in self.dimensions})
        
        return results


if __name__ == "__main__":
    # Test the analyzer
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "The sun blazed overhead, a furious orb of molten gold that scorched the earth below!",
        "She walked quietly through the morning mist.",
        "Chaos erupted as colors exploded across the canvas in a magnificent dance of creation!"
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        try:
            scores = analyzer.analyze(text)
            print("Scores:")
            for dim, score in scores.items():
                print(f"  {dim}: {score:.2f}")
        except Exception as e:
            print(f"Error: {e}") 