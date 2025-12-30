import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Card, Badge, ProgressBar, Form, Alert } from 'react-bootstrap';
import { VivaAPIService, handleAPIError } from '../services/apiService';

interface VivaQuestion {
  question: string;
  expected_answer: string;
  level: number;
}

interface AnswerRecord {
  question: string;
  user_answer: string;
  expected_answer: string;
  score: number;
  is_correct: boolean;
  is_partial?: boolean;
  feedback: string;
}

type VivaState = 'setup' | 'welcome' | 'playing' | 'waiting' | 'summary';

// Avatar expressions
type AvatarMood = 'neutral' | 'thinking' | 'happy' | 'encouraging' | 'listening';

const KBCViva: React.FC = () => {
  // Setup state
  const [machines, setMachines] = useState<any[]>([]);
  const [topics, setTopics] = useState<any[]>([]);  // NEW: Training topics
  const [sourceType, setSourceType] = useState<'topic' | 'machine'>('topic');  // NEW: Default to topic
  const [selectedMachine, setSelectedMachine] = useState<number | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null);  // NEW
  const [selectedMachineName, setSelectedMachineName] = useState<string>('');
  const [selectedTopicName, setSelectedTopicName] = useState<string>('');  // NEW
  const [userName, setUserName] = useState('');
  const [language, setLanguage] = useState<'Hindi' | 'English'>('Hindi');
  const [numQuestions, setNumQuestions] = useState(10);
  
  // Viva state
  const [vivaState, setVivaState] = useState<VivaState>('setup');
  const [questions, setQuestions] = useState<VivaQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerRecord[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Current question state
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);
  const [feedbackType, setFeedbackType] = useState<'success' | 'warning' | 'error'>('success');
  const [showCorrectAnswer, setShowCorrectAnswer] = useState<string | null>(null);
  
  // Avatar state
  const [avatarMood, setAvatarMood] = useState<AvatarMood>('neutral');
  const [hostMessage, setHostMessage] = useState('');
  
  // Timer for waiting
  const [waitSeconds, setWaitSeconds] = useState(0);
  const [isWaiting, setIsWaiting] = useState(false);
  const waitTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Audio recording
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Load machines on mount
  useEffect(() => {
    loadMachines();
    loadTopics();  // NEW
  }, []);

  const loadMachines = async () => {
    try {
      const data = await VivaAPIService.getMachines();
      setMachines(data.machines);
    } catch (err) {
      setError(handleAPIError(err));
    }
  };

  // NEW: Load training topics
  const loadTopics = async () => {
    try {
      const response = await fetch('http://localhost:5000/qa/topics-stats');
      const data = await response.json();
      // Only show topics with 5+ questions
      const topicsWithQuestions = (data.topics || []).filter((t: any) => (t.total_questions || 0) >= 5);
      setTopics(topicsWithQuestions);
    } catch (err) {
      console.error('Error loading topics:', err);
    }
  };

  // TTS - Speak text with avatar animation
  const speakText = (text: string, mood: AvatarMood = 'neutral') => {
    setAvatarMood(mood);
    setHostMessage(text);
    
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      
      const voices = window.speechSynthesis.getVoices();
      if (language === 'Hindi') {
        const hindiVoice = voices.find(v => 
          v.lang.includes('hi') || v.name.toLowerCase().includes('hindi')
        );
        if (hindiVoice) utterance.voice = hindiVoice;
        utterance.lang = 'hi-IN';
      } else {
        utterance.lang = 'en-US';
      }
      
      utterance.rate = 0.85;
      utterance.pitch = 1;
      
      utterance.onend = () => {
        setAvatarMood('neutral');
      };
      
      window.speechSynthesis.speak(utterance);
    }
  };

  // Generate questions in real-time (background)
  const generateQuestionsRealtime = async () => {
    setIsGenerating(true);
    
    try {
      // NEW: If topic selected, fetch from training Q&A bank
      if (sourceType === 'topic' && selectedTopic) {
        const lang = language === 'Hindi' ? 'HI' : 'EN';
        const response = await fetch(`http://localhost:5000/qa/viva-questions/${selectedTopic}?count=${numQuestions}&language=${lang}`);
        const data = await response.json();
        
        if (data.questions && data.questions.length > 0) {
          const formattedQuestions = data.questions.map((q: any) => ({
            question: q.question,
            expected_answer: q.expected_answer,
            level: q.level
          }));
          setQuestions(prev => [...prev, ...formattedQuestions]);
        }
      } else if (selectedMachine) {
        // OLD: Machine-based questions
        const result = await VivaAPIService.generateVivaQuestions(
          selectedMachine,
          numQuestions,
          language
        );
        
        if (result.questions && result.questions.length > 0) {
          setQuestions(prev => [...prev, ...result.questions]);
        }
      }
    } catch (err) {
      console.error('Error generating questions:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  // Start viva immediately with welcome
  const startViva = async () => {
    if (!userName.trim()) {
      setError('कृपया अपना नाम दर्ज करें');
      return;
    }
    
    if (sourceType === 'topic' && !selectedTopic) {
      setError('कृपया एक Training Topic चुनें');
      return;
    }
    
    if (sourceType === 'machine' && !selectedMachine) {
      setError('कृपया एक Machine चुनें');
      return;
    }
    
    setError(null);
    setVivaState('welcome');
    
    // Welcome message
    const sourceName = sourceType === 'topic' ? selectedTopicName : selectedMachineName;
    const welcomeMsg = language === 'Hindi' 
      ? `स्वागत है ${userName}! मैं आपका host हूँ। आज हम ${sourceName} के बारे में कुछ सवाल पूछेंगे। क्या आप तैयार हैं?`
      : `Welcome ${userName}! I'm your host. Today we'll discuss about ${sourceName}. Are you ready?`;
    
    speakText(welcomeMsg, 'happy');
    
    // Start generating questions in background
    generateQuestionsRealtime();
    
    // Auto-start after welcome (5 seconds)
    setTimeout(() => {
      if (questions.length > 0) {
        beginViva();
      } else {
        // Wait for at least 1 question
        const checkInterval = setInterval(() => {
          if (questions.length > 0) {
            clearInterval(checkInterval);
            beginViva();
          }
        }, 1000);
        
        // Max wait 30 seconds
        setTimeout(() => clearInterval(checkInterval), 30000);
      }
    }, 5000);
  };

  const beginViva = () => {
    setVivaState('playing');
    setCurrentIndex(0);
    askCurrentQuestion(0);
  };

  const askCurrentQuestion = (index: number) => {
    if (index >= questions.length) {
      // Need more questions or end
      if (isGenerating) {
        setHostMessage('अगला सवाल तैयार हो रहा है...');
        setAvatarMood('thinking');
        return;
      }
      showSummary();
      return;
    }
    
    const q = questions[index];
    const questionText = `Question ${index + 1}: ${q.question}`;
    
    setAvatarMood('neutral');
    speakText(questionText, 'neutral');
    setFeedback(null);
    setShowCorrectAnswer(null);
    setCurrentAnswer('');
    setIsWaiting(false);
  };

  // Voice recording
  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
      
      audioChunks.current = [];
      mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };
      
      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        stream.getTracks().forEach(track => track.stop());
        await processAnswer(audioBlob);
      };
      
      mediaRecorder.current.start();
      setIsListening(true);
      setAvatarMood('listening');
      setHostMessage('मैं सुन रहा हूँ... बोलिए');
    } catch (err) {
      setError('Microphone permission denied');
    }
  };

  const stopListening = () => {
    if (mediaRecorder.current && isListening) {
      mediaRecorder.current.stop();
      setIsListening(false);
      setAvatarMood('thinking');
      setHostMessage('आपका जवाब check कर रहा हूँ...');
    }
  };

  const processAnswer = async (audioBlob: Blob) => {
    setIsProcessing(true);
    
    try {
      // Speech to Text
      const audioFile = new File([audioBlob], 'answer.wav', { type: 'audio/wav' });
      const sttResult = await VivaAPIService.speechToText(audioFile);
      const transcribedText = sttResult.text;
      
      setCurrentAnswer(transcribedText);
      
      if (!transcribedText || transcribedText.trim().length < 3) {
        speakText('आपकी आवाज़ सुनाई नहीं दी। कृपया फिर से बोलें।', 'encouraging');
        setIsProcessing(false);
        return;
      }
      
      // Evaluate answer
      const currentQ = questions[currentIndex];
      const evalResult = await VivaAPIService.evaluateWithAnswer(
        currentQ.question,
        transcribedText,
        currentQ.expected_answer,
        language
      );
      
      // Record answer
      const answerRecord: AnswerRecord = {
        question: currentQ.question,
        user_answer: transcribedText,
        expected_answer: currentQ.expected_answer,
        score: evalResult.score,
        is_correct: evalResult.is_correct,
        is_partial: evalResult.is_partial,
        feedback: evalResult.feedback,
      };
      setAnswers(prev => [...prev, answerRecord]);
      
      // Show reaction based on answer
      if (evalResult.is_correct) {
        setFeedbackType('success');
        setFeedback('✅ बिल्कुल सही!');
        speakText('बिल्कुल सही! शाबाश!', 'happy');
        startWaitTimer(5);
      } else if (evalResult.is_partial) {
        setFeedbackType('warning');
        setFeedback('⚠️ आंशिक रूप से सही');
        setShowCorrectAnswer(currentQ.expected_answer);
        speakText('ठीक है, लेकिन पूरा जवाब था: ' + currentQ.expected_answer.substring(0, 100), 'encouraging');
        startWaitTimer(20);
      } else {
        setFeedbackType('error');
        setFeedback('❌ गलत जवाब');
        setShowCorrectAnswer(currentQ.expected_answer);
        speakText('अफ़सोस, सही जवाब था: ' + currentQ.expected_answer.substring(0, 100), 'encouraging');
        startWaitTimer(30);
      }
      
    } catch (err) {
      console.error('Error processing answer:', err);
      speakText('कोई समस्या आई। फिर से try करें।', 'encouraging');
    } finally {
      setIsProcessing(false);
    }
  };

  const submitTextAnswer = async () => {
    if (!currentAnswer.trim()) return;
    
    setIsProcessing(true);
    setAvatarMood('thinking');
    setHostMessage('आपका जवाब check कर रहा हूँ...');
    
    try {
      const currentQ = questions[currentIndex];
      const evalResult = await VivaAPIService.evaluateWithAnswer(
        currentQ.question,
        currentAnswer,
        currentQ.expected_answer,
        language
      );
      
      // Record answer
      const answerRecord: AnswerRecord = {
        question: currentQ.question,
        user_answer: currentAnswer,
        expected_answer: currentQ.expected_answer,
        score: evalResult.score,
        is_correct: evalResult.is_correct,
        is_partial: evalResult.is_partial,
        feedback: evalResult.feedback,
      };
      setAnswers(prev => [...prev, answerRecord]);
      
      // Show reaction
      if (evalResult.is_correct) {
        setFeedbackType('success');
        setFeedback('✅ बिल्कुल सही!');
        speakText('बिल्कुल सही! शाबाश!', 'happy');
        startWaitTimer(5);
      } else if (evalResult.is_partial) {
        setFeedbackType('warning');
        setFeedback('⚠️ आंशिक रूप से सही');
        setShowCorrectAnswer(currentQ.expected_answer);
        speakText('ठीक है, लेकिन पूरा जवाब था: ' + currentQ.expected_answer.substring(0, 100), 'encouraging');
        startWaitTimer(20);
      } else {
        setFeedbackType('error');
        setFeedback('❌ गलत जवाब');
        setShowCorrectAnswer(currentQ.expected_answer);
        speakText('अफ़सोस, सही जवाब था: ' + currentQ.expected_answer.substring(0, 100), 'encouraging');
        startWaitTimer(30);
      }
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  // Wait timer
  const startWaitTimer = (seconds: number) => {
    setWaitSeconds(seconds);
    setIsWaiting(true);
    
    if (waitTimerRef.current) {
      clearInterval(waitTimerRef.current);
    }
    
    waitTimerRef.current = setInterval(() => {
      setWaitSeconds(prev => {
        if (prev <= 1) {
          clearInterval(waitTimerRef.current!);
          setIsWaiting(false);
          moveToNext();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const skipWait = () => {
    if (waitTimerRef.current) {
      clearInterval(waitTimerRef.current);
    }
    window.speechSynthesis.cancel();
    setIsWaiting(false);
    setWaitSeconds(0);
    moveToNext();
  };

  const moveToNext = () => {
    const nextIndex = currentIndex + 1;
    
    if (nextIndex >= numQuestions || (nextIndex >= questions.length && !isGenerating)) {
      showSummary();
    } else {
      setCurrentIndex(nextIndex);
      askCurrentQuestion(nextIndex);
    }
  };

  const showSummary = () => {
    setVivaState('summary');
    
    const correct = answers.filter(a => a.is_correct).length;
    const total = answers.length;
    const percent = Math.round((correct / total) * 100);
    
    let summaryMsg = '';
    if (percent >= 80) {
      summaryMsg = `शानदार ${userName}! आपने ${total} में से ${correct} सवालों का सही जवाब दिया। Excellent!`;
    } else if (percent >= 50) {
      summaryMsg = `अच्छा ${userName}! आपने ${total} में से ${correct} सही किए। थोड़ी और practice करें!`;
    } else {
      summaryMsg = `${userName}, आपने ${total} में से ${correct} सही किए। Study material फिर से पढ़ें।`;
    }
    
    speakText(summaryMsg, 'happy');
  };

  // Render Avatar
  const renderAvatar = () => {
    const moodStyles: Record<AvatarMood, { bg: string; emoji: string; animation: string }> = {
      neutral: { bg: 'linear-gradient(135deg, #667eea, #764ba2)', emoji: '🎓', animation: '' },
      thinking: { bg: 'linear-gradient(135deg, #f093fb, #f5576c)', emoji: '🤔', animation: 'pulse 1.5s infinite' },
      happy: { bg: 'linear-gradient(135deg, #4facfe, #00f2fe)', emoji: '😊', animation: 'bounce 0.5s' },
      encouraging: { bg: 'linear-gradient(135deg, #43e97b, #38f9d7)', emoji: '💪', animation: '' },
      listening: { bg: 'linear-gradient(135deg, #fa709a, #fee140)', emoji: '👂', animation: 'pulse 1s infinite' },
    };
    
    const style = moodStyles[avatarMood];
    
    return (
      <div className="text-center mb-4">
        {/* Avatar Circle */}
        <div style={{
          width: '150px',
          height: '150px',
          borderRadius: '50%',
          background: style.bg,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '4rem',
          boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
          animation: style.animation,
          border: '4px solid white',
        }}>
          {style.emoji}
        </div>
        
        {/* Speech Bubble */}
        {hostMessage && (
          <div style={{
            background: 'white',
            borderRadius: '20px',
            padding: '15px 25px',
            margin: '20px auto',
            maxWidth: '500px',
            boxShadow: '0 5px 20px rgba(0,0,0,0.1)',
            position: 'relative',
          }}>
            <div style={{
              position: 'absolute',
              top: '-10px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 0,
              height: 0,
              borderLeft: '10px solid transparent',
              borderRight: '10px solid transparent',
              borderBottom: '10px solid white',
            }} />
            <p className="mb-0" style={{ fontSize: '1.1rem', color: '#333' }}>
              {hostMessage}
            </p>
          </div>
        )}
      </div>
    );
  };

  // Render Setup Screen
  const renderSetup = () => (
    <Container className="py-5">
      <Row className="justify-content-center">
        <Col md={8} lg={6}>
          <Card className="shadow-lg border-0" style={{ 
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            borderRadius: '20px',
          }}>
            <Card.Body className="p-5 text-white">
              <div className="text-center mb-4">
                <div style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  margin: '0 auto',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '3rem',
                }}>
                  🎓
                </div>
                <h2 className="mt-3">Smart Viva</h2>
                <p className="text-muted">KBC Style Interactive Viva</p>
              </div>
              
              {error && <Alert variant="danger">{error}</Alert>}
              
              <Form.Group className="mb-4">
                <Form.Label>👤 आपका नाम</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="अपना नाम लिखें..."
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="form-control-lg"
                  style={{ borderRadius: '10px' }}
                />
              </Form.Group>
              
              {/* NEW: Source Type Toggle */}
              <Form.Group className="mb-4">
                <Form.Label>📚 Source चुनें</Form.Label>
                <div className="d-flex gap-2">
                  <Button 
                    variant={sourceType === 'topic' ? 'primary' : 'outline-light'}
                    onClick={() => { setSourceType('topic'); setSelectedMachine(null); }}
                    className="flex-fill"
                  >
                    📚 Training Topics
                  </Button>
                  <Button 
                    variant={sourceType === 'machine' ? 'primary' : 'outline-light'}
                    onClick={() => { setSourceType('machine'); setSelectedTopic(null); }}
                    className="flex-fill"
                  >
                    ⚙️ Machines (Old)
                  </Button>
                </div>
              </Form.Group>
              
              {/* Conditional: Topic or Machine Selection */}
              {sourceType === 'topic' ? (
                <Form.Group className="mb-4">
                  <Form.Label>📖 Training Topic चुनें</Form.Label>
                  <Form.Select
                    value={selectedTopic || ''}
                    onChange={(e) => {
                      const id = parseInt(e.target.value);
                      setSelectedTopic(id);
                      const topic = topics.find(t => t.id === id);
                      setSelectedTopicName(topic?.name || '');
                    }}
                    className="form-select-lg"
                    style={{ borderRadius: '10px' }}
                  >
                    <option value="">-- Topic Select करें --</option>
                    {topics.map(t => (
                      <option key={t.id} value={t.id}>{t.name} ({t.total_questions} Q)</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              ) : (
                <Form.Group className="mb-4">
                  <Form.Label>🏭 Machine चुनें</Form.Label>
                  <Form.Select
                    value={selectedMachine || ''}
                    onChange={(e) => {
                      const id = parseInt(e.target.value);
                      setSelectedMachine(id);
                      const machine = machines.find(m => m.id === id);
                      setSelectedMachineName(machine?.name || '');
                    }}
                    className="form-select-lg"
                    style={{ borderRadius: '10px' }}
                  >
                    <option value="">-- Machine Select करें --</option>
                    {machines.map(m => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              )}
              
              <Row className="mb-4">
                <Col>
                  <Form.Label>🌐 Language</Form.Label>
                  <Form.Select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value as 'Hindi' | 'English')}
                    style={{ borderRadius: '10px' }}
                  >
                    <option value="Hindi">हिंदी</option>
                    <option value="English">English</option>
                  </Form.Select>
                </Col>
                <Col>
                  <Form.Label>📝 Questions</Form.Label>
                  <Form.Select
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                    style={{ borderRadius: '10px' }}
                  >
                    <option value={5}>5 Questions</option>
                    <option value={10}>10 Questions</option>
                    <option value={15}>15 Questions</option>
                    <option value={20}>20 Questions</option>
                  </Form.Select>
                </Col>
              </Row>
              
              <Button 
                variant="light" 
                size="lg" 
                className="w-100 py-3"
                onClick={startViva}
                disabled={(sourceType === 'topic' ? !selectedTopic : !selectedMachine) || !userName.trim()}
                style={{ 
                  borderRadius: '15px',
                  fontWeight: 'bold',
                  fontSize: '1.2rem',
                }}
              >
                🎤 Start Viva
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );

  // Render Welcome Screen
  const renderWelcome = () => (
    <Container fluid className="vh-100 d-flex align-items-center justify-content-center" style={{
      background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1a 100%)',
    }}>
      <div className="text-center text-white">
        {renderAvatar()}
        
        {isGenerating && (
          <div className="mt-4">
            <div className="spinner-border text-info" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-2">Questions तैयार हो रहे हैं...</p>
          </div>
        )}
        
        <Button 
          variant="success" 
          size="lg" 
          className="mt-4 px-5"
          onClick={beginViva}
          disabled={questions.length === 0}
        >
          🚀 शुरू करें
        </Button>
      </div>
    </Container>
  );

  // Render Playing Screen (Main Viva)
  const renderPlaying = () => {
    const currentQ = questions[currentIndex];
    const progress = ((currentIndex + 1) / numQuestions) * 100;
    
    if (!currentQ) {
      return (
        <Container fluid className="vh-100 d-flex align-items-center justify-content-center" style={{
          background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1a 100%)',
        }}>
          <div className="text-center text-white">
            <div className="spinner-border text-info mb-3" role="status" />
            <p>अगला question तैयार हो रहा है...</p>
          </div>
        </Container>
      );
    }
    
    return (
      <Container fluid className="min-vh-100 p-0" style={{
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1a 100%)',
      }}>
        {/* Progress Bar */}
        <ProgressBar 
          now={progress} 
          variant="info" 
          style={{ height: '8px', borderRadius: 0 }}
        />
        
        {/* Question Counter */}
        <div className="text-center py-2">
          <Badge bg="dark" className="px-4 py-2" style={{ fontSize: '1rem' }}>
            Question {currentIndex + 1} / {numQuestions}
          </Badge>
          {isGenerating && (
            <Badge bg="warning" className="ms-2 px-3 py-2">
              <span className="spinner-border spinner-border-sm me-1" />
              Generating...
            </Badge>
          )}
        </div>
        
        {/* Avatar */}
        <div className="pt-3">
          {renderAvatar()}
        </div>
        
        {/* Question Card */}
        <Container>
          <Row className="justify-content-center">
            <Col md={10} lg={8}>
              <Card className="shadow-lg border-0 mb-4" style={{
                background: 'linear-gradient(135deg, #2d3748, #1a202c)',
                borderRadius: '20px',
                border: '2px solid #4a5568',
              }}>
                <Card.Body className="p-4 text-white">
                  {/* Level Badge */}
                  <div className="text-center mb-3">
                    <Badge 
                      bg={currentQ.level === 1 ? 'success' : currentQ.level === 2 ? 'warning' : 'danger'}
                      className="px-4 py-2"
                      style={{ fontSize: '0.9rem' }}
                    >
                      {currentQ.level === 1 ? '🟢 Easy' : currentQ.level === 2 ? '🟡 Medium' : '🔴 Hard'}
                    </Badge>
                  </div>
                  
                  {/* Question */}
                  <h4 className="text-center mb-4" style={{ lineHeight: 1.6 }}>
                    {currentQ.question}
                  </h4>
                  
                  {/* User's Answer */}
                  {currentAnswer && (
                    <div className="p-3 mb-3" style={{
                      background: 'rgba(255,255,255,0.1)',
                      borderRadius: '10px',
                    }}>
                      <small className="text-muted">आपका जवाब:</small>
                      <p className="mb-0">{currentAnswer}</p>
                    </div>
                  )}
                  
                  {/* Feedback */}
                  {feedback && (
                    <Alert variant={feedbackType === 'success' ? 'success' : feedbackType === 'warning' ? 'warning' : 'danger'}>
                      {feedback}
                    </Alert>
                  )}
                  
                  {/* Correct Answer */}
                  {showCorrectAnswer && (
                    <Alert variant="info">
                      <strong>✅ सही जवाब:</strong> {showCorrectAnswer}
                    </Alert>
                  )}
                  
                  {/* Wait Timer with Skip */}
                  {isWaiting && (
                    <div className="text-center p-3" style={{
                      background: 'rgba(0,0,0,0.3)',
                      borderRadius: '10px',
                    }}>
                      <div style={{
                        fontSize: '2rem',
                        fontWeight: 'bold',
                        color: waitSeconds > 15 ? '#fc8181' : waitSeconds > 5 ? '#f6e05e' : '#68d391',
                      }}>
                        {waitSeconds}s
                      </div>
                      <Button variant="outline-light" onClick={skipWait} className="mt-2">
                        ⏭️ Skip - Next Question
                      </Button>
                    </div>
                  )}
                </Card.Body>
              </Card>
              
              {/* Controls - Hide when waiting */}
              {!isWaiting && (
                <Card className="shadow border-0" style={{
                  background: 'rgba(255,255,255,0.95)',
                  borderRadius: '20px',
                }}>
                  <Card.Body className="p-4">
                    {/* Voice Button */}
                    <div className="text-center mb-3">
                      <Button
                        variant={isListening ? 'danger' : 'primary'}
                        className="rounded-circle p-0"
                        onClick={isListening ? stopListening : startListening}
                        disabled={isProcessing}
                        style={{ 
                          width: '80px', 
                          height: '80px',
                          fontSize: '2rem',
                        }}
                      >
                        {isListening ? '⏹️' : isProcessing ? '⏳' : '🎤'}
                      </Button>
                      <p className="mt-2 text-muted">
                        {isListening ? '🔴 Recording... Click to stop' : 
                         isProcessing ? 'Processing...' : 'Click to speak'}
                      </p>
                    </div>
                    
                    {/* OR Text Input */}
                    <div className="text-center mb-2">
                      <small className="text-muted">— या टाइप करें —</small>
                    </div>
                    
                    <Form.Control
                      as="textarea"
                      rows={2}
                      placeholder="यहाँ जवाब लिखें..."
                      value={currentAnswer}
                      onChange={(e) => setCurrentAnswer(e.target.value)}
                      disabled={isListening || isProcessing}
                      style={{ borderRadius: '10px' }}
                    />
                    
                    <Button 
                      variant="success" 
                      className="w-100 mt-3"
                      onClick={submitTextAnswer}
                      disabled={!currentAnswer.trim() || isListening || isProcessing}
                      style={{ borderRadius: '10px' }}
                    >
                      जवाब Submit करें →
                    </Button>
                  </Card.Body>
                </Card>
              )}
            </Col>
          </Row>
        </Container>
        
        <style>{`
          @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
          }
          @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
          }
        `}</style>
      </Container>
    );
  };

  // Render Summary
  const renderSummary = () => {
    const correct = answers.filter(a => a.is_correct).length;
    const partial = answers.filter(a => a.is_partial).length;
    const wrong = answers.length - correct - partial;
    const avgScore = answers.reduce((sum, a) => sum + a.score, 0) / answers.length;
    const percent = Math.round((correct / answers.length) * 100);
    
    // Download PDF Report Function
    const downloadReport = () => {
      const reportDate = new Date().toLocaleDateString('en-IN');
      const reportTime = new Date().toLocaleTimeString('en-IN');
      const sourceName = sourceType === 'topic' ? selectedTopicName : selectedMachineName;
      
      // Create printable HTML content
      const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Viva Performance Report - ${userName}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: auto; }
            .header { text-align: center; border-bottom: 3px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
            .header h1 { color: #1a1a3e; margin: 0; }
            .header p { color: #666; margin: 5px 0; }
            .score-box { text-align: center; padding: 30px; background: ${percent >= 70 ? '#d4edda' : percent >= 40 ? '#fff3cd' : '#f8d7da'}; border-radius: 15px; margin: 20px 0; }
            .score-box h1 { font-size: 60px; margin: 0; color: ${percent >= 70 ? '#28a745' : percent >= 40 ? '#ffc107' : '#dc3545'}; }
            .stats { display: flex; justify-content: space-around; margin: 30px 0; }
            .stat { text-align: center; padding: 15px 25px; border-radius: 10px; }
            .stat.correct { background: #d4edda; }
            .stat.partial { background: #fff3cd; }
            .stat.wrong { background: #f8d7da; }
            .stat h3 { margin: 0; font-size: 28px; }
            .stat p { margin: 5px 0 0 0; color: #666; }
            .questions { margin-top: 30px; }
            .question { padding: 15px; margin: 10px 0; border-radius: 10px; border-left: 5px solid; }
            .question.correct { background: #d4edda; border-color: #28a745; }
            .question.partial { background: #fff3cd; border-color: #ffc107; }
            .question.wrong { background: #f8d7da; border-color: #dc3545; }
            .question strong { display: block; margin-bottom: 8px; }
            .answer { color: #555; font-size: 14px; }
            .expected { color: #28a745; font-size: 14px; margin-top: 5px; }
            .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #888; }
            @media print { body { padding: 20px; } }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>🎓 Viva Performance Report</h1>
            <p><strong>Candidate:</strong> ${userName}</p>
            <p><strong>Topic:</strong> ${sourceName}</p>
            <p><strong>Date:</strong> ${reportDate} | <strong>Time:</strong> ${reportTime}</p>
            <p><strong>Language:</strong> ${language}</p>
          </div>
          
          <div class="score-box">
            <h1>${percent}%</h1>
            <p style="font-size: 18px; color: #333;">
              ${percent >= 70 ? '🏆 Excellent Performance!' : percent >= 40 ? '👍 Good Effort - Keep Practicing!' : '📚 Needs Improvement - Study More!'}
            </p>
          </div>
          
          <div class="stats">
            <div class="stat correct">
              <h3>${correct}</h3>
              <p>✅ Correct</p>
            </div>
            <div class="stat partial">
              <h3>${partial}</h3>
              <p>⚠️ Partial</p>
            </div>
            <div class="stat wrong">
              <h3>${wrong}</h3>
              <p>❌ Wrong</p>
            </div>
          </div>
          
          <div class="questions">
            <h3>📊 Question-wise Analysis</h3>
            ${answers.map((a, idx) => `
              <div class="question ${a.is_correct ? 'correct' : a.is_partial ? 'partial' : 'wrong'}">
                <strong>Q${idx + 1}: ${a.question}</strong>
                <div class="answer"><strong>Your Answer:</strong> ${a.user_answer || 'No answer'}</div>
                <div class="answer"><strong>Score:</strong> ${a.score}% | <strong>Status:</strong> ${a.is_correct ? '✅ Correct' : a.is_partial ? '⚠️ Partial' : '❌ Wrong'}</div>
                ${!a.is_correct ? `<div class="expected"><strong>Expected Answer:</strong> ${a.expected_answer}</div>` : ''}
              </div>
            `).join('')}
          </div>
          
          <div class="footer">
            <p>Generated by AI Training Viva System</p>
            <p>Gautam Solar Private Limited</p>
          </div>
        </body>
        </html>
      `;
      
      // Open print dialog
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
          printWindow.print();
        }, 500);
      }
    };
    
    return (
      <Container className="py-5" style={{
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%)',
        minHeight: '100vh',
      }}>
        <Row className="justify-content-center">
          <Col md={10} lg={8}>
            {/* Avatar */}
            {renderAvatar()}
            
            {/* Score Card */}
            <Card className="shadow-lg border-0 mb-4" style={{
              borderRadius: '20px',
              overflow: 'hidden',
            }}>
              <Card.Header className="text-center py-4" style={{
                background: percent >= 70 ? 'linear-gradient(135deg, #11998e, #38ef7d)' 
                  : percent >= 40 ? 'linear-gradient(135deg, #f093fb, #f5576c)'
                  : 'linear-gradient(135deg, #eb3349, #f45c43)',
              }}>
                <h1 className="text-white mb-0" style={{ fontSize: '4rem' }}>
                  {percent}%
                </h1>
                <h4 className="text-white">
                  {percent >= 70 ? '🏆 Excellent!' : percent >= 40 ? '👍 Good Effort!' : '📚 Keep Learning!'}
                </h4>
              </Card.Header>
              
              <Card.Body className="p-4">
                <Row className="text-center mb-4">
                  <Col>
                    <h3 className="text-success">{correct}</h3>
                    <p className="text-muted mb-0">सही ✅</p>
                  </Col>
                  <Col>
                    <h3 className="text-warning">{partial}</h3>
                    <p className="text-muted mb-0">आंशिक ⚠️</p>
                  </Col>
                  <Col>
                    <h3 className="text-danger">{wrong}</h3>
                    <p className="text-muted mb-0">गलत ❌</p>
                  </Col>
                </Row>
                
                <hr />
                
                <h5 className="mb-3">📊 Question-wise Analysis</h5>
                {answers.map((a, idx) => (
                  <div key={idx} className="mb-3 p-3" style={{
                    background: a.is_correct ? '#d4edda' : a.is_partial ? '#fff3cd' : '#f8d7da',
                    borderRadius: '10px',
                  }}>
                    <div className="d-flex justify-content-between">
                      <strong>Q{idx + 1}: {a.question.substring(0, 50)}...</strong>
                      <Badge bg={a.is_correct ? 'success' : a.is_partial ? 'warning' : 'danger'}>
                        {a.score}%
                      </Badge>
                    </div>
                    {!a.is_correct && (
                      <small className="text-muted d-block mt-1">
                        <strong>सही जवाब:</strong> {a.expected_answer.substring(0, 100)}...
                      </small>
                    )}
                  </div>
                ))}
              </Card.Body>
              
              <Card.Footer className="text-center py-3">
                <Button 
                  variant="success" 
                  size="lg" 
                  onClick={downloadReport}
                  className="me-2"
                >
                  📥 Download Report
                </Button>
                <Button 
                  variant="primary" 
                  size="lg" 
                  onClick={() => {
                    setVivaState('setup');
                    setQuestions([]);
                    setAnswers([]);
                    setCurrentIndex(0);
                  }}
                  className="me-2"
                >
                  🔄 New Viva
                </Button>
              </Card.Footer>
            </Card>
          </Col>
        </Row>
      </Container>
    );
  };

  // Main render
  switch (vivaState) {
    case 'setup':
      return renderSetup();
    case 'welcome':
      return renderWelcome();
    case 'playing':
      return renderPlaying();
    case 'summary':
      return renderSummary();
    default:
      return renderSetup();
  }
};

export default KBCViva;
