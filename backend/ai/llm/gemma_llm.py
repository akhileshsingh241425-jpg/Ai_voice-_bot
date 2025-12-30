"""
Google Gemma LLM Integration
- Generates follow-up questions based on user's answer and topic.
- Works like Jarvis: contextual, intelligent, interview-style questions.
"""

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from transformers.utils import logging as hf_logging
import torch
import os

# Enable progress bars and verbose logging for downloads
hf_logging.set_verbosity_info()
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"

# Hugging Face token for gated models (Gemma)
# Set HF_TOKEN environment variable with your Hugging Face token
HF_TOKEN = os.environ.get("HF_TOKEN", "")

class LocalLLM:
    def __init__(self, model_id="google/gemma-2b-it"):
        """
        Initialize the Gemma model for local inference.
        Requires Hugging Face login with access to Gemma.
        """
        self.model_id = model_id
        self.tokenizer = None
        self.model = None
        self.pipe = None
        self._loaded = False

    def load_model(self):
        """Load the model and tokenizer (lazy loading)."""
        if self._loaded:
            return
        
        print("="*60)
        print(f"[Gemma LLM] Starting model download: {self.model_id}")
        print("="*60)
        print("[Gemma LLM] Downloading tokenizer... (Progress bar will show)")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            use_fast=True,
            token=HF_TOKEN
        )
        print("[Gemma LLM] Tokenizer downloaded!")
        
        print("="*60)
        print("[Gemma LLM] Downloading model weights (~5GB)...")
        print("[Gemma LLM] This may take 5-15 minutes on first run...")
        print("="*60)
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            token=HF_TOKEN,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        print("[Gemma LLM] Model weights downloaded!")
        
        print("[Gemma LLM] Setting up generation pipeline...")
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=150,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )
        self._loaded = True
        print("="*60)
        print("[Gemma LLM] ✅ Model loaded successfully! Ready to generate.")
        print("="*60)

    def generate_followup_question(self, topic: str, previous_question: str, user_answer: str, language: str = "Hindi") -> str:
        """
        Generate a follow-up question based on user's answer and topic.
        Works like Jarvis: contextual, intelligent, interview-style.
        """
        self.load_model()
        
        # Better structured prompt for small models
        prompt = f"""<|system|>
You are an expert technical interviewer. Generate ONE relevant follow-up question in {language} based on the conversation below. The question should test deeper understanding of the topic.
</s>
<|user|>
Topic: {topic}
Previous Question: {previous_question}
Candidate's Answer: {user_answer}

Generate a single follow-up question in {language} that:
1. Tests deeper knowledge about {topic}
2. Is related to the candidate's answer
3. Is clear and specific
</s>
<|assistant|>
Follow-up Question: """
        
        result = self.pipe(prompt)
        generated = result[0]['generated_text']
        
        # Extract only the generated question (after prompt)
        if "Follow-up Question:" in generated:
            parts = generated.split("Follow-up Question:")
            question = parts[-1].strip()
        else:
            question = generated.replace(prompt, "").strip()
        
        # Take first line only and clean up
        question = question.split("\n")[0].strip()
        question = question.replace("</s>", "").replace("<|", "").strip()
        
        # Fallback if question is empty or too short
        if len(question) < 10:
            question = self._get_fallback_question(topic, language)
        
        return question
    
    def _get_fallback_question(self, topic: str, language: str) -> str:
        """Fallback questions when LLM fails to generate good response."""
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
        import random
        lang_key = "Hindi" if "hindi" in language.lower() else "English"
        return random.choice(fallback_questions.get(lang_key, fallback_questions["English"]))

# Singleton instance (lazy loaded)
_llm_instance = None

def get_local_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LocalLLM()
    return _llm_instance

def generate_next_question(topic: str, previous_question: str, user_answer: str, language: str = "Hindi") -> str:
    """
    API-friendly function to generate the next interview question.
    """
    llm = get_local_llm()
    return llm.generate_followup_question(topic, previous_question, user_answer, language)
