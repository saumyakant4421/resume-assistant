interface ConfidenceBarProps {
  confidence: number;
}

export default function ConfidenceBar({ confidence }: ConfidenceBarProps) {
  const percentage = Math.round(confidence * 100);
  const colorClass =
    confidence >= 0.7 ? "app-confidence__fill--good" : confidence >= 0.5 ? "app-confidence__fill--mid" : "app-confidence__fill--low";

  return (
    <div className="app-confidence">
      <div className="app-confidence__header">
        <span>Confidence</span>
        <span>{percentage}%</span>
      </div>
      <div className="app-confidence__track">
        <div className={`app-confidence__fill ${colorClass}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}