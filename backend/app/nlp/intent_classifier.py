"""
DOER Platform - Intent Classification System

Uses scikit-learn TF-IDF + Naive Bayes for lightweight dispute classification.
Trained on synthetic data for 5 dispute categories.

CATEGORIES:
- ownership_dispute: Property ownership conflicts
- boundary_dispute: Land boundary disagreements
- inheritance_dispute: Inheritance-related conflicts
- encroachment: Illegal occupation of land
- title_issue: Title deed problems

PRODUCTION UPGRADES:
- Use BERT-based transformer models for better accuracy
- Implement active learning pipeline
- Add multi-label classification support
- Fine-tune on actual legal documents
"""

import os
import pickle
from typing import Dict, Optional, Tuple, List
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import numpy as np

from app.nlp.training_data import get_training_texts_and_labels, INTENT_CATEGORIES


class IntentClassifier:
    """
    Lightweight intent classifier for land dispute categorization.
    
    Uses TF-IDF vectorization with Multinomial Naive Bayes.
    Fast inference suitable for real-time API responses.
    """
    
    MODEL_VERSION = "1.0.0"
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the classifier.
        
        Args:
            model_path: Path to saved model. If None, creates new model.
        """
        self.model_path = model_path or self._default_model_path()
        self.pipeline: Optional[Pipeline] = None
        self.categories = list(INTENT_CATEGORIES.keys())
        self._is_trained = False
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            self.load_model()
    
    def _default_model_path(self) -> str:
        """Get default model path in data directory."""
        base_dir = Path(__file__).parent.parent.parent / "data" / "models"
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir / "intent_classifier.pkl")
    
    def _create_pipeline(self) -> Pipeline:
        """Create the ML pipeline."""
        return Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
                min_df=2,
                max_df=0.95,
                lowercase=True,
                stop_words='english'
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
    
    def train(self, test_size: float = 0.2) -> Dict[str, any]:
        """
        Train the classifier on synthetic data.
        
        Args:
            test_size: Fraction of data to use for testing
            
        Returns:
            Dict with training metrics
        """
        texts, labels = get_training_texts_and_labels()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        # Create and train pipeline
        self.pipeline = self._create_pipeline()
        self.pipeline.fit(X_train, y_train)
        self._is_trained = True
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        accuracy = (y_pred == np.array(y_test)).mean()
        
        # Get detailed report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save model
        self.save_model()
        
        return {
            "accuracy": accuracy,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "categories": self.categories,
            "report": report
        }
    
    def predict(self, text: str) -> Dict[str, any]:
        """
        Predict the intent category for input text.
        
        Args:
            text: Input text (should be in English or translated)
            
        Returns:
            Dict with category, confidence, and all probabilities
        """
        if not self._is_trained:
            # Auto-train if not trained
            self.train()
        
        if not text or not text.strip():
            return {
                "category": "unknown",
                "confidence": 0.0,
                "all_scores": {cat: 0.0 for cat in self.categories}
            }
        
        # Get prediction and probabilities
        category = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        
        # Map probabilities to categories
        classes = self.pipeline.classes_
        all_scores = {
            classes[i]: float(probabilities[i]) 
            for i in range(len(classes))
        }
        
        confidence = float(max(probabilities))
        
        return {
            "category": category,
            "confidence": confidence,
            "all_scores": all_scores,
            "description": INTENT_CATEGORIES.get(category, "Unknown category")
        }
    
    def predict_batch(self, texts: List[str]) -> List[Dict[str, any]]:
        """Predict intents for multiple texts."""
        return [self.predict(text) for text in texts]
    
    def save_model(self) -> None:
        """Save trained model to disk."""
        if self.pipeline is None:
            raise ValueError("No model to save. Train first.")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            "pipeline": self.pipeline,
            "categories": self.categories,
            "version": self.MODEL_VERSION
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self) -> bool:
        """
        Load model from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.pipeline = model_data["pipeline"]
            self.categories = model_data.get("categories", self.categories)
            self._is_trained = True
            return True
            
        except Exception as e:
            print(f"Could not load model: {e}")
            return False


# Singleton instance
_classifier: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    """Get or create the intent classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
        # Ensure model is trained
        if not _classifier._is_trained:
            _classifier.train()
    return _classifier


def classify_dispute(text: str) -> Dict[str, any]:
    """
    Convenience function to classify a dispute text.
    
    Args:
        text: Dispute description (English preferred)
        
    Returns:
        Classification result with category and confidence
    """
    classifier = get_intent_classifier()
    return classifier.predict(text)
