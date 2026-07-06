"""
ML-Powered Chatbot Engine using TF-IDF and Cosine Similarity
Understands complex questions and finds best matching answers
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from typing import Tuple, Dict, List
from .chatbot_kb import KNOWLEDGE_BASE, TRAINING_PHRASES

class ChatbotEngine:
    """
    Intelligent chatbot engine using TF-IDF for semantic understanding.
    Handles complex questions and finds best matching FAQ answers.
    """
    
    def __init__(self):
        """Initialize the chatbot engine"""
        self.knowledge_base = KNOWLEDGE_BASE
        self.training_phrases = TRAINING_PHRASES
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None,  # Don't remove stop words - they might be important for matching
            ngram_range=(1, 2),  # Unigrams and bigrams for better context
            max_features=1000,
            min_df=1  # Include terms that appear even once
        )
        
        # Build FAQ document corpus
        self.faq_texts = [self._build_faq_text(faq) for faq in self.knowledge_base]
        
        # Fit the vectorizer on FAQ texts
        self.tfidf_matrix = self.vectorizer.fit_transform(self.faq_texts)
        
        # Lower confidence threshold for better matching
        self.CONFIDENCE_THRESHOLD = 0.15
        
    def _build_faq_text(self, faq: Dict) -> str:
        """Build combined text for better TF-IDF matching"""
        question = faq.get('question', '')
        keywords = ' '.join(faq.get('keywords', []))
        answer = faq.get('answer', '')
        
        # Combine all text for better vectorization
        return f"{question} {keywords} {answer}"
    
    def _preprocess_question(self, question: str) -> str:
        """
        Preprocess user question for better matching
        - Lowercase
        - Remove special characters
        - Expand common abbreviations
        """
        # Lowercase
        question = question.lower().strip()
        
        # Remove extra spaces
        question = re.sub(r'\s+', ' ', question)
        
        # Expand common abbreviations
        question = question.replace("what's", "what is")
        question = question.replace("don't", "do not")
        question = question.replace("can't", "cannot")
        question = question.replace("how's", "how is")
        
        return question
    
    def _extract_intent(self, question: str) -> str:
        """Extract user intent from question"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in self.training_phrases['emergency']):
            return 'emergency'
        elif any(word in question_lower for word in self.training_phrases['location']):
            return 'location'
        elif any(word in question_lower for word in self.training_phrases['information']):
            return 'information'
        elif any(word in question_lower for word in self.training_phrases['help']):
            return 'help'
        else:
            return 'general'
    
    def get_answer(self, user_question: str) -> Dict:
        """
        Main method to get chatbot response
        
        Args:
            user_question: User's question text
            
        Returns:
            Dictionary with answer, confidence score, and FAQ ID
        """
        # Preprocess the question
        processed_question = self._preprocess_question(user_question)
        
        # If question is too short, return a prompt
        if len(processed_question.split()) < 1:
            return {
                'answer': "I didn't quite understand that. Could you please rephrase your question? For example: 'How do I report abuse?' or 'Where can I find a shelter?'",
                'confidence': 0.0,
                'faq_id': None,
                'intent': 'unclear'
            }
        
        # Extract user intent
        intent = self._extract_intent(processed_question)
        
        # First, check for keyword matches (high priority)
        keyword_match = self._find_keyword_match(processed_question)
        if keyword_match:
            best_faq = keyword_match
            best_similarity = 0.9  # High confidence for keyword matches
        else:
            # Vectorize the user question
            user_vector = self.vectorizer.transform([processed_question])
            
            # Calculate similarity with all FAQ answers
            similarities = cosine_similarity(user_vector, self.tfidf_matrix)[0]
            
            # Get the best match
            best_match_idx = np.argmax(similarities)
            best_similarity = similarities[best_match_idx]
            
            # Check if similarity meets threshold
            if best_similarity < self.CONFIDENCE_THRESHOLD:
                return {
                    'answer': self._get_fallback_answer(intent),
                    'confidence': 0.0,
                    'faq_id': None,
                    'intent': intent
                }
            
            best_faq = self.knowledge_base[best_match_idx]
        
        # Return the best matching answer
        return {
            'answer': best_faq['answer'],
            'confidence': float(best_similarity),
            'faq_id': best_faq['id'],
            'question': best_faq['question'],
            'intent': intent
        }
    
    def _find_keyword_match(self, question: str) -> Dict or None:
        """Find exact keyword matches in FAQ knowledge base"""
        question_lower = question.lower()
        best_match = None
        best_match_count = 0
        
        for faq in self.knowledge_base:
            keywords = [k.lower() for k in faq.get('keywords', [])]
            question_text = faq.get('question', '').lower()
            
            # Count how many keywords match
            match_count = sum(1 for keyword in keywords if keyword in question_lower)
            
            # Also check if question text matches
            if question_lower in question_text or question_text in question_lower:
                match_count += 3  # Boost score for question text match
            
            if match_count > best_match_count:
                best_match_count = match_count
                best_match = faq
        
        # Return match only if we found keywords
        return best_match if best_match_count > 0 else None
    
    def _get_fallback_answer(self, intent: str) -> str:
        """Get appropriate fallback answer based on intent"""
        fallback_answers = {
            'emergency': (
                "🚨 **EMERGENCY**: If you need immediate help, please call our 24/7 Crisis Hotline: **999-8888** "
                "or dial 911. Your safety is our priority.\n\n"
                "Please describe your situation more clearly so I can provide better guidance."
            ),
            'location': (
                "📍 To find service locations, please visit our **Resource Center** page where you can view "
                "all PNP Women's Desks, shelters, and counseling centers on an interactive map.\n\n"
                "Would you like to know about a specific type of service?"
            ),
            'information': (
                "ℹ️ I don't have specific information about that topic. "
                "Please try asking about:\n"
                "- Reporting abuse\n"
                "- Legal protection (RA 9262)\n"
                "- Available services and shelters\n"
                "- Emergency contacts\n"
                "- Support programs\n\n"
                "Or contact us at **999-8888** for more detailed information."
            ),
            'help': (
                "💙 I'm here to help! You can ask me about:\n"
                "- How to report abuse\n"
                "- Your rights under the law\n"
                "- Available support services\n"
                "- Emergency contacts\n"
                "- Free programs and counseling\n\n"
                "What would you like to know?"
            ),
            'general': (
                "I'm not sure how to answer that. Could you try rephrasing your question? "
                "For example:\n"
                "- 'What is RA 9262?'\n"
                "- 'Where can I find help?'\n"
                "- 'How do I report?'\n\n"
                "Or call our hotline: **999-8888**"
            )
        }
        
        return fallback_answers.get(intent, fallback_answers['general'])
    
    def get_all_faqs(self) -> List[Dict]:
        """Return all FAQs for reference"""
        return self.knowledge_base
    
    def add_faq(self, question: str, answer: str, keywords: List[str] = None) -> bool:
        """
        Add new FAQ to knowledge base and retrain
        
        Args:
            question: FAQ question
            answer: FAQ answer
            keywords: Related keywords for better matching
            
        Returns:
            True if added successfully
        """
        try:
            new_faq = {
                'id': len(self.knowledge_base) + 1,
                'question': question,
                'answer': answer,
                'keywords': keywords or []
            }
            self.knowledge_base.append(new_faq)
            
            # Rebuild the chatbot with new FAQ
            self.__init__()  # Reinitialize to retrain
            
            return True
        except Exception as e:
            print(f"Error adding FAQ: {e}")
            return False


# Global chatbot instance
chatbot = None

def get_chatbot():
    """Get or create the global chatbot instance"""
    global chatbot
    if chatbot is None:
        chatbot = ChatbotEngine()
    return chatbot
