import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';

const Navigation: React.FC = () => {
  return (
    <Navbar bg="dark" variant="dark" expand="lg" sticky="top">
      <Container>
        <LinkContainer to="/">
          <Navbar.Brand>
            🎓 AI Training Viva System
          </Navbar.Brand>
        </LinkContainer>
        
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <LinkContainer to="/">
              <Nav.Link>
                📊 Dashboard
              </Nav.Link>
            </LinkContainer>
            
            <LinkContainer to="/qa-bank">
              <Nav.Link>
                ❓ Q&A Bank
              </Nav.Link>
            </LinkContainer>
          </Nav>
          
          <Nav>
            <LinkContainer to="/kbc-viva">
              <Nav.Link className="btn btn-success text-white px-3">
                🎤 Start Viva
              </Nav.Link>
            </LinkContainer>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Navigation;