import { apiClient } from './client';
import type { ChatHistoryResponse, ChatSendResponse } from '../types/chat';

export async function getChatHistory(reportId: string): Promise<ChatHistoryResponse> {
  const response = await apiClient.get<ChatHistoryResponse>(`/api/reports/${reportId}/chat/`);
  return response.data;
}

export async function sendChatMessage(reportId: string, message: string): Promise<ChatSendResponse> {
  const response = await apiClient.post<ChatSendResponse>(`/api/reports/${reportId}/chat/`, { message });
  return response.data;
}
