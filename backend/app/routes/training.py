"""
Training Management API Routes
- Departments, Categories, Topics
- Training Records
"""

from flask import Blueprint, request, jsonify
import pymysql

training_bp = Blueprint('training', __name__, url_prefix='/training')


def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='ai_voice_bot_new',
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


# ============================================
# DEPARTMENT ROUTES
# ============================================

@training_bp.route('/departments', methods=['GET'])
def get_departments():
    """Get all departments with topic counts"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.*, 
               COUNT(DISTINCT dtm.topic_id) as topic_count,
               COUNT(DISTINCT e.id) as employee_count
        FROM department_new d
        LEFT JOIN department_topic_mapping dtm ON dtm.department_id = d.id
        LEFT JOIN employee_new e ON e.department_id = d.id
        WHERE d.is_active = TRUE
        GROUP BY d.id
        ORDER BY d.name
    """)
    departments = cursor.fetchall()
    conn.close()
    
    return jsonify({'departments': departments})


# ============================================
# TRAINING CATEGORY ROUTES
# ============================================

@training_bp.route('/training-categories', methods=['GET'])
def get_categories():
    """Get all training categories"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tc.*, COUNT(tt.id) as topic_count
        FROM training_category tc
        LEFT JOIN training_topic tt ON tt.category_id = tc.id
        WHERE tc.is_active = TRUE
        GROUP BY tc.id
        ORDER BY tc.name
    """)
    categories = cursor.fetchall()
    conn.close()
    
    return jsonify({'categories': categories})


# ============================================
# TRAINING TOPIC ROUTES
# ============================================

@training_bp.route('/training-topics', methods=['GET'])
def get_topics():
    """Get all training topics with optional filters"""
    department_id = request.args.get('department_id', type=int)
    category_id = request.args.get('category_id', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT DISTINCT tt.*, tc.name as category_name,
               (SELECT COUNT(*) FROM qa_bank_new q WHERE q.topic_id = tt.id AND q.is_active = TRUE) as question_count
        FROM training_topic tt
        LEFT JOIN training_category tc ON tc.id = tt.category_id
        LEFT JOIN department_topic_mapping dtm ON dtm.topic_id = tt.id
        WHERE tt.is_active = TRUE
    """
    params = []
    
    if department_id:
        query += " AND dtm.department_id = %s"
        params.append(department_id)
    
    if category_id:
        query += " AND tt.category_id = %s"
        params.append(category_id)
    
    query += " ORDER BY tc.name, tt.name"
    
    cursor.execute(query, params)
    topics = cursor.fetchall()
    conn.close()
    
    return jsonify({'topics': topics})


@training_bp.route('/training-topics/<int:topic_id>', methods=['GET'])
def get_topic_detail(topic_id):
    """Get single topic with all details"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tt.*, tc.name as category_name
        FROM training_topic tt
        LEFT JOIN training_category tc ON tc.id = tt.category_id
        WHERE tt.id = %s
    """, (topic_id,))
    topic = cursor.fetchone()
    
    if not topic:
        conn.close()
        return jsonify({'error': 'Topic not found'}), 404
    
    # Get departments for this topic
    cursor.execute("""
        SELECT d.id, d.name, d.code
        FROM department_new d
        JOIN department_topic_mapping dtm ON dtm.department_id = d.id
        WHERE dtm.topic_id = %s
    """, (topic_id,))
    topic['departments'] = cursor.fetchall()
    
    # Get question count by level
    cursor.execute("""
        SELECT level, COUNT(*) as count
        FROM qa_bank_new
        WHERE topic_id = %s AND is_active = TRUE
        GROUP BY level
    """, (topic_id,))
    levels = cursor.fetchall()
    topic['questions_by_level'] = {l['level']: l['count'] for l in levels}
    
    conn.close()
    return jsonify({'topic': topic})


@training_bp.route('/training-topics', methods=['POST'])
def create_topic():
    """Create new training topic"""
    data = request.json
    name = data.get('name')
    category_id = data.get('category_id')
    department_ids = data.get('department_ids', [])
    is_common = data.get('is_common', False)
    
    if not name or not category_id:
        return jsonify({'error': 'Name and category required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common, description)
        VALUES (%s, %s, %s, %s)
    """, (name, category_id, is_common, data.get('description', '')))
    
    topic_id = cursor.lastrowid
    
    # Add department mappings
    for dept_id in department_ids:
        cursor.execute("""
            INSERT INTO department_topic_mapping (department_id, topic_id)
            VALUES (%s, %s)
        """, (dept_id, topic_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'topic_id': topic_id})


# ============================================
# EMPLOYEE ROUTES
# ============================================

@training_bp.route('/employees', methods=['GET'])
def get_employees():
    """Get all employees with department info"""
    department_id = request.args.get('department_id', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT e.*, d.name as department_name
        FROM employee_new e
        LEFT JOIN department_new d ON d.id = e.department_id
        WHERE e.is_active = TRUE
    """
    params = []
    
    if department_id:
        query += " AND e.department_id = %s"
        params.append(department_id)
    
    query += " ORDER BY e.name"
    
    cursor.execute(query, params)
    employees = cursor.fetchall()
    conn.close()
    
    return jsonify({'employees': employees})


@training_bp.route('/employees/<int:emp_id>', methods=['GET'])
def get_employee_detail(emp_id):
    """Get employee with training records and viva history"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.*, d.name as department_name
        FROM employee_new e
        LEFT JOIN department_new d ON d.id = e.department_id
        WHERE e.id = %s
    """, (emp_id,))
    employee = cursor.fetchone()
    
    if not employee:
        conn.close()
        return jsonify({'error': 'Employee not found'}), 404
    
    # Get training records
    cursor.execute("""
        SELECT tr.*, tt.name as topic_name
        FROM training_record tr
        LEFT JOIN training_topic tt ON tt.id = tr.topic_id
        WHERE tr.employee_id = %s
        ORDER BY tr.training_date DESC
    """, (emp_id,))
    employee['training_records'] = cursor.fetchall()
    
    # Get viva results
    cursor.execute("""
        SELECT vr.*, tt.name as topic_name
        FROM viva_result_new vr
        LEFT JOIN training_topic tt ON tt.id = vr.topic_id
        WHERE vr.employee_id = %s
        ORDER BY vr.created_at DESC
    """, (emp_id,))
    employee['viva_results'] = cursor.fetchall()
    
    conn.close()
    return jsonify({'employee': employee})


@training_bp.route('/employees', methods=['POST'])
def create_employee():
    """Create new employee"""
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO employee_new (emp_id, name, department_id, designation, phone, email)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data.get('emp_id'),
        data.get('name'),
        data.get('department_id'),
        data.get('designation'),
        data.get('phone'),
        data.get('email')
    ))
    
    employee_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'employee_id': employee_id})


# ============================================
# TRAINING RECORD ROUTES
# ============================================

@training_bp.route('/training-records', methods=['GET'])
def get_training_records():
    """Get training records with filters"""
    employee_id = request.args.get('employee_id', type=int)
    topic_id = request.args.get('topic_id', type=int)
    status = request.args.get('status')
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT tr.*, e.name as employee_name, e.emp_id,
               tt.name as topic_name, d.name as department_name
        FROM training_record tr
        LEFT JOIN employee_new e ON e.id = tr.employee_id
        LEFT JOIN training_topic tt ON tt.id = tr.topic_id
        LEFT JOIN department_new d ON d.id = e.department_id
        WHERE 1=1
    """
    params = []
    
    if employee_id:
        query += " AND tr.employee_id = %s"
        params.append(employee_id)
    
    if topic_id:
        query += " AND tr.topic_id = %s"
        params.append(topic_id)
    
    if status:
        query += " AND tr.status = %s"
        params.append(status)
    
    query += " ORDER BY tr.training_date DESC LIMIT 100"
    
    cursor.execute(query, params)
    records = cursor.fetchall()
    conn.close()
    
    return jsonify({'records': records})


@training_bp.route('/training-records', methods=['POST'])
def create_training_record():
    """Record training completion for employee"""
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO training_record 
        (employee_id, topic_id, training_date, trainer_name, training_type, status, remarks)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get('employee_id'),
        data.get('topic_id'),
        data.get('training_date'),
        data.get('trainer_name'),
        data.get('training_type', 'New Joiner'),
        data.get('status', 'Completed'),
        data.get('remarks')
    ))
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'record_id': record_id})


# ============================================
# DASHBOARD STATS
# ============================================

@training_bp.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # Department-wise employee count
    cursor.execute("""
        SELECT d.name, COUNT(e.id) as count
        FROM department_new d
        LEFT JOIN employee_new e ON e.department_id = d.id
        GROUP BY d.id
    """)
    stats['employees_by_dept'] = cursor.fetchall()
    
    # Training records this month
    cursor.execute("""
        SELECT COUNT(*) as count FROM training_record
        WHERE MONTH(training_date) = MONTH(CURRENT_DATE)
        AND YEAR(training_date) = YEAR(CURRENT_DATE)
    """)
    stats['trainings_this_month'] = cursor.fetchone()['count']
    
    # Viva results this month
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN passed = TRUE THEN 1 ELSE 0 END) as passed,
            SUM(CASE WHEN passed = FALSE THEN 1 ELSE 0 END) as failed
        FROM viva_result_new
        WHERE MONTH(created_at) = MONTH(CURRENT_DATE)
        AND YEAR(created_at) = YEAR(CURRENT_DATE)
    """)
    stats['viva_this_month'] = cursor.fetchone()
    
    # Pending vivas (training completed but no viva)
    cursor.execute("""
        SELECT COUNT(*) as count FROM training_record
        WHERE status = 'Pending Viva'
    """)
    stats['pending_vivas'] = cursor.fetchone()['count']
    
    # Total counts
    cursor.execute("SELECT COUNT(*) as c FROM employee_new WHERE is_active = TRUE")
    stats['total_employees'] = cursor.fetchone()['c']
    
    cursor.execute("SELECT COUNT(*) as c FROM training_topic WHERE is_active = TRUE")
    stats['total_topics'] = cursor.fetchone()['c']
    
    cursor.execute("SELECT COUNT(*) as c FROM qa_bank_new WHERE is_active = TRUE")
    stats['total_questions'] = cursor.fetchone()['c']
    
    conn.close()
    return jsonify(stats)
