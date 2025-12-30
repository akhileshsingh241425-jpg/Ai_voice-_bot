from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    machine = db.Column(db.String(50), nullable=False)
    # ...existing code...

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    score = db.Column(db.Integer)
    passed = db.Column(db.Boolean)
    # ...existing code...


class Department(db.Model):
    """
    Main departments: Production, Quality, Maintenance, FG Area
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Production, Quality, Maintenance, FG Area
    code = db.Column(db.String(20), nullable=False)   # PROD, QC, MAINT, FG
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'


class SubDepartment(db.Model):
    """
    Sub-departments under main departments.
    E.g., Production → Pre-Lam, Post-Lam
          Quality → IPQC, IQC, FQC
    """
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Pre-Lam, Post-Lam, IPQC, etc.
    code = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    department = db.relationship('Department', backref=db.backref('sub_departments', lazy=True))
    
    def __repr__(self):
        return f'<SubDepartment {self.name}>'


class Machine(db.Model):
    """
    Machines/Stages under sub-departments.
    E.g., Pre-Lam → Stringer, Pre EL
          Post-Lam → Laminator, Post EL, Sun Simulator
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    
    # Link to sub-department (optional for backward compatibility)
    sub_department_id = db.Column(db.Integer, db.ForeignKey('sub_department.id'), nullable=True)
    
    # Category for quick filtering
    category = db.Column(db.String(50), default='General')  # Pre-Lam, Post-Lam, IPQC, etc.
    
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    sub_department = db.relationship('SubDepartment', backref=db.backref('machines', lazy=True))
    
    def __repr__(self):
        return f'<Machine {self.name}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    # ...existing code...

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    # ...existing code...


class StudyMaterial(db.Model):
    """Store study material text for each machine/topic for context-based question generation"""
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Extracted text from PDF/document
    file_path = db.Column(db.String(500))  # Original file path
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)
    
    machine = db.relationship('Machine', backref=db.backref('study_materials', lazy=True))


class MachineTraining(db.Model):
    """
    Store training data for each machine to improve question generation.
    Works like few-shot learning - saved examples guide the LLM.
    """
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    
    # Good question examples (JSON list of {question, answer})
    good_examples = db.Column(db.Text, default='[]')
    
    # Bad questions to avoid (JSON list of strings)
    bad_examples = db.Column(db.Text, default='[]')
    
    # Custom instructions for this machine
    instructions = db.Column(db.Text, default='')
    
    # Question style preferences
    question_style = db.Column(db.String(50), default='technical')  # technical, practical, safety, mixed
    preferred_language = db.Column(db.String(20), default='Hindi')
    difficulty_focus = db.Column(db.String(20), default='mixed')  # easy, medium, hard, mixed
    
    # Stats
    total_corrections = db.Column(db.Integer, default=0)
    last_trained_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    machine = db.relationship('Machine', backref=db.backref('training_data', uselist=False))


# Import viva models to register them with SQLAlchemy
try:
    from app.models.viva_models import VivaSession, VivaQuestion, VivaLevel
except ImportError:
    pass  # Models will be imported when needed
