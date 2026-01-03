import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Button, Modal, Form, Spinner, Alert } from 'react-bootstrap';

// API Base URL - same as other components
const API_BASE_URL = process.env.REACT_APP_API_URL || (
  process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000'
);

interface VivaRecord {
  id: number;
  employee_id: string;
  employee_name: string;
  department: string;
  designation: string;
  topic_name: string;
  total_questions: number;
  correct_answers: number;
  partial_answers: number;
  wrong_answers: number;
  score_percent: number;
  result: string;
  video_path: string | null;
  language: string;
  duration_seconds: number;
  completed_at: string;
  answers_json?: string;
}

interface AnswerDetail {
  question: string;
  user_answer: string;
  expected_answer: string;
  score: number;
  is_correct: boolean;
  is_partial?: boolean;
  feedback: string;
}

const VivaRecords: React.FC = () => {
  const [records, setRecords] = useState<VivaRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<VivaRecord | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterResult, setFilterResult] = useState<string>('all');

  useEffect(() => {
    loadRecords();
  }, []);

  const loadRecords = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/viva-records/list`);
      const data = await response.json();
      if (data.success) {
        setRecords(data.records || []);
      } else {
        setError(data.error || 'Failed to load records');
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredRecords = records.filter(r => {
    const matchesSearch = 
      r.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.employee_id.includes(searchTerm) ||
      r.topic_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterResult === 'all' || r.result === filterResult;
    return matchesSearch && matchesFilter;
  });

  const openDetail = (record: VivaRecord) => {
    setSelectedRecord(record);
    setShowDetailModal(true);
  };

  const openVideo = (record: VivaRecord) => {
    setSelectedRecord(record);
    setShowVideoModal(true);
  };

  const getAnswers = (): AnswerDetail[] => {
    if (!selectedRecord?.answers_json) return [];
    try {
      return JSON.parse(selectedRecord.answers_json);
    } catch {
      return [];
    }
  };

  // Stats
  const totalVivas = records.length;
  const passCount = records.filter(r => r.result === 'Pass').length;
  const failCount = records.filter(r => r.result === 'Fail').length;
  const avgScore = records.length > 0 
    ? (records.reduce((sum, r) => sum + r.score_percent, 0) / records.length).toFixed(1)
    : '0';

  return (
    <Container fluid className="py-4" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      {/* Header */}
      <Row className="mb-4">
        <Col>
          <h2 className="mb-1">📊 Viva Records</h2>
          <p className="text-muted">View all viva exam results and recorded videos</p>
        </Col>
      </Row>

      {/* Stats Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center">
              <h3 className="text-primary mb-0">{totalVivas}</h3>
              <small className="text-muted">Total Vivas</small>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center">
              <h3 className="text-success mb-0">{passCount}</h3>
              <small className="text-muted">Passed</small>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center">
              <h3 className="text-danger mb-0">{failCount}</h3>
              <small className="text-muted">Failed</small>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center">
              <h3 className="text-info mb-0">{avgScore}%</h3>
              <small className="text-muted">Avg Score</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Row className="mb-4">
        <Col md={6}>
          <Form.Control
            type="text"
            placeholder="🔍 Search by name, punch ID, or topic..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </Col>
        <Col md={3}>
          <Form.Select value={filterResult} onChange={(e) => setFilterResult(e.target.value)}>
            <option value="all">All Results</option>
            <option value="Pass">✅ Pass Only</option>
            <option value="Fail">❌ Fail Only</option>
          </Form.Select>
        </Col>
        <Col md={3}>
          <Button variant="outline-primary" onClick={loadRecords}>
            🔄 Refresh
          </Button>
        </Col>
      </Row>

      {/* Error */}
      {error && <Alert variant="danger" onClose={() => setError(null)} dismissible>{error}</Alert>}

      {/* Records Table */}
      <Card className="border-0 shadow-sm">
        <Card.Body>
          {loading ? (
            <div className="text-center py-5">
              <Spinner animation="border" variant="primary" />
              <p className="mt-2 text-muted">Loading records...</p>
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="text-center py-5">
              <h4>📭 No Records Found</h4>
              <p className="text-muted">No viva records match your search criteria</p>
            </div>
          ) : (
            <Table hover responsive>
              <thead className="bg-light">
                <tr>
                  <th>#</th>
                  <th>Employee</th>
                  <th>Topic</th>
                  <th>Score</th>
                  <th>Result</th>
                  <th>Duration</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record, idx) => (
                  <tr key={record.id}>
                    <td>{idx + 1}</td>
                    <td>
                      <div>
                        <strong>{record.employee_name}</strong>
                        <br />
                        <small className="text-muted">ID: {record.employee_id}</small>
                      </div>
                    </td>
                    <td>
                      <div>
                        {record.topic_name}
                        <br />
                        <small className="text-muted">{record.language}</small>
                      </div>
                    </td>
                    <td>
                      <div>
                        <strong>{record.score_percent}%</strong>
                        <br />
                        <small className="text-muted">
                          {record.correct_answers}/{record.total_questions} correct
                        </small>
                      </div>
                    </td>
                    <td>
                      <Badge bg={record.result === 'Pass' ? 'success' : 'danger'} className="px-3 py-2">
                        {record.result === 'Pass' ? '✅ Pass' : '❌ Fail'}
                      </Badge>
                    </td>
                    <td>{formatDuration(record.duration_seconds)}</td>
                    <td>{formatDate(record.completed_at)}</td>
                    <td>
                      <Button 
                        variant="outline-primary" 
                        size="sm" 
                        className="me-1"
                        onClick={() => openDetail(record)}
                      >
                        📋 Details
                      </Button>
                      {record.video_path && (
                        <Button 
                          variant="outline-success" 
                          size="sm"
                          onClick={() => openVideo(record)}
                        >
                          🎬 Video
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Detail Modal */}
      <Modal show={showDetailModal} onHide={() => setShowDetailModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>📋 Viva Details - {selectedRecord?.employee_name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedRecord && (
            <>
              {/* Summary */}
              <Row className="mb-4">
                <Col md={6}>
                  <p><strong>👤 Employee:</strong> {selectedRecord.employee_name}</p>
                  <p><strong>🆔 Punch ID:</strong> {selectedRecord.employee_id}</p>
                  <p><strong>🏢 Department:</strong> {selectedRecord.department}</p>
                  <p><strong>💼 Designation:</strong> {selectedRecord.designation}</p>
                </Col>
                <Col md={6}>
                  <p><strong>📚 Topic:</strong> {selectedRecord.topic_name}</p>
                  <p><strong>🌐 Language:</strong> {selectedRecord.language}</p>
                  <p><strong>⏱️ Duration:</strong> {formatDuration(selectedRecord.duration_seconds)}</p>
                  <p><strong>📅 Date:</strong> {formatDate(selectedRecord.completed_at)}</p>
                </Col>
              </Row>

              {/* Score Card */}
              <Card className={`mb-4 ${selectedRecord.result === 'Pass' ? 'border-success' : 'border-danger'}`}>
                <Card.Body className="text-center">
                  <h1 className={selectedRecord.result === 'Pass' ? 'text-success' : 'text-danger'}>
                    {selectedRecord.score_percent}%
                  </h1>
                  <Badge bg={selectedRecord.result === 'Pass' ? 'success' : 'danger'} className="px-4 py-2 fs-5">
                    {selectedRecord.result}
                  </Badge>
                  <div className="mt-3">
                    <span className="text-success me-3">✅ {selectedRecord.correct_answers} Correct</span>
                    <span className="text-warning me-3">⚡ {selectedRecord.partial_answers} Partial</span>
                    <span className="text-danger">❌ {selectedRecord.wrong_answers} Wrong</span>
                  </div>
                </Card.Body>
              </Card>

              {/* Q&A Details */}
              <h5>📝 Question-wise Analysis</h5>
              {getAnswers().length > 0 ? (
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {getAnswers().map((ans, idx) => (
                    <Card key={idx} className={`mb-2 ${ans.is_correct ? 'border-success' : ans.is_partial ? 'border-warning' : 'border-danger'}`}>
                      <Card.Body>
                        <p><strong>Q{idx + 1}:</strong> {ans.question}</p>
                        <p className="mb-1"><strong>Your Answer:</strong> {ans.user_answer || '(No answer)'}</p>
                        <p className="mb-1 text-muted"><strong>Expected:</strong> {ans.expected_answer}</p>
                        <div className="d-flex justify-content-between align-items-center">
                          <small className="text-muted">{ans.feedback}</small>
                          <Badge bg={ans.is_correct ? 'success' : ans.is_partial ? 'warning' : 'danger'}>
                            {ans.is_correct ? '✅ Correct' : ans.is_partial ? '⚡ Partial' : '❌ Wrong'}
                          </Badge>
                        </div>
                      </Card.Body>
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-muted">No detailed answers available</p>
              )}
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDetailModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Video Modal */}
      <Modal show={showVideoModal} onHide={() => setShowVideoModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>🎬 Viva Recording - {selectedRecord?.employee_name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedRecord?.video_path && (
            <video 
              controls 
              width="100%" 
              style={{ maxHeight: '500px' }}
              src={`http://localhost:5000/viva-records/video/${selectedRecord.id}`}
            >
              Your browser does not support video playback.
            </video>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowVideoModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default VivaRecords;
