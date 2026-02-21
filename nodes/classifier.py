from typing import Dict, Any
from llm_config import get_llm


class IntentClassifier:
    """Classifies user intent into signal type"""
    
    def __init__(self):
        self.llm = get_llm()
    
    def classify(self, user_request: str) -> Dict[str, Any]:
        """Classify user request into signal type and domain"""
        
        prompt = f"""Analyze this trading signal request and classify it.

User Request: "{user_request}"

Classify into ONE of these types:
- indicator: Technical indicators like moving averages, RSI, MACD
- condition: Price/volume conditions, thresholds, crossovers
- strategy: Complete trading strategies combining multiple signals

Also identify the main signal being requested.

Respond ONLY with this exact format (no extra text):
Type: [indicator/condition/strategy]
Signal: [specific signal name like MovingAverage, RSI, PriceThreshold, etc]
Confidence: [high/medium/low]"""

        try:
            response = self.llm.invoke(prompt)
            
            # Parse response
            lines = response.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip().lower()] = value.strip()
            
            return {
                "signal_type": result.get('type', 'indicator'),
                "signal_hint": result.get('signal', ''),
                "confidence": result.get('confidence', 'medium')
            }
        
        except Exception as e:
            # Fallback: simple keyword matching
            request_lower = user_request.lower()
            
            if any(word in request_lower for word in ['strategy', 'system', 'combine']):
                return {"signal_type": "strategy", "signal_hint": "", "confidence": "low"}
            elif any(word in request_lower for word in ['if', 'when', 'above', 'below', 'crosses']):
                return {"signal_type": "condition", "signal_hint": "", "confidence": "low"}
            else:
                return {"signal_type": "indicator", "signal_hint": "", "confidence": "low"}
