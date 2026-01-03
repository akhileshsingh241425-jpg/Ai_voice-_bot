"""
Google Gemini API Integration for Production
FREE API with high quota - works on production server
"""

import os
import re
import google.generativeai as genai

# Configure API key from environment
API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDu9gVGZdCVVq_S0XYHuZJFVp3i9gKkdJo')  # Free tier
genai.configure(api_key=API_KEY)

def evaluate_with_correct_answer(topic: str, question: str, user_answer: str, expected_answer: str, language: str = "Hindi") -> dict:
    """
    Evaluate user answer using Google Gemini API - works in production
    """
    if not user_answer or len(user_answer.strip()) < 3:
        return {
            "is_correct": False,
            "score": 0,
            "feedback": "कृपया जवाब दें।" if "hindi" in language.lower() else "Please answer.",
            "correct_answer": expected_answer,
            "user_said": user_answer
        }
    
    # Improved multilingual semantic matching prompt
    prompt = f"""You are an EXPERT evaluator checking if two answers have the SAME MEANING.

**CRITICAL RULES:**
1. IGNORE language differences (Hindi, English, Hinglish - ALL are acceptable)
2. IGNORE spelling mistakes, grammar errors, pronunciation variations
3. IGNORE word order differences
4. CHECK ONLY if the CORE CONCEPT and MEANING match
5. Different words with SAME meaning = CORRECT answer
6. Synonyms and paraphrasing = CORRECT if meaning matches
7. Focus on TECHNICAL CORRECTNESS of concept, not exact wording

**Examples of CORRECT answers (different words, same meaning):**
- "सूर्य की रोशनी से पौधे भोजन बनाते हैं" = "Plants make food using sunlight" = "Photosynthesis" ✅
- "Safety goggles पहनना जरूरी है" = "We must wear safety glasses" = "Eye protection required" ✅
- "Machine को oil लगाना चाहिए" = "Lubricate the machine" = "Apply oil for maintenance" ✅

**Question:** {question}

**Reference Answer (Expected):** {expected_answer}

**Candidate's Answer:** {user_answer}

**YOUR TASK:**
Compare the MEANING and TECHNICAL CONCEPT. Do they mean the SAME thing?
- If candidate mentioned the KEY POINTS in ANY language → HIGH SCORE
- If candidate explained the concept differently but correctly → HIGH SCORE  
- Only give LOW SCORE if the concept/meaning is actually WRONG or completely different

**OUTPUT FORMAT (strictly follow):**
MATCH: [YES/PARTIAL/NO]
SCORE: [0-100 number only]
FEEDBACK: [One short encouraging line in {language}]

**SCORING GUIDE:**
- 90-100: Same meaning, all key points covered (even if different words/language)
- 70-89: Same main concept, minor details missing but technically correct
- 40-69: Partially correct, has some correct key points
- 0-39: Wrong concept or completely different/irrelevant

Now evaluate:"""

    try:
        # Use Gemini 1.5 Flash (fastest, free tier)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=150,
            )
        )
        
        result = response.text
        result_upper = result.upper()
        
        # Parse response
        is_match = False
        is_partial = False
        
        if "MATCH:" in result_upper:
            match_line = result_upper.split("MATCH:")[-1].split("\n")[0].strip()
            is_match = "YES" in match_line
            is_partial = "PARTIAL" in match_line
        
        # Extract score
        score = 50  # default
        score_match = re.search(r'SCORE:\s*(\d+)', result, re.IGNORECASE)
        if score_match:
            score = min(100, max(0, int(score_match.group(1))))
        else:
            if is_match:
                score = 85
            elif is_partial:
                score = 55
            else:
                score = 25
        
        # Extract feedback
        feedback = "जवाब का मूल्यांकन हो गया।"
        feedback_match = re.search(r'FEEDBACK:\s*(.+)', result, re.IGNORECASE | re.DOTALL)
        if feedback_match:
            feedback_text = feedback_match.group(1).strip()
            feedback = feedback_text.split('\n')[0].strip()
        
        # Determine correctness
        is_correct = score >= 70
        is_partial_final = (score >= 40 and score < 70) or is_partial
        
        print(f"[GEMINI EVALUATION] Score: {score}, Correct: {is_correct}, Partial: {is_partial_final}")
        
        return {
            "is_correct": is_correct,
            "is_partial": is_partial_final,
            "score": score,
            "feedback": feedback,
            "correct_answer": expected_answer if not is_correct else None,
            "user_said": user_answer
        }
        
    except Exception as e:
        print(f"[GEMINI ERROR] {str(e)}")
        # Fallback: simple text matching
        user_lower = user_answer.lower()
        expected_lower = expected_answer.lower()
        
        # Check for keyword overlap
        user_words = set(user_lower.split())
        expected_words = set(expected_lower.split())
        common_words = user_words & expected_words
        overlap_percent = (len(common_words) / len(expected_words)) * 100 if expected_words else 0
        
        score = min(100, int(overlap_percent * 1.2))
        is_correct = score >= 70
        is_partial = score >= 40 and score < 70
        
        return {
            "is_correct": is_correct,
            "is_partial": is_partial,
            "score": score,
            "feedback": "Network issue - basic matching used" if language == "English" else "नेटवर्क समस्या - बेसिक मैचिंग",
            "correct_answer": expected_answer if not is_correct else None,
            "user_said": user_answer
        }
