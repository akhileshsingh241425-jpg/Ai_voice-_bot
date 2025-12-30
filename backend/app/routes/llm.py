from flask import Blueprint, request, jsonify

llm_bp = Blueprint('llm', __name__)

# Lazy loading - import only when needed (using Ollama now)
def get_llm_functions():
    from ai.llm.ollama_llm import generate_next_question, evaluate_user_answer
    return generate_next_question, evaluate_user_answer

@llm_bp.route('/next_question', methods=['POST'])
def next_question():
    """
    Evaluate user's answer and generate the next interview question.
    If machine_id is provided, questions will be based on uploaded study material.
    
    Expects JSON: { 
        "topic": "...", 
        "previous_question": "...", 
        "user_answer": "...", 
        "language": "Hindi",
        "machine_id": 1  # Optional - for context-based questions
    }
    Returns JSON: { 
        "next_question": "...", 
        "evaluation": { "is_relevant": bool, "score": int, "feedback": str },
        "using_study_material": bool
    }
    """
    print("[LLM] Received next_question request")
    data = request.json
    topic = data.get('topic', '')
    previous_question = data.get('previous_question', '')
    user_answer = data.get('user_answer', '')
    language = data.get('language', 'Hindi')
    machine_id = data.get('machine_id')  # Optional
    
    print(f"[LLM] Topic: {topic}, Language: {language}, Machine ID: {machine_id}")
    print(f"[LLM] User answer: {user_answer[:100]}...")

    if not topic or not user_answer:
        return jsonify({'error': 'topic and user_answer are required'}), 400

    try:
        generate_fn, evaluate_fn = get_llm_functions()
        
        # First, evaluate the answer (with study material if machine_id provided)
        print("[LLM] Evaluating answer...")
        evaluation = evaluate_fn(topic, previous_question, user_answer, language, machine_id)
        print(f"[LLM] Evaluation result: {evaluation}")
        
        # If answer is not relevant, ask to answer again (don't generate new question)
        if not evaluation.get('is_relevant', True) and evaluation.get('score', 50) < 20:
            print("[LLM] Answer not relevant, asking to repeat")
            return jsonify({
                'next_question': previous_question,  # Repeat the same question
                'evaluation': evaluation,
                'repeat': True,
                'using_study_material': False
            })
        
        # Generate next question (with study material context if machine_id provided)
        print("[LLM] Generating next question...")
        next_q = generate_fn(topic, previous_question, user_answer, language, machine_id)
        print(f"[LLM] Next question: {next_q}")
        
        # Check if study material was used
        using_study_material = False
        if machine_id:
            from ai.llm.ollama_llm import get_study_material_for_machine
            study_content = get_study_material_for_machine(machine_id)
            using_study_material = len(study_content.strip()) > 50
        
        return jsonify({
            'next_question': next_q,
            'evaluation': evaluation,
            'repeat': False,
            'using_study_material': using_study_material
        })
    except Exception as e:
        print(f"[LLM] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'LLM generation failed: {str(e)}'}), 500

@llm_bp.route('/evaluate_answer', methods=['POST'])
def evaluate_answer():
    """
    Only evaluate the answer without generating next question.
    Expects JSON: { "topic": "...", "question": "...", "user_answer": "...", "language": "Hindi" }
    Returns JSON: { "is_relevant": bool, "score": int, "feedback": str, "reason": str }
    """
    data = request.json
    topic = data.get('topic', '')
    question = data.get('question', '')
    user_answer = data.get('user_answer', '')
    language = data.get('language', 'Hindi')

    if not topic or not question or not user_answer:
        return jsonify({'error': 'topic, question, and user_answer are required'}), 400

    try:
        _, evaluate_fn = get_llm_functions()
        evaluation = evaluate_fn(topic, question, user_answer, language)
        return jsonify(evaluation)
    except Exception as e:
        return jsonify({'error': f'Evaluation failed: {str(e)}'}), 500


@llm_bp.route('/generate_viva_questions', methods=['POST'])
def generate_viva_questions():
    """
    Generate all questions for a viva from study material OR LLM knowledge.
    If no study material, uses machine/department name to generate relevant questions.
    Expects JSON: { "machine_id": 1, "num_questions": 15, "language": "Hindi" }
    Returns JSON: { "questions": [...], "total": 15 }
    """
    from ai.llm.ollama_llm import generate_questions_for_department
    from app.models.models import Machine
    
    data = request.json
    machine_id = data.get('machine_id')
    num_questions = data.get('num_questions', 15)
    language = data.get('language', 'Hindi')
    
    if not machine_id:
        return jsonify({'error': 'machine_id is required'}), 400
    
    # Get machine name for department-based questions
    machine = Machine.query.get(machine_id)
    machine_name = machine.name if machine else "Solar Panel Manufacturing"
    
    try:
        print(f"[LLM] Generating {num_questions} questions for machine {machine_id} ({machine_name})")
        questions = generate_questions_for_department(machine_id, machine_name, num_questions, language)
        print(f"[LLM] Generated {len(questions)} questions")
        return jsonify({
            'questions': questions,
            'total': len(questions)
        })
    except Exception as e:
        print(f"[LLM] Error generating questions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate questions: {str(e)}'}), 500


@llm_bp.route('/evaluate_with_answer', methods=['POST'])
def evaluate_with_answer():
    """
    Evaluate answer against expected answer and provide correct answer if wrong.
    Expects JSON: { 
        "question": "...", 
        "user_answer": "...", 
        "expected_answer": "...",
        "language": "Hindi" 
    }
    """
    from ai.llm.ollama_llm import evaluate_with_correct_answer
    
    data = request.json
    question = data.get('question', '')
    user_answer = data.get('user_answer', '')
    expected_answer = data.get('expected_answer', '')
    language = data.get('language', 'Hindi')
    topic = data.get('topic', 'General')
    
    print(f"[LLM EVALUATION] Question: {question[:50]}...")
    print(f"[LLM EVALUATION] User Answer: {user_answer}")
    print(f"[LLM EVALUATION] Expected: {expected_answer[:50]}...")
    
    if not question or not expected_answer:
        return jsonify({'error': 'question and expected_answer are required'}), 400
    
    try:
        print("[LLM EVALUATION] Calling Ollama LLM (gemma3:1b)...")
        result = evaluate_with_correct_answer(topic, question, user_answer, expected_answer, language)
        print(f"[LLM EVALUATION] ✅ Score: {result.get('score')}, Correct: {result.get('is_correct')}")
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Evaluation failed: {str(e)}'}), 500


@llm_bp.route('/get_welcome', methods=['POST'])
def get_welcome():
    """Get welcome message for viva."""
    from ai.llm.ollama_llm import get_welcome_message
    
    data = request.json
    candidate_name = data.get('candidate_name', 'Candidate')
    machine_name = data.get('machine_name', 'Machine')
    language = data.get('language', 'Hindi')
    
    message = get_welcome_message(candidate_name, machine_name, language)
    return jsonify({'message': message})


@llm_bp.route('/get_summary', methods=['POST'])
def get_summary():
    """Get viva summary with improvements."""
    from ai.llm.ollama_llm import get_viva_summary
    
    data = request.json
    questions_asked = data.get('questions', [])
    language = data.get('language', 'Hindi')
    
    summary = get_viva_summary(questions_asked, language)
    return jsonify(summary)
