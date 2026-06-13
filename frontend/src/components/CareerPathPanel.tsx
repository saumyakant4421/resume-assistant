import { Target } from "lucide-react";
import type { EvaluationInsights, ResumeData } from "../types";

interface CareerPathPanelProps {
  resume?: ResumeData | null;
  evaluation?: EvaluationInsights | null;
}

function getFallbackMessage(resume?: ResumeData | null) {
  if (!resume) {
    return "Upload a resume first, then run an evaluation to see career-fit guidance.";
  }

  return "Run an Evaluate Candidate query to generate role-fit percentages.";
}

export default function CareerPathPanel({ resume, evaluation }: CareerPathPanelProps) {
  const topRoles = evaluation?.role_fits ?? [];
  const hasRoles = topRoles.length > 0;

  return (
    <section className="app-panel app-career-panel">
      <div className="app-career-panel__header">
        <div className="app-career-panel__icon">
          <Target size={18} />
        </div>
        <div>
          <p className="app-summary__eyebrow">Career direction</p>
          <h3 className="app-career-panel__title">Best-fit role match</h3>
          <p className="app-career-panel__copy">{evaluation?.top_recommendation || getFallbackMessage(resume)}</p>
        </div>
      </div>

      {hasRoles ? (
        <div className="app-career-panel__roles">
          {topRoles.map((item) => (
            <div key={item.role} className="app-career-panel__role">
              <div className="app-career-panel__role-head">
                <span className="app-career-panel__role-name">{item.role}</span>
                <span className="app-career-panel__role-percent">{Math.round(item.fit_percent)}%</span>
              </div>
              <div className="app-career-panel__track">
                <div className="app-career-panel__fill" style={{ width: `${Math.max(8, item.fit_percent)}%` }} />
              </div>
              <ul className="app-career-panel__reasons">
                {item.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : (
        <p className="app-career-panel__empty">{getFallbackMessage(resume)}</p>
      )}
    </section>
  );
}