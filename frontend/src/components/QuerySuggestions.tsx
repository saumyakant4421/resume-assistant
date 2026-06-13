import { MessageCircle } from "lucide-react";

interface QuerySuggestionsProps {
  onSelect: (query: string) => void;
  isLoading?: boolean;
}

const suggestions = [
  "Summarize candidate",
  "Evaluate candidate",
  "What are the strongest skills?",
  "What experience is relevant?",
];

export default function QuerySuggestions({ onSelect, isLoading }: QuerySuggestionsProps) {
  return (
    <div className="app-prompts">
      <div className="app-prompts__label">
        <MessageCircle size={14} />
        Suggested prompts
      </div>

      <div className="app-prompts__grid">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSelect(suggestion)}
            disabled={isLoading}
            className="app-prompts__button"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}