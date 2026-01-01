import React, { useState, useRef, useEffect } from 'react';
import { Button, Card, Container, Row, Col, Spinner, Badge, ProgressBar } from 'react-bootstrap';
import axios from 'axios';

// Production: empty string (relative URLs), Development: localhost:5000
const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000';

interface Message {
  role: 'ai' | 'user';
  text: string;
  timestamp: Date;
}

interface Topic {
  id: number;
  name: string;
  category_name: string;
  department_name: string;
}

interface Evaluation {
  score: number;
  strong_areas: string;
  weak_areas: string;
  summary: string;
}

interface EmployeeInfo {
  id: number;
  punch_id: string;
  name: string;
  department: string;
  designation: string;
  company: string;
  line_unit: string;
  photo: string;
}

type Screen = 'setup' | 'interview' | 'result';

const ChatViva: React.FC = () => {
  const [screen, setScreen] = useState<Screen>('setup');
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [punchId, setPunchId] = useState('');
  const [employee, setEmployee] = useState<EmployeeInfo | null>(null);
  const [lookupError, setLookupError] = useState('');
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [turn, setTurn] = useState(1);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const maxTurns = 8;

  // Load topics on mount
  useEffect(() => {
    loadTopics();
  }, []);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadTopics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/qa/topics-stats`);
      // Filter topics that have questions
      const topicsWithQuestions = (res.data.topics || []).filter((t: any) => t.total_questions > 0);
      setTopics(topicsWithQuestions);
    } catch (err) {
      console.error('Failed to load topics:', err);
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
      const res = await axios.get(`${API_BASE}/training/employee/lookup?punch_id=${punchId.trim()}`);
      if (res.data.success) {
        setEmployee(res.data.employee);
        setLookupError('');
      } else {
        setLookupError(res.data.error || 'Employee not found');
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setLookupError('❌ Invalid Punch ID - Employee not found');
      } else {
        setLookupError('Server error. Please try again.');
      }
      console.error('Lookup error:', err);
    } finally {
      setIsLookingUp(false);
    }
  };

  // Text-to-Speech
  const speak = (text: string): Promise<void> => {
    return new Promise((resolve) => {
      if (!('speechSynthesis' in window)) {
        resolve();
        return;
      }
      
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'hi-IN';
      utterance.rate = 0.9;
      
      utterance.onend = () => {
        setIsSpeaking(false);
        resolve();
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        resolve();
      };
      
      setIsSpeaking(true);
      window.speechSynthesis.speak(utterance);
    });
  };

  // Start Interview
  const startInterview = async () => {
    if (!selectedTopic || !employee) {
      alert('Please verify your Punch ID and select a topic');
      return;
    }

    setScreen('interview');
    setIsProcessing(true);

    try {
      const res = await axios.post(`${API_BASE}/chat-viva/start`, {
        topic_id: selectedTopic.id,
        user_name: employee.name,
        employee_id: employee.punch_id,
        language: 'Hindi'
      });

      const aiMessage = res.data.message;
      setMessages([{ role: 'ai', text: aiMessage, timestamp: new Date() }]);
      setTurn(res.data.turn || 1);
      
      await speak(aiMessage);
    } catch (err) {
      console.error('Failed to start:', err);
      const fallback = `नमस्ते ${employee.name}! आइए ${selectedTopic.name} के बारे में बात करते हैं। बताइए, आप क्या काम करते हैं?`;
      setMessages([{ role: 'ai', text: fallback, timestamp: new Date() }]);
      await speak(fallback);
    } finally {
      setIsProcessing(false);
    }
  };

  // Start Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        processRecording();
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Mic error:', err);
      alert('Microphone access denied!');
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Process Recording - STT then get AI response
  const processRecording = async () => {
    setIsProcessing(true);

    try {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      // STT
      const sttRes = await axios.post(`${API_BASE}/stt`, formData);
      const userText = sttRes.data.text || '';

      if (!userText.trim()) {
        await speak('माफ कीजिए, आवाज़ सुनाई नहीं दी। फिर से बोलिए।');
        setIsProcessing(false);
        return;
      }

      // Add user message
      const userMsg: Message = { role: 'user', text: userText, timestamp: new Date() };
      setMessages(prev => [...prev, userMsg]);

      // Build history for API
      const history = messages.map(m => ({
        ai: m.role === 'ai' ? m.text : '',
        user: m.role === 'user' ? m.text : ''
      })).filter(h => h.ai || h.user);

      // Get AI response
      const chatRes = await axios.post(`${API_BASE}/chat-viva/respond`, {
        topic_id: selectedTopic?.id,
        user_answer: userText,
        history: history,
        turn: turn,
        max_turns: maxTurns,
        language: 'Hindi'
      });

      const aiText = chatRes.data.message;
      const aiMsg: Message = { role: 'ai', text: aiText, timestamp: new Date() };
      setMessages(prev => [...prev, aiMsg]);
      setTurn(chatRes.data.turn || turn + 1);

      await speak(aiText);

      // Check if interview ended
      if (!chatRes.data.continue || chatRes.data.evaluation) {
        setEvaluation(chatRes.data.evaluation);
        setTimeout(() => setScreen('result'), 2000);
      }

    } catch (err) {
      console.error('Processing error:', err);
      await speak('कुछ problem हुई। फिर से try करें।');
    } finally {
      setIsProcessing(false);
    }
  };

  // End Interview
  const endInterview = async () => {
    setIsProcessing(true);
    try {
      const history = messages.reduce((acc: any[], m, i, arr) => {
        if (m.role === 'ai' && arr[i + 1]?.role === 'user') {
          acc.push({ ai: m.text, user: arr[i + 1].text });
        }
        return acc;
      }, []);

      const res = await axios.post(`${API_BASE}/chat-viva/evaluate-final`, {
        topic_id: selectedTopic?.id,
        history: history,
        language: 'Hindi'
      });

      setEvaluation(res.data.evaluation);
      await speak(res.data.message);
      setScreen('result');
    } catch (err) {
      setScreen('result');
    } finally {
      setIsProcessing(false);
    }
  };

  // Download Report
  const downloadReport = () => {
    const html = `
      <html>
      <head><title>Interview Report</title>
      <style>
        body { font-family: Arial; padding: 20px; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .score { font-size: 48px; color: ${(evaluation?.score || 0) >= 70 ? 'green' : (evaluation?.score || 0) >= 40 ? 'orange' : 'red'}; text-align: center; }
        .section { margin: 20px 0; }
        .message { padding: 10px; margin: 5px 0; border-radius: 8px; }
        .ai { background: #e3f2fd; }
        .user { background: #e8f5e9; }
      </style>
      </head>
      <body>
        <div class="header">
          <h1>🎤 Conversational Interview Report</h1>
          <p><strong>Punch ID:</strong> ${employee?.punch_id || ''}</p>
          <p><strong>Name:</strong> ${employee?.name || ''}</p>
          <p><strong>Department:</strong> ${employee?.department || ''}</p>
          <p><strong>Designation:</strong> ${employee?.designation || ''}</p>
          <p><strong>Topic:</strong> ${selectedTopic?.name}</p>
          <p><strong>Date:</strong> ${new Date().toLocaleString()}</p>
        </div>
        <div class="score">${evaluation?.score || 0}%</div>
        <div class="section">
          <h3>✅ Strong Areas</h3>
          <p>${evaluation?.strong_areas || 'N/A'}</p>
        </div>
        <div class="section">
          <h3>📚 Areas to Improve</h3>
          <p>${evaluation?.weak_areas || 'N/A'}</p>
        </div>
        <div class="section">
          <h3>💬 Conversation</h3>
          ${messages.map(m => `<div class="message ${m.role}">${m.role === 'ai' ? '🤖' : '👤'} ${m.text}</div>`).join('')}
        </div>
      </body>
      </html>
    `;
    const win = window.open('', '_blank');
    win?.document.write(html);
    win?.document.close();
    win?.print();
  };

  // ========== SETUP SCREEN ==========
  if (screen === 'setup') {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '40px 20px'
      }}>
        <Container>
          <Row className="justify-content-center">
            <Col md={8} lg={6}>
              <Card className="shadow-lg">
                <Card.Body className="p-4">
                  <h2 className="text-center mb-4">🎤 Voice Interview</h2>
                  <p className="text-center text-muted mb-4">
                    Natural conversation style - Just talk!
                  </p>

                  {/* Punch ID Input */}
                  <div className="mb-4">
                    <label className="form-label fw-bold">🔢 Punch ID डालें</label>
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control form-control-lg"
                        placeholder="अपना Punch ID डालें..."
                        value={punchId}
                        onChange={(e) => {
                          setPunchId(e.target.value);
                          setEmployee(null);
                          setLookupError('');
                        }}
                        onKeyPress={(e) => e.key === 'Enter' && lookupEmployee()}
                      />
                      <button 
                        className="btn btn-primary" 
                        type="button"
                        onClick={lookupEmployee}
                        disabled={isLookingUp}
                      >
                        {isLookingUp ? '...' : 'Verify'}
                      </button>
                    </div>
                    {lookupError && (
                      <div className="text-danger mt-2 small">{lookupError}</div>
                    )}
                  </div>

                  {/* Employee Details Card */}
                  {employee && (
                    <div className="mb-4 p-3 rounded" style={{ background: '#e8f5e9', border: '1px solid #4caf50' }}>
                      <div className="d-flex align-items-center">
                        <div style={{ 
                          width: '60px', 
                          height: '60px', 
                          borderRadius: '50%', 
                          background: '#4caf50',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '24px',
                          marginRight: '15px'
                        }}>
                          {employee.photo ? (
                            <img src={employee.photo} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                          ) : (
                            employee.name.charAt(0).toUpperCase()
                          )}
                        </div>
                        <div>
                          <div className="fw-bold text-success">✓ Verified</div>
                          <div className="fw-bold" style={{ fontSize: '18px' }}>{employee.name}</div>
                          <div className="text-muted small">
                            {employee.designation} | {employee.department}
                          </div>
                          <div className="text-muted small">{employee.company}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="mb-4">
                    <label className="form-label fw-bold">📚 Select Topic</label>
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      {topics.map(topic => (
                        <div
                          key={topic.id}
                          onClick={() => setSelectedTopic(topic)}
                          style={{
                            padding: '12px 15px',
                            margin: '5px 0',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            border: selectedTopic?.id === topic.id ? '2px solid #667eea' : '1px solid #ddd',
                            background: selectedTopic?.id === topic.id ? '#f0f4ff' : 'white'
                          }}
                        >
                          <div className="fw-bold">{topic.name}</div>
                          <small className="text-muted">{topic.category_name} • {topic.department_name}</small>
                        </div>
                      ))}
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    size="lg"
                    className="w-100"
                    onClick={startInterview}
                    disabled={!selectedTopic || !employee}
                  >
                    🎙️ Start Voice Interview
                  </Button>

                  <div className="text-center mt-3">
                    <a href="/kbc-viva" className="text-decoration-none">
                      ← Back to KBC Viva
                    </a>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Container>
      </div>
    );
  }

  // ========== INTERVIEW SCREEN ==========
  if (screen === 'interview') {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        color: 'white',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{ padding: '15px 20px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Badge bg="info">{selectedTopic?.name}</Badge>
            <span className="ms-2 text-muted">Turn {turn}/{maxTurns}</span>
          </div>
          <Button variant="outline-danger" size="sm" onClick={endInterview}>
            End Interview
          </Button>
        </div>

        {/* Progress */}
        <ProgressBar 
          now={(turn / maxTurns) * 100} 
          style={{ height: '4px', borderRadius: 0 }}
        />

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '15px'
              }}
            >
              <div style={{
                maxWidth: '80%',
                padding: '15px 20px',
                borderRadius: msg.role === 'user' ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
                background: msg.role === 'user' 
                  ? 'linear-gradient(135deg, #667eea, #764ba2)' 
                  : 'rgba(255,255,255,0.1)',
                fontSize: '16px',
                lineHeight: '1.5'
              }}>
                {msg.role === 'ai' && <span style={{ marginRight: '8px' }}>🤖</span>}
                {msg.text}
                {msg.role === 'user' && <span style={{ marginLeft: '8px' }}>👤</span>}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Recording Controls */}
        <div style={{ 
          padding: '20px', 
          borderTop: '1px solid #333',
          display: 'flex',
          justifyContent: 'center',
          gap: '20px',
          alignItems: 'center'
        }}>
          {isProcessing ? (
            <div className="text-center">
              <Spinner animation="border" variant="light" />
              <div className="mt-2">Processing...</div>
            </div>
          ) : isSpeaking ? (
            <div className="text-center">
              <div style={{ fontSize: '40px' }}>🔊</div>
              <div className="mt-2">AI Speaking...</div>
            </div>
          ) : (
            <Button
              variant={isRecording ? 'danger' : 'success'}
              size="lg"
              onClick={isRecording ? stopRecording : startRecording}
              style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                fontSize: '40px',
                boxShadow: isRecording ? '0 0 30px rgba(255,0,0,0.5)' : '0 0 30px rgba(0,255,0,0.3)'
              }}
            >
              {isRecording ? '⏹️' : '🎤'}
            </Button>
          )}
        </div>

        <div className="text-center pb-3 text-muted">
          {isRecording ? 'Recording... Tap to stop' : 'Tap microphone to speak'}
        </div>
      </div>
    );
  }

  // ========== RESULT SCREEN ==========
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px'
    }}>
      <Container>
        <Row className="justify-content-center">
          <Col md={8} lg={6}>
            <Card className="shadow-lg">
              <Card.Body className="p-4 text-center">
                <h2 className="mb-4">🎉 Interview Complete!</h2>

                <div style={{
                  fontSize: '80px',
                  fontWeight: 'bold',
                  color: (evaluation?.score || 0) >= 70 ? '#28a745' : (evaluation?.score || 0) >= 40 ? '#ffc107' : '#dc3545'
                }}>
                  {evaluation?.score || 0}%
                </div>

                <div className="text-muted mb-4">Your Understanding Score</div>

                <div className="text-start mb-4">
                  <h5>✅ Strong Areas</h5>
                  <p className="text-success">{evaluation?.strong_areas || 'Good effort!'}</p>

                  <h5>📚 Areas to Improve</h5>
                  <p className="text-danger">{evaluation?.weak_areas || 'Keep learning!'}</p>

                  <h5>💬 Summary</h5>
                  <p>{evaluation?.summary || 'Interview completed successfully.'}</p>
                </div>

                <div className="d-flex gap-3 justify-content-center">
                  <Button variant="success" size="lg" onClick={downloadReport}>
                    📥 Download Report
                  </Button>
                  <Button variant="primary" size="lg" onClick={() => window.location.reload()}>
                    🔄 New Interview
                  </Button>
                </div>

                <div className="mt-4">
                  <a href="/kbc-viva" className="text-decoration-none">
                    ← Back to KBC Viva
                  </a>
                  <span className="mx-3">|</span>
                  <a href="/" className="text-decoration-none">
                    🏠 Dashboard
                  </a>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default ChatViva;
