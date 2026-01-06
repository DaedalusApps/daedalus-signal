"""
Keyword filtering engine
"""
import re
from app.database import get_session, close_session
from app.models import User, Tag


class KeywordFilter:
    """Filter content based on keyword matching."""
    
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.keywords = []
        self._load_keywords()
    
    def _load_keywords(self):
        """Load keywords from user's tags or defaults."""
        db = get_session()
        try:
            if self.user_id:
                user = db.query(User).filter_by(id=self.user_id).first()
                if user and user.tags:
                    self.keywords = [tag.name.lower() for tag in user.tags]
            
            if not self.keywords:
                # Use default tags
                default_tags = db.query(Tag).filter_by(is_default=True).all()
                self.keywords = [tag.name.lower() for tag in default_tags]
            
            # Add built-in AI-related keywords
            if not self.keywords:
                self.keywords = [
                    'ai', 'artificial intelligence', 'machine learning',
                    'deep learning', 'llm', 'gpt', 'agent', 'agentic',
                    'context engineering', 'prompt engineering', 'rag',
                    'transformer', 'neural network', 'nlp', 'automation'
                ]
        finally:
            close_session(db)
    
    def calculate_relevance(self, content: dict) -> int:
        """
        Calculate relevance score (0-100) based on keyword matches.
        """
        if not self.keywords:
            return 50  # Default score if no keywords
        
        text = f"{content.get('title', '')} {content.get('description', '')}".lower()
        
        if not text.strip():
            return 0
        
        matches = 0
        keyword_weights = {}
        
        for keyword in self.keywords:
            # Count occurrences
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            count = len(pattern.findall(text))
            
            if count > 0:
                matches += 1
                keyword_weights[keyword] = min(count, 3)  # Cap at 3 per keyword
        
        if matches == 0:
            return 0
        
        # Calculate score
        # Base: percentage of keywords matched (max 50 points)
        match_ratio = matches / len(self.keywords)
        base_score = min(50, int(match_ratio * 100))
        
        # Bonus: keyword frequency (max 30 points)
        frequency_score = min(30, sum(keyword_weights.values()) * 5)
        
        # Bonus: title matches are more valuable (max 20 points)
        title = content.get('title', '').lower()
        title_matches = sum(1 for k in self.keywords if k in title)
        title_score = min(20, title_matches * 10)
        
        total = base_score + frequency_score + title_score
        return min(100, total)
    
    def filter_content(self, content_list: list[dict], min_score: int = 10) -> list[dict]:
        """
        Filter and score a list of content items.
        Returns items with relevance >= min_score, sorted by score.
        """
        scored = []
        
        for content in content_list:
            score = self.calculate_relevance(content)
            if score >= min_score:
                content['relevance_score'] = score
                scored.append(content)
        
        # Sort by relevance score descending
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored
