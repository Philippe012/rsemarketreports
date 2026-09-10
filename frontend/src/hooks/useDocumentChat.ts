import { useCallback, useRef, useState } from 'react';

import { getChatHistory, sendChatMessage } from '../api/chat';
import { getApiErrorMessage } from '../api/client';
import type { ChatMessage } from '../types/chat';

export function useDocumentChat(reportId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadedRef = useRef(false);

  const loadHistory = useCallback(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    setLoadingHistory(true);
    setError(null);
    getChatHistory(reportId)
      .then((data) => {
        setMessages(data.messages);
        setSuggestions(data.suggested_questions);
      })
      .catch((err) => {
        loadedRef.current = false;
        setError(getApiErrorMessage(err));
      })
      .finally(() => setLoadingHistory(false));
  }, [reportId]);

  const send = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || sending) return;
      setSending(true);
      setError(null);
      try {
        const result = await sendChatMessage(reportId, trimmed);
        setMessages((prev) => [...prev, result.user_message, result.assistant_message]);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setSending(false);
      }
    },
    [reportId, sending],
  );

  return { messages, suggestions, loadingHistory, sending, error, loadHistory, send };
}
