#!/usr/bin/env python3
"""
Add sample questions for viva testing
"""
from app import create_app
from app.models.models import db, Machine, Question, Answer

def add_sample_questions():
    """Add sample questions for first few machines for testing"""
    print("Adding sample questions for viva testing...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get first 3 machines
            machines = Machine.query.limit(3).all()
            
            if not machines:
                print("❌ No machines found")
                return False
            
            questions_added = 0
            
            for machine in machines:
                print(f"\nAdding questions for {machine.name}...")
                
                # Sample questions for each level
                sample_questions = {
                    1: [  # Level 1 - Basic
                        {
                            'question': f'{machine.name} का मुख्य कार्य क्या है?',
                            'answer': f'{machine.name} का मुख्य कार्य उत्पादन लाइन में विशिष्ट कार्य करना है।'
                        },
                        {
                            'question': f'{machine.name} की सुरक्षा के लिए क्या सावधानी बरतनी चाहिए?',
                            'answer': f'{machine.name} चलाते समय सुरक्षा उपकरण पहनना और निर्देशों का पालन करना आवश्यक है।'
                        },
                        {
                            'question': f'{machine.name} की दैनिक जांच कैसे करते हैं?',
                            'answer': f'{machine.name} की दैनिक जांच में मशीन की सफाई और कार्यप्रणाली की जांच शामिल है।'
                        }
                    ],
                    2: [  # Level 2 - Intermediate
                        {
                            'question': f'{machine.name} में आने वाली सामान्य समस्याएं क्या हैं?',
                            'answer': f'{machine.name} में सामान्य समस्याएं जैसे गति की कमी, गुणवत्ता में गिरावट हो सकती हैं।'
                        },
                        {
                            'question': f'{machine.name} की कार्यक्षमता कैसे बढ़ा सकते हैं?',
                            'answer': f'{machine.name} की कार्यक्षमता नियमित रखरखाव और सही संचालन से बढ़ाई जा सकती है।'
                        },
                        {
                            'question': f'{machine.name} के लिए गुणवत्ता नियंत्रण कैसे करते हैं?',
                            'answer': f'{machine.name} में गुणवत्ता नियंत्रण नियमित निरीक्षण और परीक्षण से किया जाता है।'
                        }
                    ],
                    3: [  # Level 3 - Advanced
                        {
                            'question': f'{machine.name} की तकनीकी समस्याओं का समाधान कैसे करें?',
                            'answer': f'{machine.name} की तकनीकी समस्याओं का समाधान विशेषज्ञ मार्गदर्शन और उन्नत तकनीकों से किया जाता है।'
                        },
                        {
                            'question': f'{machine.name} के प्रदर्शन को अधिकतम कैसे करें?',
                            'answer': f'{machine.name} का अधिकतम प्रदर्शन उचित सेटिंग्स और नियमित अनुकूलन से प्राप्त किया जाता है।'
                        },
                        {
                            'question': f'{machine.name} की रखरखाव रणनीति क्या होनी चाहिए?',
                            'answer': f'{machine.name} की रखरखाव रणनीति में निवारक रखरखाव और समय पर पुर्जों की बदली शामिल है।'
                        }
                    ]
                }
                
                for level in [1, 2, 3]:
                    for q_data in sample_questions[level]:
                        # Check if question already exists
                        existing = Question.query.filter_by(
                            machine_id=machine.id,
                            text=q_data['question'],
                            level=level
                        ).first()
                        
                        if not existing:
                            # Create question
                            question = Question(
                                machine_id=machine.id,
                                text=q_data['question'],
                                level=level
                            )
                            db.session.add(question)
                            db.session.flush()  # Get question ID
                            
                            # Create answer
                            answer = Answer(
                                question_id=question.id,
                                text=q_data['answer']
                            )
                            db.session.add(answer)
                            questions_added += 1
                            
                            print(f"  Added Level {level} question: {q_data['question'][:50]}...")
                        else:
                            print(f"  Skipped existing Level {level} question")
            
            db.session.commit()
            print(f"\n✅ Added {questions_added} new questions!")
            
            # Verify questions
            for machine in machines:
                for level in [1, 2, 3]:
                    count = Question.query.filter_by(machine_id=machine.id, level=level).count()
                    print(f"  {machine.name} Level {level}: {count} questions")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding questions: {e}")
            return False

if __name__ == "__main__":
    print("=== Adding Sample Questions for Viva Testing ===")
    if add_sample_questions():
        print("\n🎉 Sample questions ready for viva testing!")
    else:
        print("\n❌ Failed to add sample questions")