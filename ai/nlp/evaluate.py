from ai.nlp.semantic import semantic_similarity

# Hindi keyword match function
def keyword_match(answer, expected_keywords):
    matched = sum(1 for kw in expected_keywords if kw in answer)
    return matched / len(expected_keywords) if expected_keywords else 0

# Combined evaluation function
def evaluate_answer(answer, expected_answer, expected_keywords):
    # Keyword score (0-1)
    kw_score = keyword_match(answer, expected_keywords)
    # Semantic similarity score (0-1)
    sem_score = semantic_similarity(answer, expected_answer)
    # Weighted final score (0-10)
    final_score = (0.4 * kw_score + 0.6 * sem_score) * 10
    return {
        'keyword_score': round(kw_score, 2),
        'semantic_score': round(sem_score, 2),
        'final_score': round(final_score, 2)
    }

# Example usage:
if __name__ == "__main__":
    ans = "स्ट्रिंगर मशीन तारों को जोड़ने का काम करती है।"
    exp = "स्ट्रिंगर मशीन का कार्य तारों को जोड़ना है।"
    keywords = ["स्ट्रिंगर", "तारों", "जोड़ना"]
    print(evaluate_answer(ans, exp, keywords))
