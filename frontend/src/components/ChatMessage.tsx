import type { Message } from "../types";
import ConfidenceBar from "./ConfidenceBar";
import SourceBadge from "./SourceBadge";
import MissingDataPills from "./MissingDataPills";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`app-message app-message--${isUser ? "user" : "assistant"}`}>
      <div className={`app-message__card app-message__card--${isUser ? "user" : "assistant"}`}>
        <p className="app-message__body">{message.content}</p>

        {!isUser && message.response && (
          <div className="app-message__meta">
            <div className="app-message__meta-row">
              <span className="app-message__meta-label">Source</span>
              <SourceBadge source={message.response.source} />
            </div>

            <ConfidenceBar confidence={message.response.confidence} />

            <MissingDataPills missing={message.response.missing_data} />
          </div>
        )}
      </div>
    </div>
  );
}