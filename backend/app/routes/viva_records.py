"""
Viva Records API
- Save viva results with video
- Get employee viva history
- Admin reports
"""

from flask import Blueprint, request, jsonify, send_file
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from app.db_config import get_db

viva_records_bp = Blueprint('viva_records', __name__, url_prefix='/viva-records')

# Video upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'viva_videos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'webm', 'mp4', 'avi', 'mkv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@viva_records_bp.route('/save', methods=['POST'])
def save_viva_record():
    """Save viva record with video"""
    try:
        # Get form data
        employee_id = request.form.get('employee_id')
        employee_name = request.form.get('employee_name')
        department = request.form.get('department', '')
        designation = request.form.get('designation', '')
        topic_id = request.form.get('topic_id')
        topic_name = request.form.get('topic_name', '')
        total_questions = int(request.form.get('total_questions', 0))
        correct_answers = int(request.form.get('correct_answers', 0))
        partial_answers = int(request.form.get('partial_answers', 0))
        wrong_answers = int(request.form.get('wrong_answers', 0))
        score_percent = float(request.form.get('score_percent', 0))
        language = request.form.get('language', 'Hindi')
        duration_seconds = int(request.form.get('duration_seconds', 0))
        started_at_str = request.form.get('started_at')
        answers_json = request.form.get('answers_json', '[]')
        
        # Parse started_at datetime (handle ISO format from JavaScript)
        started_at = None
        if started_at_str:
            try:
                # Remove 'Z' and parse ISO format
                started_at_str = started_at_str.replace('Z', '').replace('T', ' ')
                if '.' in started_at_str:
                    started_at_str = started_at_str.split('.')[0]  # Remove milliseconds
                started_at = datetime.strptime(started_at_str, '%Y-%m-%d %H:%M:%S')
            except:
                started_at = datetime.now()
        else:
            started_at = datetime.now()
        
        # Determine result
        result = 'Pass' if score_percent >= 60 else 'Fail'
        
        # Handle video upload
        video_path = None
        if 'video' in request.files:
            video = request.files['video']
            if video and video.filename and allowed_file(video.filename):
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_name = secure_filename(f"{employee_id}_{timestamp}.webm")
                video_path = os.path.join(UPLOAD_FOLDER, safe_name)
                video.save(video_path)
                # Store relative path
                video_path = f"viva_videos/{safe_name}"
        
        # Save to database
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO viva_records 
            (employee_id, employee_name, department, designation, topic_id, topic_name,
             total_questions, correct_answers, partial_answers, wrong_answers,
             score_percent, result, video_path, answers_json, language, 
             duration_seconds, started_at, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            employee_id, employee_name, department, designation, topic_id, topic_name,
            total_questions, correct_answers, partial_answers, wrong_answers,
            score_percent, result, video_path, answers_json, language,
            duration_seconds, started_at
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Viva record saved successfully',
            'record_id': record_id,
            'result': result,
            'video_saved': video_path is not None
        })
        
    except Exception as e:
        print(f"Error saving viva record: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@viva_records_bp.route('/list', methods=['GET'])
def list_records():
    """Get all viva records for display"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, employee_id, employee_name, department, designation,
                   topic_name, total_questions, correct_answers, partial_answers,
                   wrong_answers, score_percent, result, video_path, language,
                   duration_seconds, completed_at, answers_json
            FROM viva_records 
            ORDER BY completed_at DESC
            LIMIT 500
        """)
        
        records = cursor.fetchall()
        conn.close()
        
        # Format datetime
        for r in records:
            if r['completed_at']:
                r['completed_at'] = r['completed_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'records': records,
            'total': len(records)
        })
        
    except Exception as e:
        print(f"Error listing records: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@viva_records_bp.route('/employee/<employee_id>', methods=['GET'])
def get_employee_history(employee_id):
    """Get viva history for an employee"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, employee_name, topic_name, total_questions, correct_answers,
               score_percent, result, video_path, language, duration_seconds,
               completed_at
        FROM viva_records 
        WHERE employee_id = %s
        ORDER BY completed_at DESC
        LIMIT 50
    """, (employee_id,))
    
    records = cursor.fetchall()
    conn.close()
    
    # Format datetime
    for r in records:
        if r['completed_at']:
            r['completed_at'] = r['completed_at'].strftime('%Y-%m-%d %H:%M')
    
    return jsonify({
        'success': True,
        'employee_id': employee_id,
        'total_records': len(records),
        'records': records
    })


@viva_records_bp.route('/detail/<int:record_id>', methods=['GET'])
def get_record_detail(record_id):
    """Get detailed viva record with answers"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM viva_records WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record:
        return jsonify({'success': False, 'error': 'Record not found'}), 404
    
    # Parse answers JSON
    if record['answers_json']:
        try:
            record['answers'] = json.loads(record['answers_json'])
        except:
            record['answers'] = []
    
    # Format datetime
    if record['completed_at']:
        record['completed_at'] = record['completed_at'].strftime('%Y-%m-%d %H:%M:%S')
    if record['started_at']:
        record['started_at'] = record['started_at'].strftime('%Y-%m-%d %H:%M:%S')
    if record['created_at']:
        record['created_at'] = record['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'success': True,
        'record': record
    })


@viva_records_bp.route('/video/<int:record_id>', methods=['GET'])
def get_video(record_id):
    """Stream video for a viva record"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT video_path FROM viva_records WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    conn.close()
    
    if not record or not record['video_path']:
        return jsonify({'success': False, 'error': 'Video not found'}), 404
    
    video_full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), record['video_path'])
    
    if not os.path.exists(video_full_path):
        return jsonify({'success': False, 'error': 'Video file not found'}), 404
    
    return send_file(video_full_path, mimetype='video/webm')


@viva_records_bp.route('/all', methods=['GET'])
def get_all_records():
    """Get all viva records (admin)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    department = request.args.get('department', '')
    topic_id = request.args.get('topic_id', type=int)
    result_filter = request.args.get('result', '')
    
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Build query
    query = """
        SELECT id, employee_id, employee_name, department, designation,
               topic_name, total_questions, correct_answers, score_percent,
               result, video_path, completed_at
        FROM viva_records 
        WHERE 1=1
    """
    params = []
    
    if department:
        query += " AND department = %s"
        params.append(department)
    
    if topic_id:
        query += " AND topic_id = %s"
        params.append(topic_id)
    
    if result_filter:
        query += " AND result = %s"
        params.append(result_filter)
    
    # Get total count
    count_query = query.replace("SELECT id, employee_id", "SELECT COUNT(*) as total")
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Get paginated results
    query += " ORDER BY completed_at DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    records = cursor.fetchall()
    
    # Format datetime
    for r in records:
        if r['completed_at']:
            r['completed_at'] = r['completed_at'].strftime('%Y-%m-%d %H:%M')
        r['has_video'] = r['video_path'] is not None
    
    conn.close()
    
    return jsonify({
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'records': records
    })


@viva_records_bp.route('/stats', methods=['GET'])
def get_viva_stats():
    """Get overall viva statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total records
    cursor.execute("SELECT COUNT(*) as total FROM viva_records")
    total = cursor.fetchone()['total']
    
    # Pass/Fail counts
    cursor.execute("""
        SELECT result, COUNT(*) as count 
        FROM viva_records 
        GROUP BY result
    """)
    result_counts = {r['result']: r['count'] for r in cursor.fetchall()}
    
    # Average score
    cursor.execute("SELECT AVG(score_percent) as avg_score FROM viva_records")
    avg_score = cursor.fetchone()['avg_score'] or 0
    
    # Records by department
    cursor.execute("""
        SELECT department, COUNT(*) as count, AVG(score_percent) as avg_score
        FROM viva_records 
        WHERE department IS NOT NULL AND department != ''
        GROUP BY department
        ORDER BY count DESC
        LIMIT 10
    """)
    by_department = cursor.fetchall()
    
    # Records by topic
    cursor.execute("""
        SELECT topic_name, COUNT(*) as count, AVG(score_percent) as avg_score
        FROM viva_records 
        WHERE topic_name IS NOT NULL AND topic_name != ''
        GROUP BY topic_name
        ORDER BY count DESC
        LIMIT 10
    """)
    by_topic = cursor.fetchall()
    
    # Recent records
    cursor.execute("""
        SELECT employee_name, topic_name, score_percent, result, completed_at
        FROM viva_records 
        ORDER BY completed_at DESC
        LIMIT 10
    """)
    recent = cursor.fetchall()
    for r in recent:
        if r['completed_at']:
            r['completed_at'] = r['completed_at'].strftime('%Y-%m-%d %H:%M')
    
    conn.close()
    
    return jsonify({
        'success': True,
        'total_vivas': total,
        'pass_count': result_counts.get('Pass', 0),
        'fail_count': result_counts.get('Fail', 0),
        'average_score': round(avg_score, 1),
        'by_department': by_department,
        'by_topic': by_topic,
        'recent_records': recent
    })
