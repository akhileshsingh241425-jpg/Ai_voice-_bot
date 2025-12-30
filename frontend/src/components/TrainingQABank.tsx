import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Table, Alert, ProgressBar, Badge, Tabs, Tab } from 'react-bootstrap';

interface Topic {
  id: number;
  name: string;
  category_name: string;
  is_common: boolean;
  total_questions: number;
  easy: number;
  medium: number;
  hard: number;
}

interface Question {
  id: number;
  question: string;
  expected_answer: string;
  level: number;
}

interface UploadResult {
  success: boolean;
  message: string;
  success_count: number;
  error_count: number;
  errors: string[];
}

const TrainingQABank: React.FC = () => {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [activeTab, setActiveTab] = useState('upload');
  
  // New question form
  const [newQ, setNewQ] = useState({ question: '', expected_answer: '', level: 1 });
  
  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadTopics();
    
    // Check URL param for topic filter
    const urlParams = new URLSearchParams(window.location.search);
    const topicId = urlParams.get('topic');
    if (topicId) {
      setSelectedTopic(Number(topicId));
      setActiveTab('topics');
    }
  }, []);

  useEffect(() => {
    if (selectedTopic) {
      loadQuestions(selectedTopic);
    }
  }, [selectedTopic]);

  const loadTopics = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:5000/qa/topics-stats');
      const data = await res.json();
      setTopics(data.topics || []);
      setTotalQuestions(data.total_questions || 0);
    } catch (error) {
      console.error('Error loading topics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQuestions = async (topicId: number) => {
    try {
      setLoading(true);
      const res = await fetch(`http://localhost:5000/qa/questions/${topicId}`);
      const data = await res.json();
      setQuestions(data.questions || []);
    } catch (error) {
      console.error('Error loading questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      setUploadResult(null);
      
      const res = await fetch('http://localhost:5000/qa/upload', {
        method: 'POST',
        body: formData
      });
      
      const result = await res.json();
      setUploadResult(result);
      
      if (result.success) {
        loadTopics();
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadResult({ success: false, message: 'Upload failed', success_count: 0, error_count: 1, errors: [String(error)] });
    } finally {
      setUploading(false);
    }
  };

  const handleAddQuestion = async () => {
    if (!selectedTopic || !newQ.question || !newQ.expected_answer) return;

    try {
      const res = await fetch('http://localhost:5000/qa/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newQ, topic_id: selectedTopic })
      });
      
      const data = await res.json();
      if (data.success) {
        setNewQ({ question: '', expected_answer: '', level: 1 });
        loadQuestions(selectedTopic);
        loadTopics();
      }
    } catch (error) {
      console.error('Add error:', error);
    }
  };

  const handleDeleteQuestion = async (questionId: number) => {
    if (!window.confirm('Delete this question?')) return;
    
    try {
      await fetch(`http://localhost:5000/qa/delete/${questionId}`, { method: 'DELETE' });
      if (selectedTopic) loadQuestions(selectedTopic);
      loadTopics();
    } catch (error) {
      console.error('Delete error:', error);
    }
  };

  const downloadTemplate = () => {
    const headers = 'topic_name,question,expected_answer,level\n';
    const example = 'Tabber & Stringer Process,Tabber machine ka function kya hai?,Tabber machine solar cells par ribbon attach karti hai interconnection ke liye,1\n';
    const content = headers + example;
    
    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'training_qa_template.csv';
    a.click();
  };

  const getLevelBadge = (level: number) => {
    switch (level) {
      case 1: return <Badge bg="success">Easy</Badge>;
      case 2: return <Badge bg="warning">Medium</Badge>;
      case 3: return <Badge bg="danger">Hard</Badge>;
      default: return <Badge bg="secondary">{level}</Badge>;
    }
  };

  return (
    <Container fluid className="py-4">
      <h2 className="mb-4">📚 Training Q&A Bank</h2>
      
      {/* Stats */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center bg-primary text-white">
            <Card.Body>
              <h3>{totalQuestions}</h3>
              <p className="mb-0">Total Questions</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center bg-success text-white">
            <Card.Body>
              <h3>{topics.filter(t => (t.total_questions || 0) >= 20).length}</h3>
              <p className="mb-0">Ready Topics (20+ Q)</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center bg-warning text-dark">
            <Card.Body>
              <h3>{topics.filter(t => (t.total_questions || 0) < 20 && (t.total_questions || 0) > 0).length}</h3>
              <p className="mb-0">Need More Questions</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center bg-danger text-white">
            <Card.Body>
              <h3>{topics.filter(t => (t.total_questions || 0) === 0).length}</h3>
              <p className="mb-0">No Questions</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'upload')} className="mb-4">
        {/* Upload Tab */}
        <Tab eventKey="upload" title="📤 Upload Excel">
          <Card>
            <Card.Body>
              <h5>Upload Q&A from Excel/CSV</h5>
              <p className="text-muted">
                Columns: <code>topic_name, question, expected_answer, level</code>
              </p>
              
              <Row className="align-items-center mb-3">
                <Col md={6}>
                  <Form.Control
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={handleFileUpload}
                    disabled={uploading}
                  />
                </Col>
                <Col md={3}>
                  <Button variant="outline-secondary" onClick={downloadTemplate}>
                    📥 Download Template
                  </Button>
                </Col>
              </Row>

              {uploading && <ProgressBar animated now={100} label="Uploading..." className="my-3" />}

              {uploadResult && (
                <Alert variant={uploadResult.success ? 'success' : 'danger'} className="mt-3">
                  <Alert.Heading>{uploadResult.success ? '✅ Success!' : '❌ Failed'}</Alert.Heading>
                  <p>{uploadResult.message}</p>
                  <p><strong>Uploaded:</strong> {uploadResult.success_count} | <strong>Errors:</strong> {uploadResult.error_count}</p>
                  {uploadResult.errors && uploadResult.errors.length > 0 && (
                    <ul className="mb-0">
                      {uploadResult.errors.slice(0, 10).map((err, i) => <li key={i} className="text-danger">{err}</li>)}
                    </ul>
                  )}
                </Alert>
              )}

              <hr />
              <h6>Excel Format:</h6>
              <Table bordered size="sm">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Description</th>
                    <th>Example</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td><code>topic_name</code></td><td>Training topic name</td><td>Tabber & Stringer Process</td></tr>
                  <tr><td><code>question</code></td><td>Question text</td><td>Tabber machine ka function kya hai?</td></tr>
                  <tr><td><code>expected_answer</code></td><td>Expected answer</td><td>Ribbon attach karti hai</td></tr>
                  <tr><td><code>level</code></td><td>1=Easy, 2=Medium, 3=Hard</td><td>1</td></tr>
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Tab>

        {/* Topics Tab */}
        <Tab eventKey="topics" title="📋 Topic-wise Q&A">
          <Row>
            <Col md={4}>
              <Card>
                <Card.Header>Training Topics</Card.Header>
                <Card.Body style={{ maxHeight: '600px', overflowY: 'auto' }}>
                  {topics.map(topic => (
                    <div
                      key={topic.id}
                      className={`p-2 mb-2 border rounded ${selectedTopic === topic.id ? 'bg-primary text-white' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setSelectedTopic(topic.id)}
                    >
                      <div className="d-flex justify-content-between">
                        <strong>{topic.name}</strong>
                        <Badge bg={topic.total_questions >= 20 ? 'success' : 'warning'}>
                          {topic.total_questions || 0}
                        </Badge>
                      </div>
                      <small className={selectedTopic === topic.id ? 'text-white-50' : 'text-muted'}>
                        {topic.category_name}
                        {topic.is_common && ' ★'}
                      </small>
                      <div className="mt-1">
                        <small>E: {topic.easy || 0} | M: {topic.medium || 0} | H: {topic.hard || 0}</small>
                      </div>
                    </div>
                  ))}
                </Card.Body>
              </Card>
            </Col>

            <Col md={8}>
              <Card>
                <Card.Header>Questions {selectedTopic && `(${questions.length})`}</Card.Header>
                <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {!selectedTopic && <p className="text-muted text-center">Select a topic</p>}
                  {loading && <p className="text-center">Loading...</p>}
                  
                  {questions.map((q, idx) => (
                    <Card key={q.id} className="mb-2">
                      <Card.Body className="py-2">
                        <div className="d-flex justify-content-between">
                          <div>
                            <strong>Q{idx + 1}:</strong> {q.question}
                          </div>
                          <div>
                            {getLevelBadge(q.level)}
                            <Button variant="link" size="sm" className="text-danger p-0 ms-2" onClick={() => handleDeleteQuestion(q.id)}>🗑️</Button>
                          </div>
                        </div>
                        <div className="text-muted mt-1">
                          <small><strong>A:</strong> {q.expected_answer}</small>
                        </div>
                      </Card.Body>
                    </Card>
                  ))}
                </Card.Body>
              </Card>

              {/* Add Question Form */}
              {selectedTopic && (
                <>
                  {/* Excel Upload for Selected Topic */}
                  <Card className="mt-3 border-primary">
                    <Card.Header className="bg-primary text-white">📤 Upload Excel for this Topic</Card.Header>
                    <Card.Body>
                      <p className="text-muted mb-2">
                        Excel columns: <code>question, expected_answer, level, language</code> 
                        <br/><small>(language = HI or EN)</small>
                      </p>
                      <Row className="align-items-center">
                        <Col md={5}>
                          <Form.Control
                            type="file"
                            accept=".xlsx,.xls,.csv"
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                setSelectedFile(file);
                                setUploadResult(null);
                              }
                            }}
                            disabled={uploading}
                          />
                        </Col>
                        <Col md={3}>
                          <Button 
                            variant="success" 
                            disabled={!selectedFile || uploading}
                            onClick={() => {
                              if (!selectedFile || !selectedTopic) return;
                              
                              const formData = new FormData();
                              formData.append('file', selectedFile);
                              formData.append('topic_id', selectedTopic.toString());
                              
                              setUploading(true);
                              fetch('http://localhost:5000/qa/upload-topic', {
                                method: 'POST',
                                body: formData
                              })
                              .then(res => res.json())
                              .then(result => {
                                setUploadResult(result);
                                if (result.success) {
                                  loadTopics();
                                  loadQuestions(selectedTopic);
                                  setSelectedFile(null);
                                }
                              })
                              .catch(err => {
                                setUploadResult({ success: false, message: 'Upload failed: ' + err, success_count: 0, error_count: 1, errors: [] });
                              })
                              .finally(() => setUploading(false));
                            }}
                          >
                            {uploading ? '⏳ Uploading...' : '📤 Upload'}
                          </Button>
                        </Col>
                        <Col md={4}>
                          <Button variant="outline-info" size="sm" onClick={() => {
                            const content = 'question,expected_answer,level,language\nYahan question likho,Yahan answer likho,1,HI\nWrite question here,Write answer here,1,EN';
                            const blob = new Blob([content], { type: 'text/csv' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'topic_qa_template.csv';
                            a.click();
                          }}>
                            📥 Template
                          </Button>
                        </Col>
                      </Row>
                      {selectedFile && <p className="mt-2 mb-0 text-info">📎 Selected: {selectedFile.name}</p>}
                      {uploading && <ProgressBar animated now={100} label="Uploading..." className="mt-2" />}
                      {uploadResult && (
                        <Alert variant={uploadResult.success ? 'success' : 'danger'} className="mt-2 mb-0">
                          {uploadResult.message} | ✅ {uploadResult.success_count} | ❌ {uploadResult.error_count}
                        </Alert>
                      )}
                    </Card.Body>
                  </Card>

                  {/* Manual Add Question Form */}
                  <Card className="mt-3">
                    <Card.Header>➕ Add New Question</Card.Header>
                    <Card.Body>
                      <Form.Group className="mb-2">
                        <Form.Control
                          placeholder="Question..."
                          value={newQ.question}
                          onChange={(e) => setNewQ({ ...newQ, question: e.target.value })}
                        />
                      </Form.Group>
                      <Form.Group className="mb-2">
                        <Form.Control
                          as="textarea"
                          rows={2}
                          placeholder="Expected Answer..."
                          value={newQ.expected_answer}
                          onChange={(e) => setNewQ({ ...newQ, expected_answer: e.target.value })}
                        />
                      </Form.Group>
                      <Row>
                        <Col md={4}>
                          <Form.Select value={newQ.level} onChange={(e) => setNewQ({ ...newQ, level: Number(e.target.value) })}>
                            <option value={1}>Easy</option>
                            <option value={2}>Medium</option>
                            <option value={3}>Hard</option>
                          </Form.Select>
                        </Col>
                        <Col md={4}>
                          <Button variant="success" onClick={handleAddQuestion} disabled={!newQ.question || !newQ.expected_answer}>
                            ➕ Add Question
                          </Button>
                        </Col>
                      </Row>
                    </Card.Body>
                  </Card>
                </>
              )}
            </Col>
          </Row>
        </Tab>

        {/* Stats Tab */}
        <Tab eventKey="stats" title="📊 Statistics">
          <Card>
            <Card.Body>
              <Table striped bordered hover>
                <thead>
                  <tr>
                    <th>Training Topic</th>
                    <th>Category</th>
                    <th>Easy</th>
                    <th>Medium</th>
                    <th>Hard</th>
                    <th>Total</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {topics.map(t => (
                    <tr key={t.id}>
                      <td>
                        {t.name}
                        {t.is_common && <Badge bg="warning" className="ms-2">★</Badge>}
                      </td>
                      <td>{t.category_name}</td>
                      <td><Badge bg="success">{t.easy || 0}</Badge></td>
                      <td><Badge bg="warning">{t.medium || 0}</Badge></td>
                      <td><Badge bg="danger">{t.hard || 0}</Badge></td>
                      <td><strong>{t.total_questions || 0}</strong></td>
                      <td>
                        {(t.total_questions || 0) >= 20 ? (
                          <Badge bg="success">✅ Ready</Badge>
                        ) : (t.total_questions || 0) > 0 ? (
                          <Badge bg="warning">⚠️ Need More</Badge>
                        ) : (
                          <Badge bg="danger">❌ Empty</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>
    </Container>
  );
};

export default TrainingQABank;
