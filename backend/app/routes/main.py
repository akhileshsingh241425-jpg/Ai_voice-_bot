from flask import Blueprint, request, jsonify
from app.models.models import db, Employee, Score, Machine

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return '''<h1>AI Voice Bot Server</h1>
<p>Core APIs:</p>
<ul>
<li><a href="/employees">/employees</a> - Employee management</li>
<li><a href="/machines">/machines</a> - Get all machines with question counts</li>
</ul>

<p>AI APIs:</p>
<ul>
<li>/stt - Speech to Text (POST audio file)</li>
<li>/evaluate - Answer evaluation (POST JSON)</li>
<li>/sstp - Complete STT + Evaluation pipeline (POST audio + data)</li>
</ul>

<p>Question Management APIs:</p>
<ul>
<li>/questions - Add question (POST JSON)</li>
<li>/questions/&lt;machine_id&gt;/&lt;level&gt; - Get questions by machine & level</li>
<li>/questions/random/&lt;machine_id&gt;/&lt;level&gt; - Get random question for viva</li>
<li>/questions/bulk - Bulk add questions (POST JSON)</li>
</ul>

<p>Viva Session Management APIs:</p>
<ul>
<li>/start_viva - Start new viva session (POST JSON)</li>
<li>/get_question/&lt;session_id&gt; - Get next question for current level</li>
<li>/submit_answer/&lt;viva_question_id&gt; - Submit answer (text/audio)</li>
<li>/complete_level/&lt;session_id&gt; - Complete current level and progress</li>
<li>/viva_progress/&lt;session_id&gt; - Get detailed session progress</li>
<li>/active_sessions - Get all active viva sessions</li>
<li>/end_session/&lt;session_id&gt; - Manually end session (admin)</li>
</ul>

<p>Other APIs:</p>
<ul>
<li>/upload_manual - Upload training manuals</li>
<li>/recommend_training - Training recommendations</li>
<li>/department_dashboard - Department analytics</li>
</ul>'''

@main_bp.route('/employees', methods=['GET'])
def get_employees():
    employees = Employee.query.all()
    return jsonify([{'id': e.id, 'name': e.name, 'role': e.role, 'machine': e.machine} for e in employees])

@main_bp.route('/score', methods=['POST'])
def submit_score():
    data = request.json
    score = Score(employee_id=data['employee_id'], score=data['score'], passed=data['passed'])
    db.session.add(score)
    db.session.commit()
    return jsonify({'message': 'Score submitted successfully'})

# Add more endpoints as needed
