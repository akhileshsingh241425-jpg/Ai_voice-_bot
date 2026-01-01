"""
Q&A Bank Management API Routes (New Structure)
- Questions per Training Topic
- Excel Upload
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import json

qa_bank_new_bp = Blueprint('qa_bank_new', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    import pymysql
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='ai_voice_bot_new',
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


@qa_bank_new_bp.route('/qa/topics-stats', methods=['GET'])
def get_topics_with_qa_stats():
    """Get all topics with Q&A count"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tt.id, tt.name, tt.is_common, tc.name as category_name,
               COUNT(q.id) as total_questions,
               SUM(CASE WHEN q.level = 1 THEN 1 ELSE 0 END) as easy,
               SUM(CASE WHEN q.level = 2 THEN 1 ELSE 0 END) as medium,
               SUM(CASE WHEN q.level = 3 THEN 1 ELSE 0 END) as hard
        FROM training_topic tt
        LEFT JOIN training_category tc ON tc.id = tt.category_id
        LEFT JOIN qa_bank_new q ON q.topic_id = tt.id AND q.is_active = TRUE
        WHERE tt.is_active = TRUE
        GROUP BY tt.id
        ORDER BY tc.name, tt.name
    """)
    topics = cursor.fetchall()
    
    # Get total
    cursor.execute("SELECT COUNT(*) as total FROM qa_bank_new WHERE is_active = TRUE")
    total = cursor.fetchone()['total']
    
    conn.close()
    return jsonify({'topics': topics, 'total_questions': total})


@qa_bank_new_bp.route('/qa/questions/<int:topic_id>', methods=['GET'])
def get_questions_for_topic(topic_id):
    """Get all questions for a training topic"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM qa_bank_new
        WHERE topic_id = %s AND is_active = TRUE
        ORDER BY level, id
    """, (topic_id,))
    questions = cursor.fetchall()
    
    # Get topic info
    cursor.execute("SELECT name FROM training_topic WHERE id = %s", (topic_id,))
    topic = cursor.fetchone()
    
    conn.close()
    return jsonify({
        'topic_id': topic_id,
        'topic_name': topic['name'] if topic else '',
        'total': len(questions),
        'questions': questions
    })


@qa_bank_new_bp.route('/qa/viva-questions/<int:topic_id>', methods=['GET'])
def get_viva_questions(topic_id):
    """Get random questions for viva with language filter"""
    import random
    
    count = request.args.get('count', 20, type=int)
    language = request.args.get('language', 'HI')  # HI or EN
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if questions exist in requested language
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM qa_bank_new 
        WHERE topic_id = %s AND language = %s AND is_active = TRUE
    """, (topic_id, language))
    lang_count = cursor.fetchone()['cnt']
    
    # Fallback to other language if no questions in requested language
    if lang_count == 0:
        language = 'EN' if language == 'HI' else 'HI'
    
    # Get questions by level - 40% Easy, 35% Medium, 25% Hard
    level1_count = int(count * 0.4)
    level2_count = int(count * 0.35)
    level3_count = count - level1_count - level2_count
    
    questions = []
    
    for level, needed in [(1, level1_count), (2, level2_count), (3, level3_count)]:
        cursor.execute("""
            SELECT id, question, expected_answer, level, language
            FROM qa_bank_new
            WHERE topic_id = %s AND level = %s AND language = %s AND is_active = TRUE
            ORDER BY RAND()
            LIMIT %s
        """, (topic_id, level, language, needed))
        questions.extend(cursor.fetchall())
    
    # If still not enough questions, get any questions from this topic
    if len(questions) < count:
        cursor.execute("""
            SELECT id, question, expected_answer, level, language
            FROM qa_bank_new
            WHERE topic_id = %s AND is_active = TRUE
            ORDER BY RAND()
            LIMIT %s
        """, (topic_id, count))
        questions = cursor.fetchall()
    
    random.shuffle(questions)
    conn.close()
    
    return jsonify({
        'topic_id': topic_id,
        'total': len(questions),
        'questions': questions[:count]
    })


@qa_bank_new_bp.route('/qa/upload', methods=['POST'])
def upload_qa_excel():
    """
    Upload Excel file with Q&A
    Expected columns: topic_name, question, expected_answer, level
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        import pandas as pd
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Read file
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        print(f"[QA Upload] Read {len(df)} rows, columns: {list(df.columns)}")
        
        # Validate columns
        required_cols = ['topic_name', 'question', 'expected_answer', 'level']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({'error': f'Missing columns: {missing}'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get topic mapping
        cursor.execute("SELECT id, name FROM training_topic")
        topics = cursor.fetchall()
        topic_map = {t['name'].lower().strip(): t['id'] for t in topics}
        
        success_count = 0
        error_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                topic_name = str(row['topic_name']).strip().lower()
                question = str(row['question']).strip()
                expected_answer = str(row['expected_answer']).strip()
                level = int(row['level']) if pd.notna(row['level']) else 1
                
                if not question or question == 'nan':
                    continue
                
                # Find topic ID
                topic_id = topic_map.get(topic_name)
                if not topic_id:
                    # Partial match
                    for t_name, t_id in topic_map.items():
                        if topic_name in t_name or t_name in topic_name:
                            topic_id = t_id
                            break
                
                if not topic_id:
                    errors.append(f"Row {idx+2}: Topic '{row['topic_name']}' not found")
                    error_count += 1
                    continue
                
                level = max(1, min(3, level))
                
                # Handle language - HI/EN format
                lang_value = str(row.get('language', 'HI')) if 'language' in df.columns else 'HI'
                lang_value = lang_value.strip().upper()
                if lang_value in ['HI', 'HINDI', 'H']:
                    language = 'HI'
                elif lang_value in ['EN', 'ENGLISH', 'E', 'ENG']:
                    language = 'EN'
                else:
                    language = 'HI'  # Default Hindi
                
                cursor.execute("""
                    INSERT INTO qa_bank_new (topic_id, question, expected_answer, level, language)
                    VALUES (%s, %s, %s, %s, %s)
                """, (topic_id, question, expected_answer, level, language))
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {idx+2}: {str(e)}")
                error_count += 1
        
        conn.commit()
        conn.close()
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Uploaded {success_count} questions',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:20]
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@qa_bank_new_bp.route('/qa/add', methods=['POST'])
def add_question():
    """Add single question"""
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO qa_bank_new (topic_id, question, expected_answer, level, language, keywords)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data.get('topic_id'),
        data.get('question'),
        data.get('expected_answer'),
        data.get('level', 1),
        data.get('language', 'Hindi'),
        data.get('keywords', '')
    ))
    
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'question_id': question_id})


@qa_bank_new_bp.route('/qa/delete/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Soft delete question"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE qa_bank_new SET is_active = FALSE WHERE id = %s", (question_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


@qa_bank_new_bp.route('/qa/clear-topic/<int:topic_id>', methods=['DELETE'])
def clear_topic_questions(topic_id):
    """Clear all questions for a topic"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE qa_bank_new SET is_active = FALSE WHERE topic_id = %s", (topic_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'deleted': affected})


@qa_bank_new_bp.route('/qa/upload-topic', methods=['POST'])
def upload_topic_qa_excel():
    """
    Upload Excel file for a SPECIFIC training topic
    Expected columns: question, expected_answer, level, language (HI/EN)
    Topic ID comes from form data
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided', 'success_count': 0, 'error_count': 1, 'errors': []}), 400
    
    topic_id = request.form.get('topic_id')
    if not topic_id:
        return jsonify({'success': False, 'message': 'Topic ID required', 'success_count': 0, 'error_count': 1, 'errors': []}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected', 'success_count': 0, 'error_count': 1, 'errors': []}), 400
    
    try:
        import pandas as pd
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Read file
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        print(f"[Topic QA Upload] Topic ID: {topic_id}, Read {len(df)} rows, columns: {list(df.columns)}")
        
        # Validate columns
        if 'question' not in df.columns or 'expected_answer' not in df.columns:
            return jsonify({'success': False, 'message': 'Missing required columns: question, expected_answer', 'success_count': 0, 'error_count': 1, 'errors': []}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        success_count = 0
        error_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                question = str(row['question']).strip()
                expected_answer = str(row['expected_answer']).strip()
                
                if not question or question == 'nan' or not expected_answer or expected_answer == 'nan':
                    continue
                
                # Level (default 1)
                level = 1
                if 'level' in df.columns and pd.notna(row.get('level')):
                    try:
                        level = int(row['level'])
                        level = max(1, min(3, level))
                    except:
                        level = 1
                
                # Language - HI/EN format
                language = 'HI'  # Default Hindi
                if 'language' in df.columns and pd.notna(row.get('language')):
                    lang_value = str(row['language']).strip().upper()
                    if lang_value in ['EN', 'ENGLISH', 'E', 'ENG']:
                        language = 'EN'
                    elif lang_value in ['HI', 'HINDI', 'H']:
                        language = 'HI'
                
                cursor.execute("""
                    INSERT INTO qa_bank_new (topic_id, question, expected_answer, level, language)
                    VALUES (%s, %s, %s, %s, %s)
                """, (topic_id, question, expected_answer, level, language))
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {idx+2}: {str(e)}")
                error_count += 1
        
        conn.commit()
        conn.close()
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Uploaded {success_count} questions for topic',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e), 'success_count': 0, 'error_count': 1, 'errors': [str(e)]}), 500
