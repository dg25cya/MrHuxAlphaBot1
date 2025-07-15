"""Sentiment analysis utilities."""
from typing import Dict, List, Any, Union
import re
from collections import Counter
from ..utils.metrics_registry import metrics

class SentimentAnalyzer:
    """Basic sentiment analyzer for token mentions."""
    
    def __init__(self) -> None:
        """Initialize the sentiment analyzer with lexicons."""
        try:
            self.SENTIMENT_SCORES = metrics.SENTIMENT_SCORES
            self.SENTIMENT_ERRORS = metrics.SENTIMENT_ERRORS
        except AttributeError:
            self.SENTIMENT_SCORES = None
            self.SENTIMENT_ERRORS = None
        self.positive_words = {
            'bullish', 'moon', 'mooning', 'gem', 'pump', 'pumping', 'soaring',
            'rocket', 'exploding', 'buy', 'buying', 'good', 'great', 'amazing',
            'awesome', 'excellent', 'promising', 'potential', 'opportunity',
            'early', 'growth', 'profit', 'profits', 'profitable', 'gain', 'gains',
            'winning', 'win', 'winner', 'strong', 'strength', 'hodl', 'hold',
            'target', 'undervalued', 'bullrun', 'breakout', 'breaking', 'up',
            'rising', 'rise', 'ath', 'high', 'higher', 'highest',
        }
        
        self.negative_words = {
            'bearish', 'dump', 'dumping', 'crash', 'crashing', 'sell', 'selling',
            'bad', 'terrible', 'avoid', 'scam', 'rug', 'rugpull', 'ponzi', 'drop',
            'dropping', 'loss', 'losses', 'losing', 'lose', 'loser', 'weak',
            'weakness', 'overvalued', 'risk', 'risky', 'down', 'falling', 'fall',
            'decline', 'declining', 'low', 'lower', 'lowest',
        }
        
        self.intensity_modifiers = {
            'very': 2.0,
            'extremely': 2.5,
            'super': 2.0,
            'massively': 2.0,
            'huge': 1.8,
            'big': 1.5,
            'major': 1.5,
            'incredible': 2.0,
            'really': 1.5,
            'definitely': 1.5,
            'absolutely': 1.7,
            'totally': 1.5,
            'completely': 1.5,
            'insanely': 2.0,
            'unbelievably': 2.0,
            'too': 1.3,
            'so': 1.3,
        }
        
        self.negation_words = {
            'not', 'no', 'never', 'none', "don't", 'dont', "doesn't", 'doesnt',
            "isn't", 'isnt', "aren't", 'arent', "wasn't", 'wasnt', "weren't",
            'werent', 'without', 'lack', 'lacks', 'lacking'
        }
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze text and return detailed sentiment analysis.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing sentiment score and analysis details
        """
        try:
            score = self.analyze_text(text)
            
            # Track sentiment score
            if self.SENTIMENT_SCORES:
                self.SENTIMENT_SCORES.observe(score)
            
            # Extract key words that contributed to sentiment
            positive_matches = [word for word in self.positive_words if word in text.lower()]
            negative_matches = [word for word in self.negative_words if word in text.lower()]
            
            return {
                "score": score,
                "positive_words": positive_matches[:5],  # Top 5 for brevity
                "negative_words": negative_matches[:5],
                "magnitude": abs(score)
            }
            
        except Exception as e:
            if self.SENTIMENT_ERRORS:
                self.SENTIMENT_ERRORS.labels(error_type="analysis_error").inc()
            return {
                "score": 0.0,
                "error": str(e),
                "positive_words": [],
                "negative_words": [],
                "magnitude": 0.0
            }

    def analyze_text(self, text: str) -> float:
        """
        Analyze text and return sentiment score between -1 and 1.
        
        Args:
            text: The text to analyze
            
        Returns:
            Sentiment score between -1 (very negative) and 1 (very positive)
        """
        if not text:
            return 0.0
        
        # Convert to lowercase and tokenize
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        if not words:
            return 0.0
        
        # Calculate sentiment
        score = 0.0
        negation = False
        skip_next = False
        
        for i, word in enumerate(words):
            if skip_next:
                skip_next = False
                continue
                
            # Check for negation
            if word in self.negation_words:
                negation = True
                continue
            
            # Get basic sentiment for the word
            word_score = 0.0
            if word in self.positive_words:
                word_score = 1.0
            elif word in self.negative_words:
                word_score = -1.0
                
            # Apply negation if needed
            if negation:
                word_score = -word_score
                negation = False
            
            # Apply intensity modifier from previous word
            if i > 0 and words[i-1] in self.intensity_modifiers:
                word_score *= self.intensity_modifiers[words[i-1]]
            
            # Apply intensity modifier from next word
            if i < len(words) - 1 and words[i+1] in self.intensity_modifiers:
                word_score *= self.intensity_modifiers[words[i+1]]
                skip_next = True
            
            score += word_score
        
        # Normalize to range [-1, 1]
        normalized_score = max(min(score / (len(words) * 0.5), 1.0), -1.0)
        
        return normalized_score
    
    def analyze_mentions(self, mentions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a list of mentions and return sentiment metrics.
        
        Args:
            mentions: List of mention dictionaries with 'text' fields
            
        Returns:
            Dictionary of sentiment metrics
        """
        if not mentions:
            return {
                "overall_sentiment": 0.0,
                "positive_percentage": 0.0,
                "negative_percentage": 0.0,
                "neutral_percentage": 0.0,
                "sentiment_count": {"positive": 0, "negative": 0, "neutral": 0},
                "mention_count": 0
            }
        
        sentiment_scores = []
        sentiment_categories = Counter()
        
        for mention in mentions:
            text = mention.get('text', '')
            
            # If mention already has sentiment, use it
            if 'sentiment' in mention and isinstance(mention['sentiment'], (int, float)):
                score = mention['sentiment']
            else:
                # Otherwise calculate it
                score = self.analyze_text(text)
            
            sentiment_scores.append(score)
            
            # Categorize sentiment
            if score > 0.2:
                sentiment_categories['positive'] += 1
            elif score < -0.2:
                sentiment_categories['negative'] += 1
            else:
                sentiment_categories['neutral'] += 1
        
        total_mentions = len(mentions)
        
        # Calculate overall metrics
        results = {
            "overall_sentiment": sum(sentiment_scores) / total_mentions if sentiment_scores else 0.0,
            "positive_percentage": (sentiment_categories['positive'] / total_mentions) * 100 if total_mentions else 0.0,
            "negative_percentage": (sentiment_categories['negative'] / total_mentions) * 100 if total_mentions else 0.0,
            "neutral_percentage": (sentiment_categories['neutral'] / total_mentions) * 100 if total_mentions else 0.0,
            "sentiment_count": dict(sentiment_categories),
            "mention_count": total_mentions
        }
        
        return results
