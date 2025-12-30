from sentence_transformers import SentenceTransformer, util

# Use a multilingual model that supports Hindi
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def semantic_similarity(answer, expected):
    # Both should be in Hindi
    emb_answer = model.encode(answer, convert_to_tensor=True)
    emb_expected = model.encode(expected, convert_to_tensor=True)
    score = util.pytorch_cos_sim(emb_answer, emb_expected).item()
    return score

# Example usage:
if __name__ == "__main__":
    ans = "स्ट्रिंगर मशीन तारों को जोड़ने का काम करती है।"
    exp = "स्ट्रिंगर मशीन का कार्य तारों को जोड़ना है।"
    print("Semantic similarity score:", semantic_similarity(ans, exp))
