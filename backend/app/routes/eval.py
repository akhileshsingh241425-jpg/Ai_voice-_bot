from flask import Blueprint, request, jsonify

eval_bp = Blueprint('eval', __name__)

# Lazy loading - import only when needed
def get_evaluate_function():
    from ai.nlp.evaluate import evaluate_answer
    return evaluate_answer

@eval_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.json
    answer = data.get('answer', '')
    expected_answer = data.get('expected_answer', '')
    expected_keywords = data.get('expected_keywords', [])
    
    try:
        evaluate_answer = get_evaluate_function()
        result = evaluate_answer(answer, expected_answer, expected_keywords)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Evaluation failed: {str(e)}'}), 500
