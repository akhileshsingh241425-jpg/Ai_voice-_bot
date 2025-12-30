from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def evaluate_answer(answer, expected_answer, expected_keywords):
    if not answer or not expected_answer:
        return {'score': 0, 'passed': False}

    # Semantic similarity
    emb1 = model.encode(answer, convert_to_tensor=True)
    emb2 = model.encode(expected_answer, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(emb1, emb2).item()
    sim_score = int(similarity * 100)

    # Keyword check
    keyword_score = 0
    for kw in expected_keywords:
        if kw.lower() in answer.lower():
            keyword_score += 10

    total_score = sim_score + keyword_score
    passed = total_score >= 60
    return {'score': total_score, 'passed': passed, 'similarity': sim_score, 'keyword_score': keyword_score}
