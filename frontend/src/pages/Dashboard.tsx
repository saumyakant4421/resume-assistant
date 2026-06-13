import { useEffect, useState } from "react";
import { AlertCircle, RefreshCw, ShieldCheck } from "lucide-react";
import type { HealthResponse, MemoryContext, Message, ResumeData } from "../types";
import {
  checkHealth,
  getMemory,
  resetConversation,
  sendMessage,
  uploadResume,
} from "../services/api";
import ResumeUpload from "../components/ResumeUpload";
import ResumeSummary from "../components/ResumeSummary";
import ChatWindow from "../components/ChatWindow";
import CareerPathPanel from "../components/CareerPathPanel";

function sanitizeAssistantContent(content: string) {
  return content
    .replace(/\r\n/g, "\n")
    .split("\n")
    .filter((line) => !/Gemini AI is disabled|Set GEMINI_API_KEY|⚠️\s*NOTE:/i.test(line))
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export default function Dashboard() {
  const [resume, setResume] = useState<ResumeData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [memory, setMemory] = useState<MemoryContext | null>(null);
  const latestEvaluation = [...messages]
    .reverse()
    .find((message) => message.role === "assistant" && message.response?.evaluation)
    ?.response?.evaluation ?? null;

  useEffect(() => {
    const syncBackendState = async () => {
      try {
        const [healthResponse, memoryResponse] = await Promise.all([
          checkHealth(),
          getMemory(),
        ]);

        setHealth(healthResponse.data);
        setMemory(memoryResponse.data);
        setResume(memoryResponse.data.resume);
        setMessages(
          memoryResponse.data.history.map((message) =>
            message.role === "assistant"
              ? { ...message, content: sanitizeAssistantContent(message.content) || message.content.trim() }
              : message,
          ),
        );
      } catch (err) {
        console.error(err);
      }
    };

    syncBackendState();
  }, []);

  const handleResumeUpload = async (file: File) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await uploadResume(file);
      setResume(response.data.data);
      setMessages([]);
      setMemory(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to upload resume.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (query: string) => {
    if (!resume) {
      setError("Upload a resume first.");
      return;
    }

    if (!query.trim()) {
      setError("Type a question before sending.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      setMessages((prev) => [...prev, { role: "user", content: query }]);

      const response = await sendMessage(query);
      const assistantContent = sanitizeAssistantContent(response.data.answer) || response.data.answer.trim();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: assistantContent,
          response: response.data,
        },
      ]);

      const memoryResponse = await getMemory();
      setMemory(memoryResponse.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to get a response.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      setIsLoading(true);
      setError(null);
      await resetConversation();
      setResume(null);
      setMessages([]);
      setMemory(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to reset the conversation.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const backendReady = Boolean(health);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-container app-header__inner">
          <div className="app-header__brand">
            <div>
              <p className="app-kicker">
                Resume Assistant
              </p>
              <h1 className="app-title">
                Intelligent Resume Assistant
              </h1>
            </div>

            <div className="app-header__status">
              <span className={`app-pill ${backendReady ? "app-pill--success" : "app-pill--info"}`}>
                <ShieldCheck size={14} />
                {health ? health.service : "Connecting to backend"}
              </span>
              <span className="app-pill app-pill--warning">
                Messages: {memory?.message_count ?? messages.length}
              </span>
              <button
                type="button"
                onClick={handleReset}
                disabled={isLoading}
                className="app-button app-button--ghost app-button--compact"
              >
                <RefreshCw size={14} />
                Reset
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="app-container app-main">
        {error && (
          <div className="app-alert">
            <AlertCircle className="mt-0.5 flex-shrink-0" size={18} />
            <p>{error}</p>
          </div>
        )}

        <div className="app-layout">
          <section className="app-sidebar">
            <div className="app-panel app-panel--upload">
              <ResumeUpload onUpload={handleResumeUpload} isLoading={isLoading} />
            </div>

            <div className="app-panel app-panel--summary">
              <ResumeSummary resume={resume} isLoading={isLoading && !resume} />
            </div>
          </section>

          <section className="app-conversation-column">
            <div className="app-chat-stage">
              <ChatWindow
                messages={messages}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                resume={resume}
              />
            </div>

            <CareerPathPanel resume={resume} evaluation={latestEvaluation} />
          </section>
        </div>
      </main>
    </div>
  );
}