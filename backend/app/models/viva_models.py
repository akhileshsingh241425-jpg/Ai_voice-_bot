from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app.models.models import db

class VivaSession(db.Model):
    """Viva session tracking for employee progression"""
    __tablename__ = 'viva_session'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    current_level = db.Column(db.Integer, default=1)  # 1, 2, 3
    status = db.Column(db.String(20), default='active')  # active, completed, failed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_score = db.Column(db.Float, default=0.0)
    level_1_score = db.Column(db.Float, default=0.0)
    level_2_score = db.Column(db.Float, default=0.0)
    level_3_score = db.Column(db.Float, default=0.0)
    questions_attempted = db.Column(db.Integer, default=0)
    questions_correct = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('Employee', backref=db.backref('viva_sessions', lazy=True))
    machine = db.relationship('Machine', backref=db.backref('viva_sessions', lazy=True))

class VivaQuestion(db.Model):
    """Track questions asked during viva session"""
    __tablename__ = 'viva_question'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('viva_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=True)  # Nullable for AI-generated questions
    level = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    expected_answer = db.Column(db.Text, nullable=False)
    user_answer = db.Column(db.Text)
    audio_file_path = db.Column(db.String(255))
    score = db.Column(db.Float, default=0.0)
    is_correct = db.Column(db.Boolean, default=False)
    time_taken = db.Column(db.Integer)  # seconds
    asked_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)
    is_ai_generated = db.Column(db.Boolean, default=False)  # Flag for AI-generated questions
    
    # Relationships
    session = db.relationship('VivaSession', backref=db.backref('viva_questions', lazy=True))
    question = db.relationship('Question', backref=db.backref('viva_questions', lazy=True))

class VivaLevel(db.Model):
    """Track level completion status"""
    __tablename__ = 'viva_level'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('viva_session.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, passed, failed
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    questions_count = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0.0)
    passing_threshold = db.Column(db.Float, default=60.0)  # Minimum score to pass
    
    # Relationships
    session = db.relationship('VivaSession', backref=db.backref('levels', lazy=True))