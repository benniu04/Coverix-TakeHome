import { useEffect, useRef } from 'react';
import { useChat } from './hooks/useChat';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { TypingIndicator } from './components/TypingIndicator';
import { ProgressIndicator } from './components/ProgressIndicator';
import './App.css';

function App() {
  const {
    sessionId,
    messages,
    currentState,
    isComplete,
    isLoading,
    error,
    startConversation,
    sendMessage,
    resetChat,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sessionId) {
      startConversation();
    }
  }, [sessionId, startConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="app">
      <div className="background-pattern">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>
      
      <header className="app-header">
        <div className="header-shine"></div>
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="currentColor" className="logo-icon">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <div className="logo-text-container">
              <span className="logo-text">InsureMe</span>
              <span className="logo-tagline">AI-Powered Insurance Assistant</span>
            </div>
          </div>
          <div className="header-info">
            <div className="status-indicator">
              <div className="status-dot"></div>
              <span className="status-text">Live</span>
            </div>
            <span className="badge">
              <svg viewBox="0 0 24 24" fill="currentColor" className="badge-icon">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
              </svg>
              Secure & Encrypted
            </span>
          </div>
        </div>
      </header>

      <main className="chat-container">
        {sessionId && (
          <ProgressIndicator currentState={currentState} isComplete={isComplete} />
        )}
        
        <div className="messages-area">
          {error && (
            <div className="error-banner">
              <svg viewBox="0 0 24 24" fill="currentColor" className="error-icon">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
              <span>{error}</span>
              <button onClick={startConversation} className="retry-btn">Retry</button>
            </div>
          )}
          
          <div className="messages-list">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {isComplete ? (
          <div className="completion-banner">
            <div className="confetti">
              {[...Array(20)].map((_, i) => (
                <div key={i} className="confetti-piece" style={{
                  '--delay': `${i * 0.1}s`,
                  '--x': `${Math.random() * 100}%`,
                  '--rotation': `${Math.random() * 360}deg`
                } as React.CSSProperties}></div>
              ))}
            </div>
            <div className="completion-content">
              <svg viewBox="0 0 24 24" fill="currentColor" className="completion-icon">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              <div>
                <h3>Onboarding Complete!</h3>
                <p>Thank you for providing your information.</p>
              </div>
            </div>
            <button onClick={resetChat} className="new-session-btn">
              Start New Session
            </button>
          </div>
        ) : (
          <ChatInput
            onSendMessage={sendMessage}
            disabled={isLoading || !sessionId}
            placeholder={isLoading ? "Please wait..." : "Type your response..."}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>Your data is encrypted and secure. By continuing, you agree to our Terms of Service.</p>
      </footer>
    </div>
  );
}

export default App;
