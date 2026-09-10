import { MessageCircle, Send, X } from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';

import { useDocumentChat } from '../../hooks/useDocumentChat';
import { Spinner } from '../common/Spinner';
import type { ChatMessage } from '../../types/chat';

const CONFIDENCE_NOTE: Record<string, string | null> = {
  low: null, 
  medium: 'Best match found in this document — double-check against the source.',
  high: null,
};

function SourceChips({ sources }: { sources: ChatMessage['sources'] }) {
  if (sources.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((source, i) => (
        <span
          key={i}
          className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium"
          style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', background: 'var(--bg-subtle)' }}
        >
          {source.label}
          {source.detail && <span style={{ color: 'var(--text-muted)' }}>&nbsp;· {source.detail}</span>}
        </span>
      ))}
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const note = CONFIDENCE_NOTE[message.confidence] ?? null;
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] ${isUser ? '' : 'w-full'}`}>
        <div
          className="rounded-lg px-3.5 py-2.5 text-sm leading-relaxed"
          style={
            isUser
              ? { background: 'var(--brand)', color: 'var(--brand-contrast)' }
              : { background: 'var(--bg-subtle)', color: 'var(--text)', border: '1px solid var(--border)' }
          }
        >
          {message.content}
        </div>
        {!isUser && <SourceChips sources={message.sources} />}
        {!isUser && note && (
          <p className="mt-1 text-[11px]" style={{ color: 'var(--text-muted)' }}>{note}</p>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div
        className="flex items-center gap-1 rounded-lg px-3.5 py-3"
        style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border)' }}
        aria-label="Thinking"
      >
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-pulse rounded-full"
            style={{ background: 'var(--text-muted)', animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

export function DocumentChat({ reportId, documentTitle }: { reportId: string; documentTitle: string }) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const { messages, suggestions, loadingHistory, sending, error, loadHistory, send } = useDocumentChat(reportId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) loadHistory();
  }, [open, loadHistory]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, sending]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!draft.trim() || sending) return;
    void send(draft);
    setDraft('');
  };

  const handleSuggestion = (question: string) => {
    if (sending) return;
    void send(question);
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-4 z-40 flex items-center gap-2 rounded-full px-4 py-3 text-sm font-semibold shadow-lg transition hover:opacity-90 sm:bottom-6 sm:right-6"
        style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
        aria-label="Ask this document"
      >
        <MessageCircle size={17} />
        <span className="hidden sm:inline">Ask this document</span>
      </button>
    );
  }

  return (
    <div
      className="fixed inset-x-0 bottom-0 z-40 flex max-h-[80vh] flex-col rounded-t-lg border shadow-lg animate-fade-in sm:inset-x-auto sm:bottom-6 sm:right-6 sm:max-h-[600px] sm:w-[400px] sm:rounded-lg"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
      role="dialog"
      aria-label="Ask this document"
    >
      <div className="flex items-center justify-between gap-3 border-b px-4 py-3" style={{ borderColor: 'var(--border)' }}>
        <div className="min-w-0">
          <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Ask this document</p>
          <p className="truncate text-xs" style={{ color: 'var(--text-secondary)' }}>{documentTitle}</p>
        </div>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition hover:opacity-70"
          style={{ color: 'var(--text-secondary)' }}
          aria-label="Close"
        >
          <X size={17} />
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {loadingHistory && (
          <div className="flex justify-center py-6">
            <Spinner size={20} />
          </div>
        )}

        {!loadingHistory && messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              Ask about any figure, section, or dataset in this document. Answers are grounded in what was actually extracted from it.
            </p>
          </div>
        )}

        {!loadingHistory && messages.map((message) => <MessageBubble key={message.id} message={message} />)}
        {sending && <TypingIndicator />}
      </div>

      {!loadingHistory && suggestions.length > 0 && messages.length === 0 && (
        <div className="flex flex-wrap gap-1.5 border-t px-4 py-3" style={{ borderColor: 'var(--border)' }}>
          {suggestions.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => handleSuggestion(question)}
              className="rounded-full border px-2.5 py-1 text-xs font-medium transition hover:opacity-80"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
            >
              {question}
            </button>
          ))}
        </div>
      )}

      {error && (
        <p className="border-t px-4 py-2 text-xs" style={{ borderColor: 'var(--border)', color: 'var(--negative)' }}>
          {error}
        </p>
      )}

      <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t p-3" style={{ borderColor: 'var(--border)' }}>
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask a question about this document…"
          disabled={sending}
          className="flex-1 rounded-lg border px-3 py-2 text-sm outline-none transition focus:ring-2 disabled:opacity-60"
          style={{ background: 'var(--bg-subtle)', borderColor: 'var(--border)', color: 'var(--text)' }}
        />
        <button
          type="submit"
          disabled={sending || !draft.trim()}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition hover:opacity-90 disabled:opacity-50"
          style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
          aria-label="Send"
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}
