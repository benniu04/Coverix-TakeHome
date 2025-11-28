import { useState, useCallback } from 'react';
import type { Message, ChatResponse, StartConversationResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export function useChat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentState, setCurrentState] = useState<string>('');
  const [isComplete, setIsComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startConversation = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversation/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to start conversation');
      }

      const data: StartConversationResponse = await response.json();
      
      setSessionId(data.session_id);
      setCurrentState(data.current_state);
      setMessages([{
        id: Date.now(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString(),
      }]);
      setIsComplete(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start conversation');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!sessionId || !content.trim()) return;

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: content.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data: ChatResponse = await response.json();

      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setCurrentState(data.current_state);
      setIsComplete(data.is_complete);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const resetChat = useCallback(async () => {
    setSessionId(null);
    setMessages([]);
    setCurrentState('');
    setIsComplete(false);
    setIsLoading(false);
    setError(null);
    // Automatically start a new conversation
    await startConversation();
  }, [startConversation]);

  return {
    sessionId,
    messages,
    currentState,
    isComplete,
    isLoading,
    error,
    startConversation,
    sendMessage,
    resetChat,
  };
}

