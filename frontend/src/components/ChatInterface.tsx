import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import config from '../config';
import './ChatInterface.css';

interface ChatInterfaceProps {
  jobId: string | null;
  jobData: any;
}

interface Message {
  type: 'user' | 'agent' | 'system';
  message: string;
  timestamp: Date;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ jobId, jobData }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initial welcome message
    if (messages.length === 0) {
      setMessages([
        {
          type: 'agent',
          message: 'Hi! I\'m your Section 8 form filling assistant. Upload an Excel file to get started, then ask me to "start filling" the applications.',
          timestamp: new Date()
        }
      ]);
    }
  }, []);

  useEffect(() => {
    // Set up WebSocket connection when jobId is available
    if (jobId && !wsConnection) {
      const ws = new WebSocket(`${config.wsUrl}/ws/${jobId}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnection(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'progress') {
          setMessages(prev => [...prev, {
            type: 'system',
            message: `Progress Update: ${data.progress} completed (${data.completed_rows}/${data.total_rows})${data.errors > 0 ? `, ${data.errors} errors` : ''}`,
            timestamp: new Date()
          }]);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnection(null);
      };
    }

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [jobId]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      type: 'user',
      message: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${config.apiUrl}/chat`, {
        message: inputMessage,
        job_id: jobId
      });

      const agentMessage: Message = {
        type: 'agent',
        message: response.data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, agentMessage]);

      // If user asked to start, trigger the job
      if (inputMessage.toLowerCase().includes('start') && jobId) {
        try {
          await axios.post(`${config.apiUrl}/jobs/${jobId}/start`);
        } catch (error) {
          console.error('Failed to start job:', error);
        }
      }

    } catch (error: any) {
      const errorMessage: Message = {
        type: 'agent',
        message: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString();
  };

  const getQuickActions = () => {
    if (!jobId) return [];
    
    return [
      'Start filling applications',
      'Show current status',
      'Show errors',
      'Help'
    ];
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Chat with Agent</h2>
        {jobId && (
          <div className="job-info">
            <span className="job-id">Job: {jobId.substring(0, 8)}...</span>
            {jobData && <span className="row-count">{jobData.preview?.length || 0} rows</span>}
          </div>
        )}
      </div>

      <div className="messages-container">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.type}`}
          >
            <div className="message-content">
              <div className="message-text">{message.message}</div>
              <div className="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message agent loading">
            <div className="message-content">
              <div className="message-text">Thinking...</div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {getQuickActions().length > 0 && (
        <div className="quick-actions">
          {getQuickActions().map((action) => (
            <button
              key={action}
              className="quick-action-btn"
              onClick={() => setInputMessage(action)}
              disabled={isLoading}
            >
              {action}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={sendMessage} className="message-form">
        <div className="input-container">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="message-input"
          />
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;