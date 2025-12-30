"""
Ollama LLM Integration
- Generates follow-up questions based on user's answer and topic.
- Evaluates if answer is relevant or just random noise/song
- Works like Jarvis: contextual, intelligent, interview-style questions.
- Uses local Ollama server (no internet required after model download)
"""

import requests
import json
import re
import time

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:1b"

class OllamaLLM:
    def __init__(self, model_name=MODEL_NAME):
        """
        Initialize Ollama LLM for local inference.
        Ollama server must be running (starts automatically with Ollama app).
        """
        self.model_name = model_name
    
    def evaluate_answer(self, topic: str, question: str, user_answer: str, language: str = "Hindi", study_context: str = None) -> dict:
        """
        Evaluate if the user's answer is relevant to the question.
        If study_context is provided, evaluates answer against that content.
        Returns: {
            "is_relevant": bool,
            "score": 0-100,
            "feedback": str,
            "reason": str
        }
        """
        # Quick checks for obviously bad answers
        if not user_answer or len(user_answer.strip()) < 5:
            return {
                "is_relevant": False,
                "score": 0,
                "feedback": "कृपया पूरा जवाब दें।" if "hindi" in language.lower() else "Please provide a complete answer.",
                "reason": "Answer too short"
            }
        
        # Check for gibberish/random text patterns
        words = user_answer.split()
        if len(words) < 2:
            return {
                "is_relevant": False,
                "score": 0,
                "feedback": "जवाब बहुत छोटा है, विस्तार से बताएं।" if "hindi" in language.lower() else "Answer is too short, please elaborate.",
                "reason": "Single word answer"
            }
        
        # Build evaluation prompt - with or without study material
        if study_context and len(study_context.strip()) > 50:
            # Evaluate against study material content
            context_snippet = study_context[:2500]  # Limit context
            eval_prompt = f"""You are evaluating a candidate's answer based ONLY on the provided study material.

=== STUDY MATERIAL (Correct Information Source) ===
{context_snippet}
=== END STUDY MATERIAL ===

Question Asked: {question}
Candidate's Answer: {user_answer}

Evaluate STRICTLY based on the study material above:
1. Is the answer CORRECT according to the study material?
2. Does the answer contain information that matches the study material?
3. Is it a genuine attempt to answer (not a song, random words)?

IMPORTANT: Only give high scores if the answer matches content from the study material.
If the answer has wrong information not in study material, give low score.

Respond in this EXACT format (no extra text):
RELEVANT: YES or NO
SCORE: 0-100
REASON: one line explanation comparing to study material"""
        else:
            # General evaluation without study material
            eval_prompt = f"""You are evaluating a candidate's answer in a technical interview.

Topic: {topic}
Question: {question}
Candidate's Answer: {user_answer}

Evaluate strictly:
1. Is this answer RELEVANT to the question? (not a song, random words, or unrelated text)
2. Does it show ANY understanding of the topic?
3. Is it a genuine attempt to answer?

Respond in this EXACT format (no extra text):
RELEVANT: YES or NO
SCORE: 0-100
REASON: one line explanation"""

        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": self.model_name,
                    "prompt": eval_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Low temperature for consistent evaluation
                        "num_predict": 80
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json().get("response", "").strip()
            
            # Parse the response
            is_relevant = "YES" in result.upper().split("RELEVANT:")[-1].split("\n")[0] if "RELEVANT:" in result.upper() else False
            
            # Extract score
            score = 50  # default
            score_match = re.search(r'SCORE:\s*(\d+)', result, re.IGNORECASE)
            if score_match:
                score = min(100, max(0, int(score_match.group(1))))
            
            # Extract reason
            reason = "Evaluation complete"
            reason_match = re.search(r'REASON:\s*(.+)', result, re.IGNORECASE)
            if reason_match:
                reason = reason_match.group(1).strip()
            
            # Generate appropriate feedback based on score
            if study_context:
                # Feedback specific to study material evaluation
                if score >= 70:
                    feedback = "बिल्कुल सही! Study material के अनुसार सही जवाब।" if "hindi" in language.lower() else "Correct! Your answer matches the study material."
                elif score >= 40:
                    feedback = "आंशिक रूप से सही। Material में और जानकारी है।" if "hindi" in language.lower() else "Partially correct. The material has more details."
                elif is_relevant:
                    feedback = "सही direction में है, लेकिन material के अनुसार check करें।" if "hindi" in language.lower() else "Right direction, but verify with the material."
                else:
                    feedback = "यह जवाब study material से match नहीं कर रहा।" if "hindi" in language.lower() else "This answer doesn't match the study material."
            else:
                if score >= 70:
                    feedback = "बहुत अच्छा! आगे बढ़ते हैं।" if "hindi" in language.lower() else "Great answer! Let's continue."
                elif score >= 40:
                    feedback = "ठीक है, लेकिन और detail दे सकते थे।" if "hindi" in language.lower() else "Okay, but could be more detailed."
                elif is_relevant:
                    feedback = "जवाब सही direction में है।" if "hindi" in language.lower() else "Answer is in the right direction."
                else:
                    feedback = "यह जवाब question से related नहीं लग रहा। कृपया question का जवाब दें।" if "hindi" in language.lower() else "This doesn't seem related to the question. Please answer the question."
            
            return {
                "is_relevant": is_relevant,
                "score": score,
                "feedback": feedback,
                "reason": reason
            }
            
        except Exception as e:
            # Fallback - be lenient if LLM fails
            return {
                "is_relevant": True,
                "score": 50,
                "feedback": "चलो आगे बढ़ते हैं।" if "hindi" in language.lower() else "Let's continue.",
                "reason": f"Evaluation fallback: {str(e)}"
            }
    
    def generate_followup_question(self, topic: str, previous_question: str, user_answer: str, language: str = "Hindi", study_context: str = None, training_prompt: str = None) -> str:
        """
        Generate a follow-up question based on user's answer and topic.
        If study_context is provided, questions will be strictly based on that material.
        If training_prompt is provided, includes few-shot examples for better quality.
        Works like Jarvis: contextual, intelligent, interview-style.
        """
        
        # Build context-aware prompt
        if study_context and len(study_context.strip()) > 50:
            # Use study material as context - questions must be from this material only
            context_snippet = study_context[:3000]  # Limit context to avoid token overflow
            
            # Include training prompt if available
            training_section = ""
            if training_prompt:
                training_section = f"\n{training_prompt}\n"
            
            prompt = f"""You are an expert technical interviewer conducting a viva/interview.
You MUST ask questions ONLY from the given study material. Do NOT use any external knowledge.
{training_section}
=== STUDY MATERIAL (Use ONLY this for questions) ===
{context_snippet}
=== END STUDY MATERIAL ===

Topic: {topic}
Previous Question: {previous_question}
Candidate's Answer: {user_answer}

Based STRICTLY on the study material above, generate ONE follow-up question in {language} that:
1. Is directly from the study material content
2. Tests understanding of concepts from the material
3. Is related to the candidate's previous answer
4. Is clear and specific

IMPORTANT: Only ask about content mentioned in the study material. No external knowledge.
Only output the question, nothing else. No explanations, no numbering."""
        else:
            # No study material - use general knowledge
            training_section = ""
            if training_prompt:
                training_section = f"\n{training_prompt}\n"
            
            prompt = f"""You are an expert technical interviewer conducting a viva/interview.
{training_section}
Topic: {topic}
Previous Question: {previous_question}
Candidate's Answer: {user_answer}

Generate ONE relevant follow-up question in {language} that:
1. Tests deeper knowledge about {topic}
2. Is related to the candidate's answer
3. Is clear and specific
4. Is appropriate for a technical interview

Only output the question, nothing else. No explanations, no numbering."""

        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 100
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            question = result.get("response", "").strip()
            
            # Clean up the response
            question = question.split("\n")[0].strip()
            
            # Fallback if empty
            if len(question) < 5:
                question = self._get_fallback_question(topic, language)
            
            return question
            
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama server not running. Please start Ollama app.")
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timed out. Model may be loading.")
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def _get_fallback_question(self, topic: str, language: str) -> str:
        """Fallback questions when LLM fails to generate good response."""
        import random
        fallback_questions = {
            "Hindi": [
                f"{topic} में safety precautions क्या लेनी चाहिए?",
                f"{topic} के main components कौन से हैं?",
                f"{topic} में कोई problem आए तो क्या करेंगे?",
                f"{topic} को operate करने से पहले क्या check करना चाहिए?",
                f"{topic} की maintenance कैसे करते हैं?",
            ],
            "English": [
                f"What safety precautions should be taken with {topic}?",
                f"What are the main components of {topic}?",
                f"What would you do if there's a problem with {topic}?",
                f"What should be checked before operating {topic}?",
                f"How do you maintain {topic}?",
            ]
        }
        lang_key = "Hindi" if "hindi" in language.lower() else "English"
        return random.choice(fallback_questions.get(lang_key, fallback_questions["English"]))


# Singleton instance
_ollama_instance = None

def get_ollama_llm():
    global _ollama_instance
    if _ollama_instance is None:
        _ollama_instance = OllamaLLM()
    return _ollama_instance


def get_study_material_for_machine(machine_id: int) -> str:
    """
    Get study material content for a specific machine from database.
    """
    try:
        from app.models.models import StudyMaterial
        materials = StudyMaterial.query.filter_by(
            machine_id=machine_id, 
            is_active=True
        ).all()
        
        if materials:
            # Combine all active materials
            combined_content = "\n\n".join([m.content for m in materials])
            return combined_content
        return ""
    except Exception as e:
        print(f"Error fetching study material: {e}")
        return ""


def get_machine_training_data(machine_id: int) -> dict:
    """
    Get training data (good/bad examples, instructions) for a specific machine.
    Used for few-shot learning to improve question quality.
    """
    try:
        from app.models.models import MachineTraining
        import json
        training = MachineTraining.query.filter_by(machine_id=machine_id).first()
        
        if training:
            # Parse JSON strings to lists
            good_examples = []
            bad_examples = []
            
            if training.good_examples:
                try:
                    good_examples = json.loads(training.good_examples) if isinstance(training.good_examples, str) else training.good_examples
                except:
                    good_examples = []
            
            if training.bad_examples:
                try:
                    bad_examples = json.loads(training.bad_examples) if isinstance(training.bad_examples, str) else training.bad_examples
                except:
                    bad_examples = []
            
            return {
                "good_examples": good_examples,
                "bad_examples": bad_examples,
                "instructions": training.instructions or "",
                "question_style": training.question_style or "practical",
                "preferred_language": training.preferred_language or "Hindi",
                "difficulty_focus": training.difficulty_focus or "medium"
            }
        return {}
    except Exception as e:
        print(f"Error fetching training data: {e}")
        return {}


def build_training_prompt(training_data: dict) -> str:
    """
    Build a prompt section from training data for few-shot learning.
    """
    if not training_data:
        return ""
    
    prompt_parts = []
    
    # Add custom instructions
    if training_data.get("instructions"):
        prompt_parts.append(f"=== SPECIAL INSTRUCTIONS ===\n{training_data['instructions']}\n")
    
    # Add good examples (questions to follow)
    good_examples = training_data.get("good_examples", [])
    if good_examples:
        prompt_parts.append("=== GOOD QUESTIONS (Follow this style) ===")
        for i, example in enumerate(good_examples[:5], 1):  # Max 5 examples
            q = example.get("question", "")
            a = example.get("answer", "")
            if q:
                prompt_parts.append(f"Example {i}:")
                prompt_parts.append(f"Q: {q}")
                if a:
                    prompt_parts.append(f"A: {a}")
        prompt_parts.append("")
    
    # Add bad examples (questions to avoid)
    bad_examples = training_data.get("bad_examples", [])
    if bad_examples:
        prompt_parts.append("=== BAD QUESTIONS (AVOID these types) ===")
        for example in bad_examples[:3]:  # Max 3 bad examples
            q = example.get("question", "")
            reason = example.get("reason", "Not appropriate")
            if q:
                prompt_parts.append(f"- DON'T ask: {q} (Reason: {reason})")
        prompt_parts.append("")
    
    # Add style preferences
    if training_data.get("question_style"):
        style = training_data["question_style"]
        prompt_parts.append(f"Question Style: {style}")
    
    if training_data.get("difficulty_focus"):
        diff = training_data["difficulty_focus"]
        prompt_parts.append(f"Focus on {diff} difficulty questions.")
    
    return "\n".join(prompt_parts)


def generate_next_question(topic: str, previous_question: str, user_answer: str, language: str = "Hindi", machine_id: int = None) -> str:
    """
    API-friendly function to generate the next interview question.
    If machine_id is provided, uses study material AND training data from that machine.
    """
    llm = get_ollama_llm()
    
    # Get study material if machine_id provided
    study_context = ""
    training_prompt = ""
    if machine_id:
        study_context = get_study_material_for_machine(machine_id)
        # Get training data for few-shot learning
        training_data = get_machine_training_data(machine_id)
        if training_data:
            training_prompt = build_training_prompt(training_data)
            print(f"[LLM] Using training data for machine {machine_id}")
    
    return llm.generate_followup_question(topic, previous_question, user_answer, language, study_context, training_prompt)


def evaluate_user_answer(topic: str, question: str, user_answer: str, language: str = "Hindi", machine_id: int = None) -> dict:
    """
    API-friendly function to evaluate user's answer.
    If machine_id is provided, evaluates answer against study material content.
    """
    llm = get_ollama_llm()
    
    # Get study material if machine_id provided
    study_context = None
    if machine_id:
        study_context = get_study_material_for_machine(machine_id)
    
    return llm.evaluate_answer(topic, question, user_answer, language, study_context)


def generate_questions_from_material(machine_id: int, num_questions: int = 15, language: str = "Hindi") -> list:
    """
    Generate questions from study material using RELIABLE approach.
    Includes model warm-up to prevent cold start timeouts.
    Uses training data (good/bad examples) for few-shot learning.
    
    Returns list of {question, expected_answer, level}
    Level: 1=Easy, 2=Medium, 3=Hard
    """
    study_content = get_study_material_for_machine(machine_id)
    
    if not study_content or len(study_content.strip()) < 50:
        return []
    
    # Get training data for this machine
    training_data = get_machine_training_data(machine_id)
    training_section = ""
    if training_data:
        training_section = build_training_prompt(training_data)
        print(f"[LLM] Using training data for machine {machine_id}")
    
    llm = get_ollama_llm()
    all_questions = []
    
    # CRITICAL: Warm up the model first - this loads it into memory
    print("[LLM] Warming up Ollama model (loading into memory)...")
    try:
        warmup_start = time.time() if 'time' in dir() else 0
        warmup = requests.post(
            OLLAMA_API_URL,
            json={
                "model": llm.model_name,
                "prompt": "Say OK",
                "stream": False,
                "options": {"num_predict": 3}
            },
            timeout=60  # Allow up to 60s for cold start
        )
        if warmup.status_code == 200:
            print(f"[LLM] Model warm-up complete, model is now in memory")
        else:
            print(f"[LLM] Warm-up returned status {warmup.status_code}")
    except requests.exceptions.Timeout:
        print("[LLM] WARNING: Warm-up timed out - model may be slow")
    except Exception as e:
        print(f"[LLM] Warm-up error: {e}")
    
    # Use limited context - 1500 chars is enough for good questions
    study_text = study_content[:1500].strip()
    
    print(f"[LLM] Generating {num_questions} questions from {len(study_text)} chars")
    
    # Build prompt with training examples if available
    if training_section:
        question_prompt = f"""Create {num_questions} Q&A pairs from this text in {language}.

{training_section}

=== STUDY MATERIAL ===
{study_text}
=== END MATERIAL ===

Format:
Q1: question
A1: answer

Q2: question
A2: answer

Generate now:"""
    else:
        # Very simple, short prompt for reliable response
        question_prompt = f"""Create {num_questions} Q&A pairs from this text in {language}:

{study_text}

Format:
Q1: question
A1: answer

Q2: question
A2: answer

Generate now:"""

    try:
        print(f"[LLM] Sending request (prompt: {len(question_prompt)} chars)...")
        start_time = time.time()
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": llm.model_name,
                "prompt": question_prompt,
                "stream": False,
                "keep_alive": "30m",  # Keep model in memory for 30 minutes
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1200  # Enough for 15 questions
                }
            },
            timeout=120  # 2 minutes timeout
        )
        elapsed = time.time() - start_time
        response.raise_for_status()
        result = response.json().get("response", "")
        
        print(f"[LLM] Response received in {elapsed:.1f}s, length: {len(result)}")
        print(f"[LLM] First 300 chars: {result[:300]}")
        
        # Parse Q&A pairs
        lines = result.split('\n')
        current_q = None
        current_a = None
        
        for line in lines:
            line = line.strip()
            # Remove markdown formatting like ** or *
            line = re.sub(r'\*+', '', line).strip()
            if not line:
                continue
            
            # Check for question line (Q1:, Q2:, Question 1:, **Q1:**, etc.)
            q_match = re.match(r'^(?:Q|Question|प्रश्न)\s*\d*[:\.\)\-]\s*(.+)', line, re.IGNORECASE)
            if q_match:
                # Save previous Q&A if exists
                if current_q and current_a:
                    # Assign difficulty based on question type
                    level = 1  # Default easy
                    q_lower = current_q.lower()
                    if any(w in q_lower for w in ['क्यों', 'कैसे', 'why', 'how', 'explain', 'समझाइए']):
                        level = 3  # Hard
                    elif any(w in q_lower for w in ['difference', 'compare', 'अंतर', 'फर्क']):
                        level = 2  # Medium
                    
                    all_questions.append({
                        "level": level,
                        "question": current_q,
                        "expected_answer": current_a
                    })
                current_q = q_match.group(1).strip()
                current_a = None
                continue
            
            # Check for answer line (A1:, A2:, Answer 1:, etc.)
            a_match = re.match(r'^(?:A|Answer|उत्तर)\s*\d*[:\.\)\-]\s*(.+)', line, re.IGNORECASE)
            if a_match:
                current_a = a_match.group(1).strip()
                continue
            
            # If we have a question but no answer, this line might be the answer
            if current_q and not current_a and len(line) > 5:
                current_a = line
        
        # Don't forget the last Q&A pair
        if current_q and current_a:
            level = 1
            q_lower = current_q.lower()
            if any(w in q_lower for w in ['क्यों', 'कैसे', 'why', 'how', 'explain']):
                level = 3
            elif any(w in q_lower for w in ['difference', 'compare', 'अंतर']):
                level = 2
            all_questions.append({
                "level": level,
                "question": current_q,
                "expected_answer": current_a
            })
        
        print(f"[LLM] Successfully parsed {len(all_questions)} questions")
        
    except requests.exceptions.Timeout:
        print("[LLM] Ollama request timed out")
    except Exception as e:
        print(f"[LLM] Error generating questions: {e}")
    
    # If still not enough, create fallback questions from key sentences
    if len(all_questions) < num_questions:
        print(f"[LLM] Only got {len(all_questions)}, generating fallback questions...")
        
        # Create simple questions from the content sentences
        sentences = study_content.replace('\n', ' ').split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        for i, sentence in enumerate(sentences):
            if len(all_questions) >= num_questions:
                break
            # Skip if already used as answer
            if sentence not in [q['expected_answer'] for q in all_questions]:
                all_questions.append({
                    "level": (i % 3) + 1,
                    "question": f"इस बारे में बताएं: {sentence[:60]}...?",
                    "expected_answer": sentence
                })
    
    print(f"[LLM] Returning {len(all_questions[:num_questions])} questions")
    return all_questions[:num_questions]


def generate_questions_for_department(machine_id: int, machine_name: str, num_questions: int = 10, language: str = "Hindi") -> list:
    """
    Generate questions for a department/machine using LLM's knowledge.
    First tries study material, if not available uses department name for context.
    Designed for Solar Panel Manufacturing departments.
    
    Returns list of {question, expected_answer, level}
    """
    # First check if study material is available
    study_content = get_study_material_for_machine(machine_id)
    
    # If study material exists, use the existing function
    if study_content and len(study_content.strip()) > 50:
        print(f"[LLM] Using study material for {machine_name}")
        return generate_questions_from_material(machine_id, num_questions, language)
    
    # No study material - use LLM's knowledge about the department
    print(f"[LLM] No study material found, using LLM knowledge for: {machine_name}")
    
    # Get training data for this machine
    training_data = get_machine_training_data(machine_id)
    training_section = ""
    if training_data:
        training_section = build_training_prompt(training_data)
        print(f"[LLM] Using training data for machine {machine_id}")
    
    llm = get_ollama_llm()
    all_questions = []
    
    # Warm up model
    print("[LLM] Warming up Ollama model...")
    try:
        warmup = requests.post(
            OLLAMA_API_URL,
            json={"model": llm.model_name, "prompt": "OK", "stream": False, "options": {"num_predict": 3}},
            timeout=60
        )
        if warmup.status_code == 200:
            print("[LLM] Model warm-up complete")
    except Exception as e:
        print(f"[LLM] Warm-up error: {e}")
    
    # Build a department-specific prompt for Solar Panel Manufacturing
    department_context = f"""You are an expert in Solar Panel Manufacturing Industry.
The department/machine is: {machine_name}

This is a VIVA/INTERVIEW for workers in a Solar Panel Manufacturing Plant.
Generate practical, job-relevant questions that a worker in this department should know.

Focus on:
- Safety procedures and precautions
- Machine operation and controls
- Quality parameters and testing
- Troubleshooting common problems
- Maintenance procedures
- Material handling
- Process parameters (temperature, pressure, timing, etc.)
"""

    # Add training examples if available
    if training_section:
        department_context += f"\n{training_section}\n"
    
    # Simple prompt for reliable parsing
    question_prompt = f"""{department_context}

Create {num_questions} practical Q&A pairs in {language} for workers.
Questions should be things a worker MUST know for their job.

Format exactly like this:
Q1: question here
A1: short answer here

Q2: question here  
A2: short answer here

Generate {num_questions} Q&A pairs now:"""

    try:
        print(f"[LLM] Generating department-based questions for: {machine_name}")
        start_time = time.time()
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": llm.model_name,
                "prompt": question_prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1500
                }
            },
            timeout=180
        )
        elapsed = time.time() - start_time
        response.raise_for_status()
        result = response.json().get("response", "")
        
        print(f"[LLM] Response received in {elapsed:.1f}s, length: {len(result)}")
        print(f"[LLM] First 300 chars: {result[:300]}")
        
        # Parse Q&A pairs (same parsing logic)
        lines = result.split('\n')
        current_q = None
        current_a = None
        
        for line in lines:
            line = line.strip()
            line = re.sub(r'\*+', '', line).strip()  # Remove markdown
            if not line:
                continue
            
            q_match = re.match(r'^(?:Q|Question|प्रश्न)\s*\d*[:\.\)\-]\s*(.+)', line, re.IGNORECASE)
            if q_match:
                if current_q and current_a:
                    level = 1
                    q_lower = current_q.lower()
                    if any(w in q_lower for w in ['क्यों', 'कैसे', 'why', 'how', 'explain']):
                        level = 3
                    elif any(w in q_lower for w in ['difference', 'compare', 'अंतर']):
                        level = 2
                    all_questions.append({
                        "level": level,
                        "question": current_q,
                        "expected_answer": current_a
                    })
                current_q = q_match.group(1).strip()
                current_a = None
                continue
            
            a_match = re.match(r'^(?:A|Answer|उत्तर)\s*\d*[:\.\)\-]\s*(.+)', line, re.IGNORECASE)
            if a_match:
                current_a = a_match.group(1).strip()
                continue
            
            if current_q and not current_a and len(line) > 5:
                current_a = line
        
        # Don't forget last Q&A
        if current_q and current_a:
            level = 1
            q_lower = current_q.lower()
            if any(w in q_lower for w in ['क्यों', 'कैसे', 'why', 'how', 'explain']):
                level = 3
            elif any(w in q_lower for w in ['difference', 'compare', 'अंतर']):
                level = 2
            all_questions.append({
                "level": level,
                "question": current_q,
                "expected_answer": current_a
            })
        
        print(f"[LLM] Parsed {len(all_questions)} questions")
        
    except requests.exceptions.Timeout:
        print("[LLM] Request timed out")
    except Exception as e:
        print(f"[LLM] Error: {e}")
    
    # Fallback questions if LLM failed - department specific
    if len(all_questions) < num_questions:
        print(f"[LLM] Adding fallback questions for {machine_name}")
        fallback_qs = get_department_fallback_questions(machine_name, language)
        for fq in fallback_qs:
            if len(all_questions) >= num_questions:
                break
            all_questions.append(fq)
    
    return all_questions[:num_questions]


def get_department_fallback_questions(department_name: str, language: str = "Hindi") -> list:
    """
    Generate fallback questions specific to solar panel manufacturing departments.
    """
    dept_lower = department_name.lower()
    
    # Solar Panel Manufacturing specific fallback questions
    questions_bank = {
        "cell": [
            {"level": 1, "question": "Cell ki efficiency kaise check karte hain?", "expected_answer": "IV curve testing aur EL testing se cell ki efficiency check ki jaati hai"},
            {"level": 1, "question": "Cell cutting machine mein blade kab change karna chahiye?", "expected_answer": "Jab cut edge rough ho ya chipping aaye tab blade change karna chahiye"},
            {"level": 2, "question": "EL testing kya hoti hai aur kyu zaroori hai?", "expected_answer": "EL (Electroluminescence) testing se cell mein micro cracks detect hote hain jo naked eye se nahi dikhte"},
            {"level": 2, "question": "Cell handling mein kaun si precautions leni chahiye?", "expected_answer": "Gloves pehanna, edges se pakadna, flat surface pe rakhna, stack zyada nahi karna"},
            {"level": 3, "question": "Cell efficiency kam hone ke main reasons kya hain?", "expected_answer": "Micro cracks, contamination, improper doping, surface defects, aur high resistance"},
        ],
        "string": [
            {"level": 1, "question": "String soldering ka temperature kitna hona chahiye?", "expected_answer": "180-220°C ke beech mein, cell type ke according"},
            {"level": 1, "question": "Ribbon width kitni hoti hai normally?", "expected_answer": "1.2mm se 1.6mm ke beech, cell size ke according"},
            {"level": 2, "question": "String mein cold solder joint kaise identify karein?", "expected_answer": "Dull gray appearance, rough surface, aur visual inspection mein gap dikhna"},
            {"level": 2, "question": "Tabbing machine ki speed kya affect karti hai?", "expected_answer": "Speed zyada hone se solder proper nahi hota, kam hone se throughput kam hota hai"},
            {"level": 3, "question": "String soldering mein flux ka kya role hai?", "expected_answer": "Flux oxide layer remove karta hai aur solder flow improve karta hai"},
        ],
        "lamination": [
            {"level": 1, "question": "Lamination temperature kitni honi chahiye?", "expected_answer": "140-150°C typically, EVA type ke according"},
            {"level": 1, "question": "Lamination time kitna hota hai?", "expected_answer": "12-18 minutes, module size aur EVA type ke according"},
            {"level": 2, "question": "Bubble kyu aate hain lamination mein?", "expected_answer": "Improper vacuum, EVA quality issue, ya temperature variation se"},
            {"level": 2, "question": "EVA kya hai aur kyu use hota hai?", "expected_answer": "Ethylene Vinyl Acetate - cells ko encapsulate karta hai aur moisture se protect karta hai"},
            {"level": 3, "question": "Delamination ke kya reasons ho sakte hain?", "expected_answer": "Poor EVA quality, improper temperature, contamination, ya insufficient pressure"},
        ],
        "frame": [
            {"level": 1, "question": "Frame fitting mein gap kitna acceptable hai?", "expected_answer": "0.5mm se kam gap acceptable hai corners pe"},
            {"level": 1, "question": "Silicone sealant kahan lagana chahiye?", "expected_answer": "Frame aur glass ke junction pe aur corners pe"},
            {"level": 2, "question": "Frame alignment check kaise karte hain?", "expected_answer": "Measuring tape se diagonal check karna - dono diagonal equal hone chahiye"},
            {"level": 2, "question": "Corner key ka kya purpose hai?", "expected_answer": "Corner key frame ko rigid banata hai aur alignment maintain karta hai"},
            {"level": 3, "question": "Frame grounding kyu zaroori hai?", "expected_answer": "Safety ke liye - lightning protection aur electrical safety ke liye grounding zaroori hai"},
        ],
        "testing": [
            {"level": 1, "question": "Flash test mein kya check hota hai?", "expected_answer": "Module ki power output (Watt), Voc, Isc, aur efficiency"},
            {"level": 1, "question": "Hi-pot test kya hai?", "expected_answer": "High potential test - insulation resistance check karne ke liye"},
            {"level": 2, "question": "IV curve se kya pata chalta hai?", "expected_answer": "Maximum power point, fill factor, efficiency, aur cell performance"},
            {"level": 2, "question": "EL testing fail hone ke reasons kya hain?", "expected_answer": "Cell cracks, broken fingers, poor soldering, ya interconnection issues"},
            {"level": 3, "question": "PID test kya hai aur kyu important hai?", "expected_answer": "Potential Induced Degradation test - long term performance verify karne ke liye"},
        ],
        "quality": [
            {"level": 1, "question": "Visual inspection mein kya check karte hain?", "expected_answer": "Scratches, chips, cracks, soldering defects, aur alignment"},
            {"level": 1, "question": "Rejection criteria kya hain module ke liye?", "expected_answer": "Visible cracks, delamination, low power output, insulation failure"},
            {"level": 2, "question": "SPC kya hai quality mein?", "expected_answer": "Statistical Process Control - process variation monitor karne ke liye"},
            {"level": 2, "question": "First article inspection kab hoti hai?", "expected_answer": "New batch start hone pe, machine setting change hone pe, ya shift change pe"},
            {"level": 3, "question": "Quality parameters ka documentation kyu zaroori hai?", "expected_answer": "Traceability ke liye, customer complaints handle karne ke liye, aur continuous improvement ke liye"},
        ]
    }
    
    # Find matching department
    matched_questions = []
    for key, questions in questions_bank.items():
        if key in dept_lower:
            matched_questions.extend(questions)
    
    # If no specific match, use general manufacturing questions
    if not matched_questions:
        matched_questions = [
            {"level": 1, "question": f"{department_name} mein safety PPE kya pehanna chahiye?", "expected_answer": "Safety shoes, gloves, safety glasses, aur ESD wrist strap"},
            {"level": 1, "question": f"{department_name} machine start karne se pehle kya check karein?", "expected_answer": "Power supply, emergency stop, guards, aur previous shift issues"},
            {"level": 2, "question": f"{department_name} mein quality reject hone pe kya karein?", "expected_answer": "Reject area mein rakhein, supervisor ko inform karein, aur rejection tag lagaein"},
            {"level": 2, "question": f"5S kya hai aur {department_name} mein kaise implement karein?", "expected_answer": "Sort, Set, Shine, Standardize, Sustain - workplace organization ke liye"},
            {"level": 3, "question": f"{department_name} mein downtime reduce kaise karein?", "expected_answer": "Preventive maintenance, proper training, spare parts availability, aur quick changeover"},
        ]
    
    return matched_questions


def evaluate_with_correct_answer(topic: str, question: str, user_answer: str, expected_answer: str, language: str = "Hindi") -> dict:
    """
    Evaluate user answer against expected answer from study material.
    MULTILINGUAL: User can answer in ANY language (Hindi, English, Hinglish, etc.)
    Evaluation matches semantic meaning regardless of language used.
    Returns score, feedback, and what the correct answer should be if wrong.
    """
    llm = get_ollama_llm()
    
    if not user_answer or len(user_answer.strip()) < 3:
        return {
            "is_correct": False,
            "score": 0,
            "feedback": "कृपया जवाब दें।" if "hindi" in language.lower() else "Please answer.",
            "correct_answer": expected_answer,
            "user_said": user_answer
        }
    
    # Multilingual evaluation prompt - ignore language differences, match meaning
    prompt = f"""You are evaluating an answer. The candidate may answer in ANY language (Hindi, English, Hinglish, mix, etc.)
Your job is to check if the MEANING matches, NOT the language.

Question: {question}
Expected Answer (Reference): {expected_answer}
Candidate's Answer: {user_answer}

IMPORTANT RULES:
- If candidate says same thing in different language, it is CORRECT
- Example: "photosynthesis" = "प्रकाश संश्लेषण" = "light se food banana" - all are SAME meaning
- Match CONCEPT and MEANING, ignore language/grammar/spelling
- Partial credit for partially correct answers

Evaluate semantic match:
MATCH: YES/PARTIAL/NO
SCORE: 0-100 (100=perfect match in any language, 50=partial, 0=wrong)
FEEDBACK: One line feedback in {language}"""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": llm.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 100
                }
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json().get("response", "")
        
        # Parse response
        is_match = "YES" in result.upper().split("MATCH:")[-1].split("\n")[0] if "MATCH:" in result.upper() else False
        is_partial = "PARTIAL" in result.upper()
        
        score = 50
        score_match = re.search(r'SCORE:\s*(\d+)', result, re.IGNORECASE)
        if score_match:
            score = min(100, max(0, int(score_match.group(1))))
        
        feedback = "जवाब का मूल्यांकन हो गया।"
        feedback_match = re.search(r'FEEDBACK:\s*(.+)', result, re.IGNORECASE)
        if feedback_match:
            feedback = feedback_match.group(1).strip()
        
        return {
            "is_correct": is_match and score >= 70,
            "is_partial": is_partial or (40 <= score < 70),
            "score": score,
            "feedback": feedback,
            "correct_answer": expected_answer if score < 70 else None,
            "user_said": user_answer
        }
        
    except Exception as e:
        return {
            "is_correct": False,
            "score": 30,
            "feedback": "मूल्यांकन में समस्या, आगे बढ़ते हैं।",
            "correct_answer": expected_answer,
            "user_said": user_answer
        }


def get_welcome_message(candidate_name: str, machine_name: str, language: str = "Hindi") -> str:
    """Generate a welcome message for the candidate."""
    if "hindi" in language.lower():
        return f"नमस्ते {candidate_name}! {machine_name} के viva में आपका स्वागत है। मैं आपसे कुछ सवाल पूछूंगा। अपने जवाब साफ और स्पष्ट बोलें। तैयार हैं? चलिए शुरू करते हैं।"
    else:
        return f"Hello {candidate_name}! Welcome to the {machine_name} viva. I will ask you some questions. Speak your answers clearly. Are you ready? Let's begin."


def get_viva_summary(questions_asked: list, language: str = "Hindi") -> dict:
    """
    Generate end-of-viva summary with improvements needed.
    questions_asked: list of {question, user_answer, expected_answer, score, is_correct}
    """
    total_questions = len(questions_asked)
    correct = sum(1 for q in questions_asked if q.get("is_correct", False))
    partial = sum(1 for q in questions_asked if q.get("is_partial", False))
    wrong = total_questions - correct - partial
    
    avg_score = sum(q.get("score", 0) for q in questions_asked) / max(1, total_questions)
    
    # Find wrong answers for improvement
    wrong_answers = [q for q in questions_asked if not q.get("is_correct", False)]
    
    # Generate grade
    if avg_score >= 80:
        grade = "Excellent"
        grade_hi = "उत्कृष्ट"
    elif avg_score >= 60:
        grade = "Good"
        grade_hi = "अच्छा"
    elif avg_score >= 40:
        grade = "Average"
        grade_hi = "औसत"
    else:
        grade = "Needs Improvement"
        grade_hi = "सुधार की जरूरत"
    
    improvements = []
    for q in wrong_answers[:5]:  # Top 5 wrong answers
        improvements.append({
            "question": q.get("question", ""),
            "your_answer": q.get("user_answer", q.get("user_said", "")),
            "correct_answer": q.get("expected_answer", q.get("correct_answer", ""))
        })
    
    return {
        "total_questions": total_questions,
        "correct": correct,
        "partial": partial,
        "wrong": wrong,
        "average_score": round(avg_score, 1),
        "grade": grade if "english" in language.lower() else grade_hi,
        "improvements": improvements,
        "message": f"आपने {total_questions} में से {correct} सवालों का सही जवाब दिया।" if "hindi" in language.lower() else f"You answered {correct} out of {total_questions} questions correctly."
    }
