"""
Conversational Voice Viva API
- Natural conversation style interview
- LLM generates follow-up questions based on user's answers
- All voice-based interaction
"""

from flask import Blueprint, request, jsonify
import requests
import re

chat_viva_bp = Blueprint('chat_viva', __name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:1b"

def get_topic_context(topic_id):
    """Get topic info and sample questions for context"""
    import pymysql
    conn = pymysql.connect(host='localhost', user='root', password='root', 
                          database='ai_voice_bot_new', port=3306)
    cursor = conn.cursor()
    
    # Get topic name
    cursor.execute('SELECT name FROM training_topic WHERE id = %s', (topic_id,))
    result = cursor.fetchone()
    topic_name = result[0] if result else 'General'
    
    # Get sample Q&A for context
    cursor.execute('''
        SELECT question, expected_answer FROM qa_bank_new 
        WHERE topic_id = %s LIMIT 20
    ''', (topic_id,))
    qa_pairs = cursor.fetchall()
    
    conn.close()
    
    context = f"Topic: {topic_name}\n\nKey concepts to cover:\n"
    for q, a in qa_pairs:
        context += f"- {q} -> {a}\n"
    
    return topic_name, context


@chat_viva_bp.route('/chat-viva/start', methods=['POST'])
def start_conversation():
    """Start a conversational viva - get first question"""
    data = request.json
    topic_id = data.get('topic_id')
    user_name = data.get('user_name', 'Candidate')
    language = data.get('language', 'Hindi')
    
    topic_name, context = get_topic_context(topic_id)
    
    # Generate opening question
    if language == 'Hindi':
        prompt = f"""You are conducting a friendly technical interview in Hindi about {topic_name}.
Start with a warm greeting and ask an open-ended question about their work.

Example opening:
"नमस्ते! मैं आपसे {topic_name} के बारे में कुछ बातें करना चाहता हूँ। सबसे पहले बताइए, आप IPQC में क्या-क्या काम करते हैं?"

Generate a similar friendly opening in Hindi (2-3 sentences max). Only output the greeting, nothing else."""
    else:
        prompt = f"""You are conducting a friendly technical interview about {topic_name}.
Start with a warm greeting and ask an open-ended question about their work.

Generate a friendly opening in English (2-3 sentences max). Only output the greeting, nothing else."""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 150}
            },
            timeout=30
        )
        response.raise_for_status()
        opening = response.json().get("response", "").strip()
        
        # Fallback
        if len(opening) < 10:
            opening = f"नमस्ते {user_name}! मैं आपसे {topic_name} के बारे में बात करना चाहता हूँ। सबसे पहले बताइए, आप इस area में क्या-क्या काम करते हैं?"
        
        return jsonify({
            'message': opening,
            'topic_name': topic_name,
            'turn': 1
        })
    except Exception as e:
        return jsonify({
            'message': f"नमस्ते {user_name}! आइए {topic_name} के बारे में बात करते हैं। बताइए, आप क्या-क्या काम करते हैं?",
            'topic_name': topic_name,
            'turn': 1
        })


@chat_viva_bp.route('/chat-viva/respond', methods=['POST'])
def respond_to_user():
    """Generate follow-up based on user's answer"""
    data = request.json
    topic_id = data.get('topic_id')
    user_answer = data.get('user_answer', '')
    conversation_history = data.get('history', [])
    turn = data.get('turn', 1)
    language = data.get('language', 'Hindi')
    max_turns = data.get('max_turns', 8)
    
    topic_name, context = get_topic_context(topic_id)
    
    # Check if we should end
    if turn >= max_turns:
        return generate_closing(topic_name, conversation_history, language)
    
    # Build conversation context
    history_text = ""
    for h in conversation_history[-6:]:  # Last 6 exchanges
        history_text += f"Interviewer: {h.get('ai', '')}\n"
        history_text += f"Candidate: {h.get('user', '')}\n"
    
    # Generate follow-up
    if language == 'Hindi':
        prompt = f"""You are conducting a technical interview about {topic_name} in Hindi.

{context}

Conversation so far:
{history_text}
Candidate's latest answer: {user_answer}

Based on their answer, generate ONE follow-up question that:
1. Explores deeper into what they mentioned
2. OR moves to a related concept they haven't discussed
3. Is conversational and friendly (like "अच्छा! और बताओ..." or "hmm, interesting! तो...")
4. Tests their practical knowledge

Keep it short (1-2 sentences). Only output the follow-up question in Hindi, nothing else."""
    else:
        prompt = f"""You are conducting a technical interview about {topic_name}.

{context}

Conversation so far:
{history_text}
Candidate's latest answer: {user_answer}

Generate ONE short follow-up question (1-2 sentences) that explores their knowledge further.
Only output the question, nothing else."""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 100}
            },
            timeout=30
        )
        response.raise_for_status()
        follow_up = response.json().get("response", "").strip()
        
        # Clean up
        follow_up = follow_up.split('\n')[0].strip()
        
        if len(follow_up) < 10:
            follow_up = "अच्छा! और कुछ बताओ इसके बारे में?"
        
        return jsonify({
            'message': follow_up,
            'turn': turn + 1,
            'continue': True
        })
    except Exception as e:
        return jsonify({
            'message': "अच्छा! और बताओ, इसमें कौन-कौन सी चीज़ें important हैं?",
            'turn': turn + 1,
            'continue': True
        })


def generate_closing(topic_name, history, language):
    """Generate closing message and evaluate"""
    
    history_text = ""
    for h in history:
        history_text += f"Q: {h.get('ai', '')}\nA: {h.get('user', '')}\n"
    
    # Evaluate overall understanding
    eval_prompt = f"""Evaluate this candidate's knowledge about {topic_name} based on this conversation:

{history_text}

Rate their understanding:
1. SCORE: 0-100 (overall knowledge percentage)
2. STRONG_AREAS: What they know well (comma separated)
3. WEAK_AREAS: What they need to learn (comma separated)
4. SUMMARY: One line summary in Hindi

Format exactly like:
SCORE: 75
STRONG_AREAS: EL testing, defect identification
WEAK_AREAS: calibration process, specifications
SUMMARY: Candidate has good practical knowledge but needs to learn specifications."""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
                "prompt": eval_prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 200}
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json().get("response", "")
        
        # Parse result
        score = 50
        score_match = re.search(r'SCORE:\s*(\d+)', result)
        if score_match:
            score = int(score_match.group(1))
        
        strong = ""
        strong_match = re.search(r'STRONG_AREAS:\s*(.+)', result)
        if strong_match:
            strong = strong_match.group(1).strip()
        
        weak = ""
        weak_match = re.search(r'WEAK_AREAS:\s*(.+)', result)
        if weak_match:
            weak = weak_match.group(1).strip()
        
        summary = ""
        summary_match = re.search(r'SUMMARY:\s*(.+)', result)
        if summary_match:
            summary = summary_match.group(1).strip()
        
        # Generate closing message
        if score >= 70:
            closing = f"बहुत बढ़िया! आपकी {topic_name} की जानकारी काफी अच्छी है। बातचीत के लिए धन्यवाद!"
        elif score >= 40:
            closing = f"अच्छा रहा! आपको {topic_name} की basic जानकारी है। थोड़ा और पढ़ाई करें। धन्यवाद!"
        else:
            closing = f"धन्यवाद! {topic_name} के बारे में और study करें। Practice से सब आ जाएगा!"
        
        return jsonify({
            'message': closing,
            'continue': False,
            'evaluation': {
                'score': score,
                'strong_areas': strong,
                'weak_areas': weak,
                'summary': summary
            }
        })
    except Exception as e:
        return jsonify({
            'message': "बातचीत के लिए धन्यवाद! आपने अच्छा किया।",
            'continue': False,
            'evaluation': {
                'score': 50,
                'strong_areas': 'General knowledge',
                'weak_areas': 'Need more assessment',
                'summary': 'Evaluation completed'
            }
        })


@chat_viva_bp.route('/chat-viva/evaluate-final', methods=['POST'])
def evaluate_final():
    """Get final evaluation of the conversation"""
    data = request.json
    topic_id = data.get('topic_id')
    history = data.get('history', [])
    language = data.get('language', 'Hindi')
    
    topic_name, _ = get_topic_context(topic_id)
    return generate_closing(topic_name, history, language)
