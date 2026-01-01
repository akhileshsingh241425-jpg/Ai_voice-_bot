// API Configuration and Services
import axios from 'axios';

// Base URL for backend API
// In production (same server), use empty string for relative URLs
// In development, use localhost:5000
const BASE_URL = process.env.REACT_APP_API_URL || (
  process.env.NODE_ENV === 'production' ? '' : 'http://127.0.0.1:5000'
);

// Create axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  // increase timeout to allow for longer STT/eval/LLM processing (2 minutes)
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for API responses
export interface Employee {
  id: number;
  name: string;
  role: string;
  machine: string;
}

export interface Machine {
  id: number;
  name: string;
  question_counts: {
    level_1: number;
    level_2: number;
    level_3: number;
  };
  total_questions: number;
}

export interface VivaSession {
  session_id: number;
  employee_name: string;
  machine_name: string;
  current_level: number;
  status: string;
  start_time: string;
  end_time?: string;
  total_score: number;
  questions_attempted: number;
  questions_correct: number;
}

export interface Question {
  viva_question_id: number;
  question_id: number;
  question_text: string;
  level: number;
  machine_name: string;
  employee_name: string;
  questions_remaining: number;
  session_info: {
    current_level: number;
    total_levels: number;
    time_elapsed: string;
    questions_attempted: number;
  };
}

export interface AnswerEvaluation {
  score: number;
  passed: boolean;
  similarity: number;
  keyword_score: number;
}

export interface AnswerResult {
  message: string;
  evaluation: AnswerEvaluation;
  question_text: string;
  user_answer: string;
  expected_answer: string;
  score: number;
  is_correct: boolean;
  time_taken: number;
  session_stats: {
    questions_attempted: number;
    questions_correct: number;
    current_level: number;
  };
}

// API Service Class
export class VivaAPIService {
  // Employee Management
  static async getEmployees(): Promise<Employee[]> {
    const response = await apiClient.get('/employees');
    return response.data;
  }

  // Machine Management
  static async getMachines(): Promise<{ machines: Machine[]; total_machines: number }> {
    const response = await apiClient.get('/machines');
    return response.data;
  }

  // Viva Session Management
  static async startVivaSession(employeeId: number, machineId: number): Promise<any> {
    const response = await apiClient.post('/start_viva', {
      employee_id: employeeId,
      machine_id: machineId,
    });
    return response.data;
  }

  // Quick AI Viva - no employee record needed
  static async startQuickAISession(machineId: number, userName: string): Promise<{
    session_id: number;
    user_name: string;
    machine_name: string;
    machine_id: number;
    study_materials_count: number;
  }> {
    const response = await apiClient.post('/start_quick_ai_viva', {
      machine_id: machineId,
      user_name: userName,
    });
    return response.data;
  }

  static async getQuestion(sessionId: number): Promise<Question> {
    const response = await apiClient.get(`/get_question/${sessionId}`);
    return response.data;
  }

  static async submitTextAnswer(vivaQuestionId: number, answer: string): Promise<AnswerResult> {
    const response = await apiClient.post(`/submit_answer/${vivaQuestionId}`, {
      answer: answer,
    });
    return response.data;
  }

  static async submitAudioAnswer(vivaQuestionId: number, audioFile: File): Promise<AnswerResult> {
    const formData = new FormData();
    formData.append('audio', audioFile);

    const response = await apiClient.post(`/submit_answer/${vivaQuestionId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  static async completeLevel(sessionId: number): Promise<any> {
    const response = await apiClient.post(`/complete_level/${sessionId}`);
    return response.data;
  }

  static async getVivaProgress(sessionId: number): Promise<any> {
    const response = await apiClient.get(`/viva_progress/${sessionId}`);
    return response.data;
  }

  static async getActiveSessions(): Promise<{ active_sessions: VivaSession[]; total_active: number }> {
    const response = await apiClient.get('/active_sessions');
    return response.data;
  }

  static async endSession(sessionId: number): Promise<any> {
    const response = await apiClient.post(`/end_session/${sessionId}`);
    return response.data;
  }

  // AI Services
  static async speechToText(audioFile: File): Promise<{ text: string }> {
    const formData = new FormData();
    formData.append('audio', audioFile);

    const response = await apiClient.post('/stt', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  static async evaluateAnswer(
    answer: string,
    expectedAnswer: string,
    expectedKeywords: string[]
  ): Promise<AnswerEvaluation> {
    const response = await apiClient.post('/evaluate', {
      answer,
      expected_answer: expectedAnswer,
      expected_keywords: expectedKeywords,
    });
    return response.data;
  }

  // AI LLM - Generate next question based on user's answer
  static async generateNextQuestion(
    topic: string,
    previousQuestion: string,
    userAnswer: string,
    language: string = 'Hindi',
    machineId?: number  // Optional - for context-based questions from study material
  ): Promise<{ 
    next_question: string; 
    evaluation?: { 
      is_relevant: boolean; 
      score: number; 
      feedback: string; 
      reason?: string; 
    };
    repeat?: boolean;
    using_study_material?: boolean;
  }> {
    const response = await apiClient.post('/next_question', {
      topic,
      previous_question: previousQuestion,
      user_answer: userAnswer,
      language,
      machine_id: machineId,
    });
    return response.data;
  }

  // Question Management (Admin)
  static async addQuestion(
    machineId: number,
    questionText: string,
    answerText: string,
    level: number
  ): Promise<any> {
    const response = await apiClient.post('/questions', {
      machine_id: machineId,
      question_text: questionText,
      answer_text: answerText,
      level,
    });
    return response.data;
  }

  static async getQuestionsByLevel(machineId: number, level: number): Promise<any> {
    const response = await apiClient.get(`/questions/${machineId}/${level}`);
    return response.data;
  }

  static async bulkAddQuestions(questions: any[]): Promise<any> {
    const response = await apiClient.post('/questions/bulk', {
      questions,
    });
    return response.data;
  }

  // Study Material Management
  static async uploadStudyMaterial(
    machineId: number,
    file: File,
    title?: string
  ): Promise<{
    message: string;
    material_id: number;
    title: string;
    content_length: number;
    preview: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('machine_id', machineId.toString());
    if (title) formData.append('title', title);

    const response = await apiClient.post('/upload_study_material', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  static async getStudyMaterials(machineId: number): Promise<{
    id: number;
    title: string;
    content_preview: string;
    content_length: number;
  }[]> {
    const response = await apiClient.get(`/study_materials/${machineId}`);
    return response.data;
  }

  static async deleteStudyMaterial(materialId: number): Promise<{ message: string }> {
    const response = await apiClient.delete(`/study_material/${materialId}`);
    return response.data;
  }

  // NEW: Generate all viva questions from study material
  static async generateVivaQuestions(
    machineId: number,
    numQuestions: number = 15,
    language: string = 'Hindi'
  ): Promise<{
    questions: Array<{
      level: number;
      question: string;
      expected_answer: string;
    }>;
    total: number;
  }> {
    const response = await apiClient.post('/generate_viva_questions', {
      machine_id: machineId,
      num_questions: numQuestions,
      language,
    });
    return response.data;
  }

  // NEW: Evaluate answer with expected answer
  static async evaluateWithAnswer(
    question: string,
    userAnswer: string,
    expectedAnswer: string,
    language: string = 'Hindi'
  ): Promise<{
    is_correct: boolean;
    is_partial?: boolean;
    score: number;
    feedback: string;
    correct_answer: string | null;
    user_said: string;
  }> {
    const response = await apiClient.post('/evaluate_with_answer', {
      question,
      user_answer: userAnswer,
      expected_answer: expectedAnswer,
      language,
    });
    return response.data;
  }

  // NEW: Get welcome message
  static async getWelcomeMessage(
    candidateName: string,
    machineName: string,
    language: string = 'Hindi'
  ): Promise<{ message: string }> {
    const response = await apiClient.post('/get_welcome', {
      candidate_name: candidateName,
      machine_name: machineName,
      language,
    });
    return response.data;
  }

  // NEW: Get viva summary
  static async getVivaSummary(
    questions: Array<{
      question: string;
      user_answer: string;
      expected_answer: string;
      score: number;
      is_correct: boolean;
      is_partial?: boolean;
    }>,
    language: string = 'Hindi'
  ): Promise<{
    total_questions: number;
    correct: number;
    partial: number;
    wrong: number;
    average_score: number;
    grade: string;
    improvements: Array<{
      question: string;
      your_answer: string;
      correct_answer: string;
    }>;
    message: string;
  }> {
    const response = await apiClient.post('/get_summary', {
      questions,
      language,
    });
    return response.data;
  }
}

// Error handling helper
export const handleAPIError = (error: any): string => {
  if (error.response) {
    // Server responded with error status
    return error.response.data.error || `Server error: ${error.response.status}`;
  } else if (error.request) {
    // Network error
    return 'Network error. Please check if the server is running.';
  } else {
    // Other error
    return error.message || 'An unexpected error occurred';
  }
};

export default VivaAPIService;