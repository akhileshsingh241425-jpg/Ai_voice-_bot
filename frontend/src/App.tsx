import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

// Core Components - Only what's being used
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import KBCViva from './components/KBCViva';
import ChatViva from './components/ChatViva';
import TrainingQABank from './components/TrainingQABank';
import VivaRecords from './components/VivaRecords';

import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* KBC Style Viva - Main Feature (Full screen, no navigation) */}
          <Route path="/kbc-viva" element={<KBCViva />} />
          
          {/* Conversational Voice Interview (Full screen) */}
          <Route path="/chat-viva" element={<ChatViva />} />
          
          {/* Viva Records Dashboard (Full screen) */}
          <Route path="/viva-records" element={<VivaRecords />} />
          
          {/* Regular routes with navigation */}
          <Route path="/*" element={
            <>
              <Navigation />
              <Container fluid className="mt-3">
                <Routes>
                  {/* Main Dashboard */}
                  <Route path="/" element={<Dashboard />} />
                  
                  {/* Q&A Bank Management - Upload questions per topic */}
                  <Route path="/qa-bank" element={<TrainingQABank />} />
                  
                  {/* Redirect unknown routes to dashboard */}
                  <Route path="*" element={<Navigate to="/" />} />
                </Routes>
              </Container>
            </>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
