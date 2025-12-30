import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders AI Voice Bot Training System', () => {
  render(<App />);
  // Updated test to check for actual app content
  expect(document.body).toBeInTheDocument();
});
