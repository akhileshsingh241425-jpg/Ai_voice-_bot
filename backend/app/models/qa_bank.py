"""
Q&A Bank Model
Store pre-defined questions and answers for each department/machine.
Used for viva sessions - random questions selected from this bank.
LLM evaluates user answers against expected answers (semantic matching).
"""

from app.models.models import db
from datetime import datetime


class QABank(db.Model):
    """
    Store questions and answers for each department/machine.
    300+ Q&A per department for comprehensive viva coverage.
    """
    __tablename__ = 'qa_bank'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    
    # Question details
    question = db.Column(db.Text, nullable=False)
    expected_answer = db.Column(db.Text, nullable=False)
    
    # Difficulty level: 1=Easy, 2=Medium, 3=Hard
    level = db.Column(db.Integer, default=1)
    
    # Category/Topic within department (optional)
    category = db.Column(db.String(100), default='General')
    
    # Keywords for better matching (comma separated)
    keywords = db.Column(db.String(500), default='')
    
    # Language: Hindi, English, Hinglish
    language = db.Column(db.String(20), default='Hindi')
    
    # Active flag
    is_active = db.Column(db.Boolean, default=True)
    
    # Stats
    times_asked = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    machine = db.relationship('Machine', backref=db.backref('qa_bank', lazy='dynamic'))
    
    def __repr__(self):
        return f'<QABank {self.id}: {self.question[:50]}...>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'question': self.question,
            'expected_answer': self.expected_answer,
            'level': self.level,
            'category': self.category,
            'keywords': self.keywords,
            'language': self.language,
            'is_active': self.is_active,
            'times_asked': self.times_asked,
            'times_correct': self.times_correct,
            'accuracy': round(self.times_correct / self.times_asked * 100, 1) if self.times_asked > 0 else 0
        }


class VivaResult(db.Model):
    """
    Store complete viva session results with per-question analysis.
    """
    __tablename__ = 'viva_result'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Session info
    session_id = db.Column(db.String(50), nullable=False, unique=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    user_name = db.Column(db.String(100), default='Anonymous')
    
    # Results summary
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    partial_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)
    
    # Score
    total_score = db.Column(db.Float, default=0.0)  # Out of 100
    
    # Detailed results (JSON array of each question's result)
    # Format: [{"qa_id": 1, "question": "...", "expected": "...", "user_answer": "...", "score": 80, "feedback": "..."}]
    detailed_results = db.Column(db.Text, default='[]')
    
    # Level-wise scores
    level1_score = db.Column(db.Float, default=0.0)
    level2_score = db.Column(db.Float, default=0.0)
    level3_score = db.Column(db.Float, default=0.0)
    
    # Timing
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer, default=0)
    
    # Status: in_progress, completed, abandoned
    status = db.Column(db.String(20), default='in_progress')
    
    # Relationship
    machine = db.relationship('Machine', backref=db.backref('viva_results', lazy='dynamic'))
    
    def __repr__(self):
        return f'<VivaResult {self.session_id}: {self.total_score}%>'
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'session_id': self.session_id,
            'machine_id': self.machine_id,
            'user_name': self.user_name,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'partial_answers': self.partial_answers,
            'wrong_answers': self.wrong_answers,
            'total_score': round(self.total_score, 1),
            'level1_score': round(self.level1_score, 1),
            'level2_score': round(self.level2_score, 1),
            'level3_score': round(self.level3_score, 1),
            'detailed_results': json.loads(self.detailed_results) if self.detailed_results else [],
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'status': self.status
        }
