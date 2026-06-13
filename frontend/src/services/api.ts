import axios from "axios";
import type {
  AgentResponse,
  ChatRequest,
  HealthResponse,
  MemoryContext,
  ResetResponse,
  UploadResumeResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL?.trim() || "http://localhost:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
});

export { API_BASE_URL };

export const uploadResume = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  return API.post<UploadResumeResponse>("/upload-resume", formData);
};

export const sendMessage = async (query: string) => {
  const payload: ChatRequest = { query };
  return API.post<AgentResponse>("/chat", payload);
};

export const getMemory = async () => {
  return API.get<MemoryContext>("/memory");
};

export const resetConversation = async () => {
  return API.post<ResetResponse>("/reset");
};

export const checkHealth = async () => {
  return API.get<HealthResponse>("/health");
};