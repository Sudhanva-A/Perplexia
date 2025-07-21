// src/types/index.ts

export interface User {
  id: number;
  email: string;
  username: string;
}

export interface ChatMessage {
  id: number;
  content: string;
  is_user_message: boolean;
  created_at: string;
  searchData?: any;
}

export interface ChatSession {
  id: number;
  name: string;
  created_at: string;
  message_count?: number;
  messages?: ChatMessage[];
}

export interface PdfDocument {
  id: number;
  filename: string;
  upload_date: string;
}

export interface ChatRequest {
  message: string;
  session_id?: number;
}
