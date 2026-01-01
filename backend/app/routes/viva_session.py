"""
Viva Session Routes
- Start new viva session
- Submit answer for evaluation
- Complete viva and get results
- Generate report
"""

from flask import Blueprint, request, jsonify
import json
import uuid
from datetime import datetime
from app.db_config import get_db

viva_session_bp = Blueprint('viva_session', __name__)

# In-memory session storage (can be moved to Redis for production)
active_sessions = {}


def get_db_connection():
    return get_db()


def evaluate_answer_semantic(user_answer, expected_answer, question):
    """
    Evaluate user answer against expected answer using semantic similarity
    Uses sentence-transformers for meaning-based matching
    """
    from sentence_transformers import SentenceTransformer, util
    
    if not user_answer or not expected_answer:
        return {
            'score': 0,
            'passed': False,
            'feedback': 'No answer provided'
        }
    
    # Clean answers
    user_answer = user_answer.strip().lower()
    expected_answer = expected_answer.strip().lower()
    
    # Load model (cached)
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    
    # Get embeddings
    user_emb = model.encode(user_answer, convert_to_tensor=True)
    expected_emb = model.encode(expected_answer, convert_to_tensor=True)
    
    # Calculate similarity
    similarity = util.pytorch_cos_sim(user_emb, expected_emb).item()
    score = int(similarity * 100)
    
    # Determine if passed (50% threshold)
    passed = score >= 50
    
    # Generate feedback
    if score >= 80:
        feedback = "Excellent! Very accurate answer."
    elif score >= 60:
        feedback = "Good answer. Mostly correct."
    elif score >= 50:
        feedback = "Acceptable. Basic understanding shown."
    elif score >= 30:
        feedback = "Partial understanding. Review this topic."
    else:
        feedback = "Incorrect. Please study this topic."
    
    return {
        'score': score,
        'passed': passed,
        'feedback': feedback,
        'similarity': round(similarity, 2)
    }


@viva_session_bp.route('/viva/start', methods=['POST'])
def start_viva():
    """
    Start a new viva session
    Body: { employee_id, employee_name, machine_id OR topic_id, question_count (default 20), language (HI/EN) }
    """
    data = request.json
    employee_id = data.get('employee_id')
    employee_name = data.get('employee_name', '')
    machine_id = data.get('machine_id')
    topic_id = data.get('topic_id')  # NEW: Training topic support
    question_count = data.get('question_count', 20)
    language = data.get('language', 'HI')  # NEW: Language support
    
    if not employee_id:
        return jsonify({'error': 'employee_id required'}), 400
    
    if not machine_id and not topic_id:
        return jsonify({'error': 'machine_id or topic_id required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        source_name = ''
        source_type = ''
        questions = []
        
        # NEW: If topic_id provided, use training topic Q&A
        if topic_id:
            cursor.execute("SELECT name FROM training_topic WHERE id = %s", (topic_id,))
            topic = cursor.fetchone()
            if not topic:
                return jsonify({'error': 'Training topic not found'}), 404
            
            source_name = topic['name']
            source_type = 'topic'
            
            # Get questions from qa_bank_new with language filter
            level1_count = int(question_count * 0.4)
            level2_count = int(question_count * 0.35)
            level3_count = question_count - level1_count - level2_count
            
            for level, count in [(1, level1_count), (2, level2_count), (3, level3_count)]:
                cursor.execute("""
                    SELECT id, question, expected_answer, level, 'Training' as category
                    FROM qa_bank_new 
                    WHERE topic_id = %s AND level = %s AND language = %s AND is_active = TRUE
                    ORDER BY RAND()
                    LIMIT %s
                """, (topic_id, level, language, count))
                questions.extend(cursor.fetchall())
        
        else:
            # OLD: Machine-based questions
            cursor.execute("SELECT name, category FROM machine WHERE id = %s", (machine_id,))
            machine = cursor.fetchone()
            if not machine:
                return jsonify({'error': 'Machine not found'}), 404
            
            source_name = machine['name']
            source_type = 'machine'
            
            level1_count = int(question_count * 0.4)
            level2_count = int(question_count * 0.35)
            level3_count = question_count - level1_count - level2_count
            
            for level, count in [(1, level1_count), (2, level2_count), (3, level3_count)]:
                cursor.execute("""
                    SELECT id, question, expected_answer, level, category
                    FROM qa_bank 
                    WHERE machine_id = %s AND level = %s AND is_active = TRUE
                    ORDER BY RAND()
                    LIMIT %s
                """, (machine_id, level, count))
                questions.extend(cursor.fetchall())
        
        conn.close()
        
        if not questions:
            return jsonify({
                'error': f'No questions available for this {source_type}. Please upload Q&A first.'
            }), 400
        
        # Create session
        session_id = str(uuid.uuid4())[:8]
        
        session_data = {
            'session_id': session_id,
            'employee_id': employee_id,
            'employee_name': employee_name,
            'machine_id': machine_id,
            'topic_id': topic_id,
            'source_name': source_name,
            'source_type': source_type,
            'language': language,
            'questions': questions,
            'current_index': 0,
            'answers': [],
            'started_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        active_sessions[session_id] = session_data
        
        # Return first question
        first_question = questions[0]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'total_questions': len(questions),
            'machine_name': machine['name'],
            'current_question': {
                'index': 1,
                'total': len(questions),
                'question_id': first_question['id'],
                'question': first_question['question'],
                'level': first_question['level'],
                'category': first_question.get('category', 'General')
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@viva_session_bp.route('/viva/answer', methods=['POST'])
def submit_answer():
    """
    Submit answer for current question
    Body: { session_id, answer }
    Returns: evaluation result + next question
    """
    data = request.json
    session_id = data.get('session_id')
    user_answer = data.get('answer', '')
    
    if not session_id:
        return jsonify({'error': 'session_id required'}), 400
    
    session = active_sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found or expired'}), 404
    
    if session['status'] != 'active':
        return jsonify({'error': 'Session already completed'}), 400
    
    try:
        current_index = session['current_index']
        current_question = session['questions'][current_index]
        
        # Evaluate answer
        evaluation = evaluate_answer_semantic(
            user_answer,
            current_question['expected_answer'],
            current_question['question']
        )
        
        # Store answer
        answer_record = {
            'question_id': current_question['id'],
            'question': current_question['question'],
            'expected_answer': current_question['expected_answer'],
            'user_answer': user_answer,
            'score': evaluation['score'],
            'passed': evaluation['passed'],
            'feedback': evaluation['feedback'],
            'level': current_question['level']
        }
        session['answers'].append(answer_record)
        
        # Update question stats in database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if evaluation['passed']:
                cursor.execute("""
                    UPDATE qa_bank SET times_asked = times_asked + 1, times_correct = times_correct + 1
                    WHERE id = %s
                """, (current_question['id'],))
            else:
                cursor.execute("""
                    UPDATE qa_bank SET times_asked = times_asked + 1
                    WHERE id = %s
                """, (current_question['id'],))
            conn.commit()
            conn.close()
        except:
            pass
        
        # Move to next question
        session['current_index'] += 1
        
        # Check if more questions
        if session['current_index'] < len(session['questions']):
            next_question = session['questions'][session['current_index']]
            return jsonify({
                'success': True,
                'evaluation': evaluation,
                'has_next': True,
                'current_question': {
                    'index': session['current_index'] + 1,
                    'total': len(session['questions']),
                    'question_id': next_question['id'],
                    'question': next_question['question'],
                    'level': next_question['level'],
                    'category': next_question.get('category', 'General')
                }
            })
        else:
            # All questions answered - auto complete
            session['status'] = 'completed'
            session['completed_at'] = datetime.now().isoformat()
            
            # Calculate final results
            total_score = sum(a['score'] for a in session['answers'])
            avg_score = total_score / len(session['answers']) if session['answers'] else 0
            passed_count = sum(1 for a in session['answers'] if a['passed'])
            
            final_passed = avg_score >= 50
            
            # Save to database
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO viva_result 
                    (session_id, employee_id, employee_name, machine_id, total_questions,
                     correct_answers, total_score, percentage, passed, detailed_results)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id,
                    session['employee_id'],
                    session['employee_name'],
                    session['machine_id'],
                    len(session['answers']),
                    passed_count,
                    total_score,
                    round(avg_score, 2),
                    final_passed,
                    json.dumps(session['answers'])
                ))
                conn.commit()
                conn.close()
            except Exception as db_err:
                print(f"Error saving viva result: {db_err}")
            
            return jsonify({
                'success': True,
                'evaluation': evaluation,
                'has_next': False,
                'completed': True,
                'result': {
                    'session_id': session_id,
                    'total_questions': len(session['answers']),
                    'correct_answers': passed_count,
                    'total_score': total_score,
                    'average_score': round(avg_score, 2),
                    'passed': final_passed,
                    'grade': get_grade(avg_score)
                }
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@viva_session_bp.route('/viva/status/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """Get current status of a viva session"""
    session = active_sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_id,
        'status': session['status'],
        'employee_name': session['employee_name'],
        'machine_name': session['machine_name'],
        'total_questions': len(session['questions']),
        'answered': len(session['answers']),
        'current_index': session['current_index'],
        'started_at': session['started_at']
    })


@viva_session_bp.route('/viva/result/<session_id>', methods=['GET'])
def get_viva_result(session_id):
    """Get detailed result of a completed viva session"""
    # First check active sessions
    session = active_sessions.get(session_id)
    if session and session['status'] == 'completed':
        answers = session['answers']
        passed_count = sum(1 for a in answers if a['passed'])
        total_score = sum(a['score'] for a in answers)
        avg_score = total_score / len(answers) if answers else 0
        
        return jsonify({
            'session_id': session_id,
            'employee_id': session['employee_id'],
            'employee_name': session['employee_name'],
            'machine_name': session['machine_name'],
            'total_questions': len(answers),
            'correct_answers': passed_count,
            'total_score': total_score,
            'average_score': round(avg_score, 2),
            'passed': avg_score >= 50,
            'grade': get_grade(avg_score),
            'detailed_results': answers,
            'started_at': session['started_at'],
            'completed_at': session.get('completed_at')
        })
    
    # Check database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vr.*, m.name as machine_name
            FROM viva_result vr
            LEFT JOIN machine m ON m.id = vr.machine_id
            WHERE vr.session_id = %s
        """, (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            detailed = json.loads(result['detailed_results']) if result['detailed_results'] else []
            return jsonify({
                'session_id': result['session_id'],
                'employee_id': result['employee_id'],
                'employee_name': result['employee_name'],
                'machine_name': result['machine_name'],
                'total_questions': result['total_questions'],
                'correct_answers': result['correct_answers'],
                'total_score': result['total_score'],
                'average_score': result['percentage'],
                'passed': result['passed'],
                'grade': get_grade(result['percentage']),
                'detailed_results': detailed,
                'created_at': result['created_at'].isoformat() if result['created_at'] else None
            })
        
        return jsonify({'error': 'Result not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@viva_session_bp.route('/viva/history', methods=['GET'])
def get_viva_history():
    """Get viva history with filters"""
    employee_id = request.args.get('employee_id')
    machine_id = request.args.get('machine_id')
    limit = request.args.get('limit', 50, type=int)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT vr.*, m.name as machine_name, m.category as machine_category
            FROM viva_result vr
            LEFT JOIN machine m ON m.id = vr.machine_id
            WHERE 1=1
        """
        params = []
        
        if employee_id:
            query += " AND vr.employee_id = %s"
            params.append(employee_id)
        
        if machine_id:
            query += " AND vr.machine_id = %s"
            params.append(machine_id)
        
        query += " ORDER BY vr.created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Format results
        formatted = []
        for r in results:
            formatted.append({
                'id': r['id'],
                'session_id': r['session_id'],
                'employee_id': r['employee_id'],
                'employee_name': r['employee_name'],
                'machine_name': r['machine_name'],
                'machine_category': r.get('machine_category'),
                'total_questions': r['total_questions'],
                'correct_answers': r['correct_answers'],
                'percentage': r['percentage'],
                'passed': r['passed'],
                'grade': get_grade(r['percentage']),
                'created_at': r['created_at'].isoformat() if r['created_at'] else None
            })
        
        return jsonify({
            'count': len(formatted),
            'results': formatted
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@viva_session_bp.route('/viva/skip', methods=['POST'])
def skip_question():
    """Skip current question (counts as wrong answer)"""
    data = request.json
    session_id = data.get('session_id')
    
    # Submit empty answer (will be evaluated as 0)
    data['answer'] = ''
    return submit_answer()


def get_grade(score):
    """Convert score to grade"""
    if score >= 90:
        return 'A+'
    elif score >= 80:
        return 'A'
    elif score >= 70:
        return 'B+'
    elif score >= 60:
        return 'B'
    elif score >= 50:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'
