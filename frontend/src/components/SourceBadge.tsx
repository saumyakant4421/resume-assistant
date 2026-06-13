interface SourceBadgeProps {
  source: string;
}

export default function SourceBadge({ source }: SourceBadgeProps) {
  const isResume = source.toLowerCase() === "resume";

  return (
    <span className={`app-source-badge ${isResume ? "app-source-badge--resume" : "app-source-badge--inference"}`}>
      {isResume ? "Resume" : "Inference"}
    </span>
  );
}
