import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Card, Badge, ProgressBar, Form, Alert } from 'react-bootstrap';
import { VivaAPIService, handleAPIError } from '../services/apiService';

// API Base URL - empty in production (same server), localhost in development
const API_BASE_URL = process.env.REACT_APP_API_URL || (
  process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000'
);

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
  const [punchId, setPunchId] = useState('');
  const [employee, setEmployee] = useState<any>(null);
  const [lookupError, setLookupError] = useState('');
  const [isLookingUp, setIsLookingUp] = useState(false);
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

  // Video recording state
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isVideoRecording, setIsVideoRecording] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const videoStreamRef = useRef<MediaStream | null>(null);
  const videoRecorderRef = useRef<MediaRecorder | null>(null);
  const videoChunksRef = useRef<Blob[]>([]);
  const vivaStartTime = useRef<Date | null>(null);

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
      setMachines(data.machines || []);
    } catch (err) {
      // Silently fail - machines are optional, topics are primary now
      console.log('Machines API not available (optional)');
      setMachines([]);
    }
  };

  // NEW: Load training topics
  const loadTopics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/qa/topics-stats`);
      const data = await response.json();
      console.log('Topics API Response:', data);
      // Only show topics with 5+ questions
      const topicsWithQuestions = (data.topics || []).filter((t: any) => (t.total_questions || 0) >= 5);
      console.log('Topics with 5+ questions:', topicsWithQuestions);
      setTopics(topicsWithQuestions);
    } catch (err) {
      console.error('Error loading topics:', err);
    }
  };

  // Lookup employee by Punch ID
  const lookupEmployee = async () => {
    if (!punchId.trim()) {
      setLookupError('Punch ID डालें');
      return;
    }
    
    setIsLookingUp(true);
    setLookupError('');
    setEmployee(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/training/employee/lookup?punch_id=${punchId.trim()}`);
      const data = await response.json();
      
      if (data.success) {
        setEmployee(data.employee);
        setLookupError('');
      } else {
        setLookupError(data.error || 'Employee not found');
      }
    } catch (err: any) {
      setLookupError('❌ Invalid Punch ID - Employee not found');
      console.error('Lookup error:', err);
    } finally {
      setIsLookingUp(false);
    }
  };

  // ========== VIDEO RECORDING FUNCTIONS ==========
  
  // Start camera preview
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false 
      });
      videoStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      return true;
    } catch (err) {
      console.error('Camera error:', err);
      setIsVideoEnabled(false);
      return false;
    }
  };

  // Start video recording
  const startVideoRecording = async () => {
    if (!isVideoEnabled) return;
    
    try {
      // Check if HTTPS or localhost
      if (!window.location.protocol.includes('https') && !window.location.hostname.includes('localhost')) {
        alert('⚠️ Camera/Mic requires HTTPS or localhost.\nFor testing, use: http://localhost:9000');
        return;
      }

      // Check if getUserMedia is available
      if (!navigator.mediaDevices?.getUserMedia) {
        alert('❌ Camera/Microphone not supported in this browser or connection.');
        return;
      }

      // Get camera + audio stream - LOW RESOLUTION for compression
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 320 },   // Low resolution for smaller file
          height: { ideal: 240 },
          frameRate: { ideal: 15 }, // Lower framerate
          facingMode: 'user' 
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 22050  // Lower audio quality
        }
      });
      
      videoStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      videoChunksRef.current = [];
      
      // Use lower bitrate for compression
      const options: MediaRecorderOptions = {
        mimeType: 'video/webm;codecs=vp8,opus',
        videoBitsPerSecond: 200000,  // 200 kbps video (very compressed)
        audioBitsPerSecond: 32000    // 32 kbps audio
      };
      
      const recorder = new MediaRecorder(stream, options);
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          videoChunksRef.current.push(e.data);
        }
      };
      
      videoRecorderRef.current = recorder;
      recorder.start(1000); // Chunk every 1 second
      setIsVideoRecording(true);
      vivaStartTime.current = new Date();
      
      console.log('📹 Video recording started (compressed mode)');
    } catch (err) {
      console.error('Video recording error:', err);
      setIsVideoEnabled(false);
    }
  };

  // Stop video recording and get blob
  const stopVideoRecording = (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!videoRecorderRef.current || !isVideoRecording) {
        resolve(null);
        return;
      }
      
      videoRecorderRef.current.onstop = () => {
        const videoBlob = new Blob(videoChunksRef.current, { type: 'video/webm' });
        console.log('📹 Video recording stopped, size:', videoBlob.size);
        resolve(videoBlob);
      };
      
      videoRecorderRef.current.stop();
      setIsVideoRecording(false);
      
      // Stop all tracks
      if (videoStreamRef.current) {
        videoStreamRef.current.getTracks().forEach(track => track.stop());
      }
    });
  };

  // Save viva record with video
  const saveVivaRecord = async (videoBlob: Blob | null, summaryData: any) => {
    try {
      const formData = new FormData();
      
      // Employee info
      formData.append('employee_id', employee?.punch_id || '');
      formData.append('employee_name', employee?.name || '');
      formData.append('department', employee?.department || '');
      formData.append('designation', employee?.designation || '');
      
      // Topic info
      formData.append('topic_id', String(selectedTopic || 0));
      formData.append('topic_name', selectedTopicName || selectedMachineName || '');
      
      // Results
      formData.append('total_questions', String(summaryData.total));
      formData.append('correct_answers', String(summaryData.correct));
      formData.append('partial_answers', String(summaryData.partial));
      formData.append('wrong_answers', String(summaryData.wrong));
      formData.append('score_percent', String(summaryData.percent));
      formData.append('language', language);
      
      // Duration
      const duration = vivaStartTime.current 
        ? Math.floor((new Date().getTime() - vivaStartTime.current.getTime()) / 1000)
        : 0;
      formData.append('duration_seconds', String(duration));
      formData.append('started_at', vivaStartTime.current?.toISOString() || '');
      
      // Answers JSON
      formData.append('answers_json', JSON.stringify(answers));
      
      // Video file
      if (videoBlob && videoBlob.size > 0) {
        formData.append('video', videoBlob, 'viva_recording.webm');
      }
      
      const response = await fetch(`${API_BASE_URL}/viva-records/save`, {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      console.log('✅ Viva record saved:', result);
      return result;
    } catch (err) {
      console.error('Error saving viva record:', err);
      return null;
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
        const response = await fetch(`${API_BASE_URL}/qa/viva-questions/${selectedTopic}?count=${numQuestions}&language=${lang}`);
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
    if (!employee) {
      setError('कृपया अपना Punch ID verify करें');
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
    
    // Start video recording
    if (isVideoEnabled) {
      await startVideoRecording();
    }
    
    // Welcome message
    const sourceName = sourceType === 'topic' ? selectedTopicName : selectedMachineName;
    const welcomeMsg = language === 'Hindi' 
      ? `स्वागत है ${employee.name}! मैं आपका host हूँ। आज हम ${sourceName} के बारे में कुछ सवाल पूछेंगे। क्या आप तैयार हैं?`
      : `Welcome ${employee.name}! I'm your host. Today we'll discuss about ${sourceName}. Are you ready?`;
    
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

  const showSummary = async () => {
    setVivaState('summary');
    
    const correct = answers.filter(a => a.is_correct).length;
    const partial = answers.filter(a => a.is_partial && !a.is_correct).length;
    const wrong = answers.filter(a => !a.is_correct && !a.is_partial).length;
    const total = answers.length;
    const percent = Math.round((correct / total) * 100);
    
    // Stop video recording and save
    const videoBlob = await stopVideoRecording();
    
    // Save viva record to database
    const summaryData = { total, correct, partial, wrong, percent };
    await saveVivaRecord(videoBlob, summaryData);
    
    let summaryMsg = '';
    const empName = employee?.name || 'Candidate';
    if (percent >= 80) {
      summaryMsg = `शानदार ${empName}! आपने ${total} में से ${correct} सवालों का सही जवाब दिया। Excellent!`;
    } else if (percent >= 50) {
      summaryMsg = `अच्छा ${empName}! आपने ${total} में से ${correct} सही किए। थोड़ी और practice करें!`;
    } else {
      summaryMsg = `${empName}, आपने ${total} में से ${correct} सही किए। Study material फिर से पढ़ें।`;
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
              
              {/* Punch ID Input */}
              <Form.Group className="mb-4">
                <Form.Label>🔢 Punch ID डालें</Form.Label>
                <div className="input-group">
                  <Form.Control
                    type="text"
                    placeholder="अपना Punch ID डालें..."
                    value={punchId}
                    onChange={(e) => {
                      setPunchId(e.target.value);
                      setEmployee(null);
                      setLookupError('');
                    }}
                    onKeyPress={(e: any) => e.key === 'Enter' && lookupEmployee()}
                    className="form-control-lg"
                    style={{ borderRadius: '10px 0 0 10px' }}
                  />
                  <button 
                    className="btn btn-primary" 
                    type="button"
                    onClick={lookupEmployee}
                    disabled={isLookingUp}
                    style={{ borderRadius: '0 10px 10px 0' }}
                  >
                    {isLookingUp ? '...' : 'Verify'}
                  </button>
                </div>
                {lookupError && (
                  <div className="text-danger mt-2 small">{lookupError}</div>
                )}
              </Form.Group>

              {/* Employee Details Card with Photo */}
              {employee && (
                <div className="mb-4 p-3 rounded" style={{ background: 'rgba(76, 175, 80, 0.15)', border: '2px solid #4caf50' }}>
                  <div className="d-flex align-items-center">
                    {/* Employee Photo */}
                    <div style={{ 
                      width: '80px', 
                      height: '80px', 
                      borderRadius: '50%', 
                      background: '#4caf50',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '28px',
                      marginRight: '15px',
                      overflow: 'hidden',
                      border: '3px solid #4caf50',
                      boxShadow: '0 4px 15px rgba(76, 175, 80, 0.4)'
                    }}>
                      {employee.photo ? (
                        <img 
                          src={`https://hrm.umanerp.com/${employee.photo}`} 
                          alt={employee.name}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={(e: any) => {
                            e.target.style.display = 'none';
                            e.target.parentElement.innerHTML = employee.name?.charAt(0)?.toUpperCase() || '?';
                          }}
                        />
                      ) : (
                        employee.name?.charAt(0)?.toUpperCase() || '?'
                      )}
                    </div>
                    <div className="flex-grow-1">
                      <div className="d-flex align-items-center mb-1">
                        <Badge bg="success" className="me-2">✓ Verified</Badge>
                        <small className="text-muted">ID: {employee.punch_id}</small>
                      </div>
                      <div className="fw-bold" style={{ fontSize: '20px', color: '#fff' }}>{employee.name}</div>
                      <div style={{ color: '#aaa', fontSize: '14px' }}>
                        <span className="me-2">👔 {employee.designation}</span>
                      </div>
                      <div style={{ color: '#888', fontSize: '13px' }}>
                        <span className="me-2">🏢 {employee.department}</span>
                        {employee.company && <span>| {employee.company}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
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
                      const val = e.target.value;
                      if (val === '') {
                        setSelectedTopic(null);
                        setSelectedTopicName('');
                      } else {
                        const id = parseInt(val);
                        setSelectedTopic(id);
                        const topic = topics.find(t => t.id === id);
                        setSelectedTopicName(topic?.name || '');
                      }
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
                disabled={
                  (sourceType === 'topic' ? (!selectedTopic || selectedTopic <= 0) : (!selectedMachine || selectedMachine <= 0)) 
                  || !employee
                }
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

  // Render Playing Screen (Main Viva) - CARTOON STYLE
  const renderPlaying = () => {
    const currentQ = questions[currentIndex];
    const progress = ((currentIndex + 1) / numQuestions) * 100;
    
    if (!currentQ) {
      return (
        <Container fluid className="vh-100 d-flex align-items-center justify-content-center" style={{
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        }}>
          <div className="text-center text-white">
            <div className="spinner-border text-info mb-3" role="status" />
            <p>अगला question तैयार हो रहा है...</p>
          </div>
        </Container>
      );
    }
    
    // DiceBear Cartoon Avatars - Working URLs
    const hostAvatarUrl = "https://api.dicebear.com/7.x/lorelei/svg?seed=trainer&backgroundColor=b6e3f4&flip=false";
    const userAvatarUrl = employee?.photo 
      ? `https://hrm.umanerp.com/${employee.photo}`
      : `https://api.dicebear.com/7.x/lorelei/svg?seed=${encodeURIComponent(employee?.name || 'student')}&backgroundColor=c0aede`;
    
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Animated Background */}
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundImage: 'radial-gradient(2px 2px at 20px 30px, rgba(255,255,255,0.3), transparent), radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.2), transparent)',
          backgroundSize: '200px 200px',
          animation: 'twinkle 5s infinite',
          pointerEvents: 'none'
        }} />

        {/* Video Recording - Corner */}
        {isVideoEnabled && isVideoRecording && (
          <div style={{
            position: 'fixed', top: '15px', right: '15px', zIndex: 1000,
            borderRadius: '12px', overflow: 'hidden',
            boxShadow: '0 4px 20px rgba(255,0,0,0.5)', border: '3px solid #ff4757'
          }}>
            <video ref={videoRef} autoPlay muted playsInline style={{ width: '100px', height: '75px', objectFit: 'cover' }} />
            <div style={{
              position: 'absolute', top: '5px', left: '5px', background: '#ff4757', color: 'white',
              padding: '2px 6px', borderRadius: '8px', fontSize: '9px', fontWeight: 'bold',
              display: 'flex', alignItems: 'center', gap: '3px'
            }}>
              <span style={{ width: '5px', height: '5px', background: 'white', borderRadius: '50%', animation: 'pulse 1s infinite' }}></span>
              REC
            </div>
          </div>
        )}

        {/* Header Bar */}
        <div style={{ 
          padding: '15px 25px', 
          background: 'rgba(0,0,0,0.4)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <Badge bg="primary" style={{ fontSize: '13px', padding: '10px 18px', borderRadius: '20px' }}>
              🎯 Question {currentIndex + 1} / {numQuestions}
            </Badge>
            <div style={{ color: '#fff', fontSize: '14px', fontWeight: '500' }}>
              {employee?.name}
            </div>
            <Badge bg={currentQ.level === 1 ? 'success' : currentQ.level === 2 ? 'warning' : 'danger'} 
              style={{ fontSize: '13px', padding: '10px 18px', borderRadius: '20px' }}>
              {currentQ.level === 1 ? '🟢 Easy' : currentQ.level === 2 ? '🟡 Medium' : '🔴 Hard'}
            </Badge>
          </div>
          <ProgressBar now={progress} variant="info" style={{ height: '8px', borderRadius: '4px', background: 'rgba(255,255,255,0.1)' }} />
        </div>

        {/* Main Chat Area */}
        <Container className="py-4" style={{ position: 'relative', zIndex: 10, maxWidth: '900px' }}>
          
          {/* ========== HOST (TRAINER) - LEFT SIDE ========== */}
          <Row className="mb-4">
            <Col xs={12}>
              <div className="d-flex align-items-end">
                {/* Host Cartoon Avatar */}
                <div style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  overflow: 'hidden',
                  boxShadow: '0 8px 30px rgba(102, 126, 234, 0.6)',
                  border: '4px solid #fff',
                  background: '#b6e3f4',
                  flexShrink: 0,
                  animation: avatarMood === 'thinking' ? 'bounce 1s infinite' : 'none'
                }}>
                  <img 
                    src={hostAvatarUrl}
                    alt="Trainer"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e: any) => { e.target.src = 'https://api.dicebear.com/7.x/bottts/svg?seed=host'; }}
                  />
                </div>
                
                {/* Host Speech Bubble */}
                <div style={{
                  marginLeft: '15px',
                  background: '#fff',
                  borderRadius: '20px 20px 20px 5px',
                  padding: '18px 22px',
                  maxWidth: 'calc(100% - 120px)',
                  position: 'relative',
                  boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                  animation: 'slideIn 0.4s ease-out'
                }}>
                  {/* Triangle pointer */}
                  <div style={{
                    position: 'absolute', left: '-12px', bottom: '20px',
                    width: 0, height: 0,
                    borderTop: '12px solid transparent',
                    borderBottom: '12px solid transparent',
                    borderRight: '12px solid #fff'
                  }} />
                  <div style={{ 
                    color: '#667eea', 
                    fontSize: '11px', 
                    fontWeight: '700', 
                    marginBottom: '8px',
                    textTransform: 'uppercase',
                    letterSpacing: '1px'
                  }}>
                    🎓 Trainer
                  </div>
                  <div style={{ 
                    color: '#2d3748', 
                    fontSize: '17px', 
                    fontWeight: '500', 
                    lineHeight: 1.6 
                  }}>
                    {currentQ.question}
                  </div>
                </div>
              </div>
            </Col>
          </Row>

          {/* ========== USER (STUDENT) - RIGHT SIDE ========== */}
          {(currentAnswer || isListening || isProcessing) && (
            <Row className="mb-4">
              <Col xs={12}>
                <div className="d-flex align-items-end justify-content-end">
                  {/* User Speech Bubble */}
                  <div style={{
                    marginRight: '15px',
                    background: isListening 
                      ? 'linear-gradient(135deg, #ff6b6b, #ee5a24)' 
                      : 'linear-gradient(135deg, #00b894, #00cec9)',
                    borderRadius: '20px 20px 5px 20px',
                    padding: '18px 22px',
                    maxWidth: 'calc(100% - 120px)',
                    position: 'relative',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.2)',
                    animation: isListening ? 'pulse 1s infinite' : 'slideInRight 0.4s ease-out'
                  }}>
                    {/* Triangle pointer */}
                    <div style={{
                      position: 'absolute', right: '-12px', bottom: '20px',
                      width: 0, height: 0,
                      borderTop: '12px solid transparent',
                      borderBottom: '12px solid transparent',
                      borderLeft: isListening ? '12px solid #ff6b6b' : '12px solid #00b894'
                    }} />
                    <div style={{ 
                      color: 'rgba(255,255,255,0.9)', 
                      fontSize: '11px', 
                      fontWeight: '700', 
                      marginBottom: '8px',
                      textTransform: 'uppercase',
                      letterSpacing: '1px'
                    }}>
                      👤 {employee?.name || 'You'}
                    </div>
                    <div style={{ color: '#fff', fontSize: '16px', lineHeight: 1.5 }}>
                      {isListening ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span className="recording-wave">🎤</span> बोल रहा हूँ...
                        </span>
                      ) : isProcessing ? (
                        <span>⏳ Processing...</span>
                      ) : currentAnswer}
                    </div>
                  </div>
                  
                  {/* User Cartoon Avatar with Photo */}
                  <div style={{
                    width: '100px',
                    height: '100px',
                    borderRadius: '50%',
                    overflow: 'hidden',
                    boxShadow: isListening 
                      ? '0 0 0 4px rgba(255,107,107,0.5), 0 8px 30px rgba(255,107,107,0.4)' 
                      : '0 8px 30px rgba(0, 184, 148, 0.5)',
                    border: '4px solid #fff',
                    background: '#c0aede',
                    flexShrink: 0,
                    animation: isListening ? 'pulse 1s infinite' : 'none'
                  }}>
                    <img 
                      src={userAvatarUrl}
                      alt={employee?.name || 'User'}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e: any) => {
                        e.target.src = `https://api.dicebear.com/7.x/lorelei/svg?seed=student&backgroundColor=c0aede`;
                      }}
                    />
                  </div>
                </div>
              </Col>
            </Row>
          )}

          {/* Feedback Section */}
          {feedback && (
            <Row className="mb-4">
              <Col xs={12}>
                <div className="d-flex align-items-start">
                  {/* Feedback Avatar */}
                  <div style={{
                    width: '70px',
                    height: '70px',
                    borderRadius: '50%',
                    background: feedbackType === 'success' ? 'linear-gradient(135deg, #00b894, #55efc4)' 
                      : feedbackType === 'warning' ? 'linear-gradient(135deg, #fdcb6e, #e17055)'
                      : 'linear-gradient(135deg, #d63031, #e17055)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '35px',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.3)',
                    border: '3px solid #fff',
                    flexShrink: 0
                  }}>
                    {feedbackType === 'success' ? '✅' : feedbackType === 'warning' ? '⚠️' : '❌'}
                  </div>
                  
                  {/* Feedback Bubble */}
                  <div style={{
                    marginLeft: '15px',
                    background: feedbackType === 'success' ? 'linear-gradient(135deg, #00b894, #55efc4)' 
                      : feedbackType === 'warning' ? 'linear-gradient(135deg, #fdcb6e, #e17055)'
                      : 'linear-gradient(135deg, #d63031, #e17055)',
                    borderRadius: '20px 20px 20px 5px',
                    padding: '15px 20px',
                    maxWidth: '70%',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.2)'
                  }}>
                    <div style={{ color: '#fff', fontSize: '16px', fontWeight: '500' }}>
                      {feedback}
                    </div>
                  </div>
                </div>
              </Col>
            </Row>
          )}

          {/* Correct Answer Display */}
          {showCorrectAnswer && (
            <Row className="mb-4">
              <Col xs={12}>
                <div style={{
                  background: 'linear-gradient(135deg, #0984e3, #6c5ce7)',
                  borderRadius: '15px',
                  padding: '15px 20px',
                  boxShadow: '0 8px 25px rgba(0,0,0,0.2)'
                }}>
                  <div style={{ color: '#fff', fontSize: '14px', marginBottom: '5px' }}>✅ सही जवाब:</div>
                  <div style={{ color: '#fff', fontSize: '16px' }}>{showCorrectAnswer}</div>
                </div>
              </Col>
            </Row>
          )}

          {/* Wait Timer */}
          {isWaiting && (
            <Row className="mb-4">
              <Col xs={12} className="text-center">
                <div style={{
                  display: 'inline-block',
                  background: 'rgba(0,0,0,0.5)',
                  borderRadius: '20px',
                  padding: '20px 40px'
                }}>
                  <div style={{
                    fontSize: '48px',
                    fontWeight: 'bold',
                    color: waitSeconds > 15 ? '#ff6b6b' : waitSeconds > 5 ? '#feca57' : '#1dd1a1',
                    textShadow: '0 0 20px currentColor'
                  }}>
                    {waitSeconds}s
                  </div>
                  <Button variant="outline-light" onClick={skipWait} className="mt-2">
                    ⏭️ Next Question
                  </Button>
                </div>
              </Col>
            </Row>
          )}

          {/* Controls - Voice & Text Input */}
          {!isWaiting && (
            <Row className="mt-4">
              <Col md={8} lg={6} className="mx-auto">
                <Card style={{
                  background: 'rgba(255,255,255,0.95)',
                  borderRadius: '25px',
                  border: 'none',
                  boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
                }}>
                  <Card.Body className="p-4">
                    {/* Voice Button */}
                    <div className="text-center mb-4">
                      <button
                        onClick={isListening ? stopListening : startListening}
                        disabled={isProcessing}
                        style={{
                          width: '100px',
                          height: '100px',
                          borderRadius: '50%',
                          border: 'none',
                          background: isListening 
                            ? 'linear-gradient(135deg, #ff6b6b, #ee5a24)' 
                            : 'linear-gradient(135deg, #667eea, #764ba2)',
                          color: 'white',
                          fontSize: '40px',
                          cursor: 'pointer',
                          boxShadow: isListening 
                            ? '0 0 0 10px rgba(255,107,107,0.3), 0 10px 40px rgba(255,107,107,0.5)'
                            : '0 10px 40px rgba(102,126,234,0.4)',
                          animation: isListening ? 'pulse 1s infinite' : 'none',
                          transition: 'all 0.3s ease'
                        }}
                      >
                        {isListening ? '⏹️' : isProcessing ? '⏳' : '🎤'}
                      </button>
                      <p className="mt-3 mb-0" style={{ color: '#666', fontWeight: '500' }}>
                        {isListening ? '🔴 Recording... Click to stop' : isProcessing ? '⏳ Processing...' : '🎤 Click to speak'}
                      </p>
                    </div>

                    <div className="text-center mb-3">
                      <span style={{ color: '#999' }}>— या टाइप करें —</span>
                    </div>

                    {/* Text Input */}
                    <Form.Control
                      as="textarea"
                      rows={2}
                      placeholder="यहाँ जवाब लिखें..."
                      value={currentAnswer}
                      onChange={(e) => setCurrentAnswer(e.target.value)}
                      disabled={isListening || isProcessing}
                      style={{ 
                        borderRadius: '15px', 
                        border: '2px solid #eee',
                        padding: '15px'
                      }}
                    />

                    <Button
                      onClick={submitTextAnswer}
                      disabled={!currentAnswer.trim() || isListening || isProcessing}
                      className="w-100 mt-3"
                      style={{
                        background: 'linear-gradient(135deg, #00b894, #00cec9)',
                        border: 'none',
                        borderRadius: '15px',
                        padding: '15px',
                        fontSize: '16px',
                        fontWeight: '600'
                      }}
                    >
                      जवाब Submit करें →
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          )}
        </Container>

        {/* Animations */}
        <style>{`
          @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
          }
          @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
          }
          @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
          }
          @keyframes slideInRight {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
          }
          @keyframes twinkle {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 0.8; }
          }
        `}</style>
      </div>
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
          <title>Viva Performance Report - ${employee?.name || 'Candidate'}</title>
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
            <p><strong>Candidate:</strong> ${employee?.name || 'N/A'}</p>
            <p><strong>Punch ID:</strong> ${employee?.punch_id || 'N/A'}</p>
            <p><strong>Department:</strong> ${employee?.department || 'N/A'}</p>
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
            {/* Employee Photo Header */}
            {employee && (
              <div className="text-center mb-4">
                <div style={{
                  width: '120px',
                  height: '120px',
                  borderRadius: '50%',
                  margin: '0 auto',
                  overflow: 'hidden',
                  border: `5px solid ${percent >= 70 ? '#38ef7d' : percent >= 40 ? '#f5576c' : '#eb3349'}`,
                  background: '#4caf50',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '48px',
                  fontWeight: 'bold',
                  boxShadow: '0 5px 30px rgba(0,0,0,0.4)'
                }}>
                  {employee.photo ? (
                    <img 
                      src={`https://hrm.umanerp.com/${employee.photo}`}
                      alt={employee.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e: any) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.innerHTML = employee.name?.charAt(0)?.toUpperCase() || '?';
                      }}
                    />
                  ) : (
                    employee.name?.charAt(0)?.toUpperCase() || '?'
                  )}
                </div>
                <h3 className="text-white mt-3 mb-0">{employee.name}</h3>
                <p style={{ color: '#aaa' }}>
                  {employee.designation} | {employee.department}
                </p>
              </div>
            )}
            
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
