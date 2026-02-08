import type {
  PatientListResponse,
  PatientSummary,
  ClinicalSnapshot,
  TimelineResponse,
  EligibilityResult,
  CohortReport,
  AIReviewResponse,
} from "@/types";

const API_BASE = "http://localhost:8000/api";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function getPatients(
  q: string = "",
  page: number = 1,
  pageSize: number = 20
): Promise<PatientListResponse> {
  const params = new URLSearchParams({
    q,
    page: String(page),
    page_size: String(pageSize),
  });
  return fetchJSON(`${API_BASE}/patients?${params}`);
}

export function getPatient(id: string): Promise<PatientSummary> {
  return fetchJSON(`${API_BASE}/patients/${id}`);
}

export function getSnapshot(id: string): Promise<ClinicalSnapshot> {
  return fetchJSON(`${API_BASE}/patients/${id}/snapshot`);
}

export function getTimeline(
  id: string,
  page: number = 1,
  pageSize: number = 50
): Promise<TimelineResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  return fetchJSON(`${API_BASE}/patients/${id}/timeline?${params}`);
}

export function getEligibility(id: string): Promise<EligibilityResult> {
  return fetchJSON(`${API_BASE}/patients/${id}/eligibility`);
}

export function getCohortReport(): Promise<CohortReport> {
  return fetchJSON(`${API_BASE}/cohort`);
}

export async function requestAIReview(id: string): Promise<AIReviewResponse> {
  const res = await fetch(`${API_BASE}/patients/${id}/ai-review`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
