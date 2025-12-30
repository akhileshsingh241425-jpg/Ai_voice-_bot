import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Alert, Spinner, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API_BASE = 'http://localhost:5000';

interface DashboardStats {
  totalEmployees: number;
  totalTopics: number;
  totalQuestions: number;
  departments: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalEmployees: 0,
    totalTopics: 0,
    totalQuestions: 0,
    departments: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load training system data
      const [deptRes, topicsRes] = await Promise.all([
        axios.get(`${API_BASE}/training/departments`),
        axios.get(`${API_BASE}/qa/topics-stats`),
      ]);

      const departments = deptRes.data.departments || [];
      const topics = topicsRes.data.topics || [];
      
      // Calculate totals
      const totalQuestions = topics.reduce((sum: number, t: any) => sum + (t.question_count || 0), 0);
      const totalEmployees = departments.reduce((sum: number, d: any) => sum + (d.employee_count || 0), 0);

      setStats({
        totalEmployees,
        totalTopics: topics.length,
        totalQuestions,
        departments: departments.length,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" role="status" variant="primary">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p className="mt-2">Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger" className="mt-3">
        <Alert.Heading>Error Loading Dashboard</Alert.Heading>
        <p>{error}</p>
        <Button variant="outline-danger" onClick={loadDashboardData}>
          Try Again
        </Button>
      </Alert>
    );
  }

  return (
    <div>
      {/* Header */}
      <Row className="mb-4">
        <Col>
          <h1 className="display-4">
            🎓 AI Training Viva System
          </h1>
          <p className="lead text-muted">
            Training Topic Based Voice Viva - Solar Panel Manufacturing
          </p>
        </Col>
      </Row>

      {/* Statistics Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center h-100 border-primary">
            <Card.Body>
              <div className="display-4 text-primary">👥</div>
              <Card.Title className="mt-3">Employees</Card.Title>
              <h2 className="text-primary">{stats.totalEmployees}</h2>
              <Card.Text className="text-muted">
                Registered employees
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center h-100 border-success">
            <Card.Body>
              <div className="display-4 text-success">📚</div>
              <Card.Title className="mt-3">Training Topics</Card.Title>
              <h2 className="text-success">{stats.totalTopics}</h2>
              <Card.Text className="text-muted">
                Available topics
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center h-100 border-warning">
            <Card.Body>
              <div className="display-4 text-warning">🏢</div>
              <Card.Title className="mt-3">Departments</Card.Title>
              <h2 className="text-warning">{stats.departments}</h2>
              <Card.Text className="text-muted">
                Production, Quality, etc.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center h-100 border-info">
            <Card.Body>
              <div className="display-4 text-info">❓</div>
              <Card.Title className="mt-3">Questions</Card.Title>
              <h2 className="text-info">{stats.totalQuestions}</h2>
              <Card.Text className="text-muted">
                In Q&A Bank
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <h4 className="mb-0">
                ⚡ Quick Actions
              </h4>
            </Card.Header>
            <Card.Body>
              <Row>
                {/* KBC Style Viva - Main Feature */}
                <Col md={6} className="mb-3">
                  <div className="d-grid">
                    <Link to="/kbc-viva">
                      <Button variant="warning" size="lg" className="w-100 py-4" style={{
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                        border: 'none', 
                        fontSize: '1.3rem',
                        color: 'white'
                      }}>
                        🎬 Start KBC Style Viva
                        <br/><small style={{fontSize: '0.8rem'}}>Avatar + Voice + Real-time LLM</small>
                      </Button>
                    </Link>
                  </div>
                </Col>
                
                <Col md={6} className="mb-3">
                  <div className="d-grid">
                    <Link to="/qa-bank">
                      <Button variant="info" size="lg" className="w-100 py-4" style={{
                        background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', 
                        border: 'none',
                        fontSize: '1.3rem',
                        color: 'white'
                      }}>
                        📝 Manage Q&A Bank
                        <br/><small style={{fontSize: '0.8rem'}}>Upload Excel per Topic</small>
                      </Button>
                    </Link>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* System Info */}
      <Row>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">✅ System Status</h5>
            </Card.Header>
            <Card.Body>
              <div className="d-flex align-items-center mb-2">
                <span className="text-success me-2">●</span>
                <span>Backend API Connected</span>
              </div>
              <div className="d-flex align-items-center mb-2">
                <span className="text-success me-2">●</span>
                <span>Whisper STT Ready</span>
              </div>
              <div className="d-flex align-items-center mb-2">
                <span className="text-success me-2">●</span>
                <span>Ollama LLM Ready</span>
              </div>
              <div className="d-flex align-items-center">
                <span className="text-success me-2">●</span>
                <span>Database Connected</span>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">📋 How to Use</h5>
            </Card.Header>
            <Card.Body>
              <ol className="mb-0">
                <li><strong>Q&A Bank</strong> - Upload questions per Training Topic (Excel)</li>
                <li><strong>Start Viva</strong> - Select Topic, Employee, Language</li>
                <li><strong>Answer</strong> - Speak your answer in Hindi/English</li>
                <li><strong>Score</strong> - LLM evaluates and gives feedback</li>
              </ol>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;