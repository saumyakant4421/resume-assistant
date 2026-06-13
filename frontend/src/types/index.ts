export interface ResumeEntry {
  entry: string;
}

export interface ResumeData {
  name: string;
  skills: string[];
  experience: ResumeEntry[];
  education: ResumeEntry[];
  raw_text: string;
}

export interface AgentResponse {
  answer: string;
  confidence: number;
  source: "resume" | "inference";
  missing_data: string[];
  evaluation?: EvaluationInsights;
}

export interface EvaluationRoleFit {
  role: string;
  fit_percent: number;
  reasons: string[];
}

export interface EvaluationInsights {
  score_reasons: Record<string, string[]>;
  role_fits: EvaluationRoleFit[];
  top_recommendation: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  response?: AgentResponse;
}

export interface UploadResumeResponse {
  status: string;
  message: string;
  data: ResumeData;
}

export interface ChatRequest {
  query: string;
}

export interface MemoryContext {
  resume: ResumeData | null;
  history: Message[];
  message_count: number;
  last_subject: string;
  current_intent: string;
  tool_usage: Array<{
    tool_name: string;
    intent: string;
    reason: string;
  }>;
  decision_log: Array<{
    intent: string;
    tool_used: string;
    reason: string;
  }>;
}

export interface ResetResponse {
  status: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}