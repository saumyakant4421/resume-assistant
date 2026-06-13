import type { Message } from "../types";
import ConfidenceBar from "./ConfidenceBar";
import SourceBadge from "./SourceBadge";
import MissingDataPills from "./MissingDataPills";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const evaluation = message.response?.evaluation;

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

            {evaluation && (
              <div className="app-evaluation">
                <div className="app-evaluation__section">
                  <p className="app-evaluation__title">Why this score</p>
                  <div className="app-evaluation__grid">
                    {Object.entries(evaluation.score_reasons).map(([category, reasons]) => (
                      <div key={category} className="app-evaluation__card">
                        <p className="app-evaluation__label">{category}</p>
                        <ul className="app-evaluation__list">
                          {reasons.map((reason) => (
                            <li key={reason}>{reason}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <MissingDataPills missing={message.response.missing_data} />
          </div>
        )}
      </div>
    </div>
  );
}