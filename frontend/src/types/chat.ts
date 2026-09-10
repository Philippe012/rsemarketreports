export type ChatRole = 'user' | 'assistant';

export type ChatConfidence = 'high' | 'medium' | 'low' | '';

export interface ChatSource {
  label: string;
  detail: string;
}

export interface ChatMessage {
  id: number;
  role: ChatRole;
  content: string;
  sources: ChatSource[];
  confidence: ChatConfidence;
  created_at: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
  suggested_questions: string[];
}

export interface ChatSendResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
}
