import type { ResumeData } from "../types";
import { BookOpen, Briefcase, User } from "lucide-react";

interface ResumeSummaryProps {
  resume: ResumeData | null;
  isLoading?: boolean;
}

function SectionEmptyState({ label }: { label: string }) {
  return <p className="app-summary__empty-copy">No {label.toLowerCase()} explicitly listed in the resume.</p>;
}

function normalizeSkills(skills: string[]) {
  return Array.from(
    new Set(
      skills.flatMap((skill) =>
        skill
          .split(/[,/;•|]+/)
          .map((part) => part.trim())
          .filter(Boolean),
      ),
    ),
  );
}

export default function ResumeSummary({ resume, isLoading }: ResumeSummaryProps) {
  const skills = Array.isArray(resume?.skills) ? normalizeSkills(resume.skills) : [];
  const experience = Array.isArray(resume?.experience) ? resume.experience : [];
  const education = Array.isArray(resume?.education) ? resume.education : [];
  const visibleSkills = skills.slice(0, 10);
  const remainingSkills = Math.max(skills.length - visibleSkills.length, 0);

  if (isLoading) {
    return (
      <div className="app-summary app-summary--loading">
        <div className="app-summary__skeleton app-summary__skeleton--title" />
        <div className="app-summary__skeleton" />
        <div className="app-summary__skeleton app-summary__skeleton--short" />
      </div>
    );
  }

  if (!resume) {
    return (
      <div className="app-summary app-summary--empty">
        <p className="app-summary__eyebrow">Candidate snapshot</p>
        <p className="app-summary__empty-copy">Upload a resume to see extracted skills, experience, and education.</p>
      </div>
    );
  }

  return (
    <div className="app-summary">
      <div className="app-summary__hero">
        <div className="app-summary__icon">
          <User size={18} />
        </div>
        <div>
          <p className="app-summary__eyebrow">Candidate Snapshot</p>
          <h2 className="app-summary__name">{resume.name}</h2>
          <p className="app-summary__muted">Extracted from the uploaded resume.</p>
        </div>
      </div>

      <div className="app-summary__stats">
        <div>
          <p className="app-summary__stat-label">Skills</p>
          <p className="app-summary__stat-value">{skills.length}</p>
        </div>
        <div>
          <p className="app-summary__stat-label">Experience</p>
          <p className="app-summary__stat-value">{experience.length}</p>
        </div>
        <div>
          <p className="app-summary__stat-label">Education</p>
          <p className="app-summary__stat-value">{education.length}</p>
        </div>
      </div>

      <section>
        <div className="app-summary__section-head">
          <h3 className="app-summary__section-title app-summary__section-title--indigo">Skills</h3>
          <span className="app-summary__section-note">Normalized from resume text</span>
        </div>
        {visibleSkills.length > 0 ? (
          <div className="app-summary__pills">
            {visibleSkills.map((skill) => (
              <span key={skill} className="app-summary__pill app-summary__pill--indigo">
                {skill}
              </span>
            ))}
            {remainingSkills > 0 && <span className="app-summary__pill">+{remainingSkills} more</span>}
          </div>
        ) : (
          <SectionEmptyState label="Skills" />
        )}
      </section>

      <section>
        <h3 className="app-summary__section-title app-summary__section-title--cyan">
          <Briefcase size={16} />
          Experience
        </h3>
        {experience.length > 0 ? (
          <ul className="app-summary__list">
            {experience.map((item, idx) => {
              const entry = typeof item === "string" ? item : item?.entry ?? "";

              return (
                <li key={`${entry || idx}`} className="app-summary__item">
                  {entry || "Experience listed in resume"}
                </li>
              );
            })}
          </ul>
        ) : (
          <SectionEmptyState label="Experience" />
        )}
      </section>

      <section>
        <h3 className="app-summary__section-title app-summary__section-title--fuchsia">
          <BookOpen size={16} />
          Education
        </h3>
        {education.length > 0 ? (
          <ul className="app-summary__list">
            {education.map((item, idx) => {
              const entry = typeof item === "string" ? item : item?.entry ?? "";

              return (
                <li key={`${entry || idx}`} className="app-summary__item app-summary__item--cyan">
                  {entry || "Education listed in resume"}
                </li>
              );
            })}
          </ul>
        ) : (
          <SectionEmptyState label="Education" />
        )}
      </section>
    </div>
  );
}