import { useEffect, useRef, useState } from "react";
import { Bot, Sparkles, Send } from "lucide-react";
import type { Message, ResumeData } from "../types";
import ChatMessage from "./ChatMessage";
import QuerySuggestions from "./QuerySuggestions";

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  resume?: ResumeData | null;
}

export default function ChatWindow({
  messages,
  onSendMessage,
  isLoading,
  resume,
}: ChatWindowProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [draft, setDraft] = useState("");

  const scrollToBottom = () => {
    const bodyElement = bodyRef.current;
    if (!bodyElement) {
      return;
    }

    bodyElement.scrollTo({
      top: bodyElement.scrollHeight,
      behavior: "smooth",
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const resizeInput = () => {
    const textarea = inputRef.current;
    if (!textarea) {
      return;
    }

    textarea.style.height = "0px";
    const nextHeight = Math.min(textarea.scrollHeight, 128);
    textarea.style.height = `${Math.max(nextHeight, 44)}px`;
  };

  useEffect(() => {
    resizeInput();
  }, [draft]);

  const handleSend = () => {
    const text = draft.trim();
    if (!text) {
      return;
    }

    onSendMessage(text);
    setDraft("");
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDraft(event.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasMessages = messages.length > 0;
  const showTypingIndicator = Boolean(isLoading && hasMessages && messages[messages.length - 1]?.role === "user");

  return (
    <div className="app-console">
      <div className="app-console__header">
        <div className="app-console__title-row">
          <span className="app-console__icon">
            <Bot size={18} />
          </span>
          <div>
            <h2 className="app-console__title">Assistant Console</h2>
          </div>
        </div>

        <div className="app-console__status-row">
          <span className="app-chip app-chip--indigo">
            {resume ? `Loaded: ${resume.name}` : "No resume loaded"}
          </span>
        </div>
      </div>

      <div className="app-console__body" ref={bodyRef}>
        <div className="app-console__top-prompts">
          <QuerySuggestions onSelect={onSendMessage} isLoading={isLoading} />
        </div>

        {!hasMessages ? (
          <div className="app-console__empty">
            <div className="app-console__empty-card">
              <div className="app-console__empty-row">
                <div className="app-console__empty-icon">
                  <Sparkles size={18} />
                </div>
                <div>
                  <p className="app-console__empty-title">
                    {resume ? "Resume loaded and ready." : "Upload a resume to begin."}
                  </p>
                  <p className="app-console__empty-copy">
                    {resume
                      ? "The assistant can summarize the candidate, assess fit, surface missing information, and answer follow-up questions with confidence scores."
                      : "Once a resume is uploaded, the assistant will show a candidate snapshot and enable structured analysis."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="app-message-stack">
            {messages.map((message, idx) => (
              <ChatMessage key={idx} message={message} />
            ))}
            {showTypingIndicator && (
              <div className="app-message app-message--assistant" aria-live="polite" aria-label="Assistant is typing">
                <div className="app-message__card app-message__card--assistant">
                  <div className="app-message__typing">
                    <span className="app-message__meta-label">Assistant</span>
                    <div className="app-message__typing-dots">
                      <span className="app-message__typing-dot" />
                      <span className="app-message__typing-dot" />
                      <span className="app-message__typing-dot" />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="app-console__footer">
        <div className="app-console__footer-stack">
          <div className="app-console__input-row">
            <textarea
              ref={inputRef}
              rows={1}
              placeholder="Ask about the candidate..."
              className="app-input app-textarea"
              value={draft}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading}
              className="app-button app-button--primary"
            >
              <Send size={16} />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}