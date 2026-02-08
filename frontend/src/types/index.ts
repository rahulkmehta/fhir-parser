export interface PatientSummary {
  id: string;
  full_name: string;
  gender: string;
  birth_date: string | null;
  age: number | null;
  city: string | null;
  state: string | null;
  is_deceased: boolean;
}

export interface PatientListResponse {
  patients: PatientSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ConditionSummary {
  id: string;
  code: string;
  display: string;
  clinical_status: string;
  onset_date: string | null;
}

export interface ObservationSummary {
  id: string;
  code: string;
  display: string;
  value: string | null;
  value_numeric: number | null;
  date: string | null;
  category: string | null;
}

export interface ProcedureSummary {
  id: string;
  code: string;
  display: string;
  status: string;
  performed_date: string | null;
}

export interface ClinicalSnapshot {
  patient: PatientSummary;
  active_conditions: ConditionSummary[];
  recent_procedures: ProcedureSummary[];
  key_observations: {
    bmi: ObservationSummary | null;
    systolic_bp: ObservationSummary | null;
    diastolic_bp: ObservationSummary | null;
    weight: ObservationSummary | null;
    height: ObservationSummary | null;
  };
  missing_data: string[];
}

export interface TimelineEntry {
  resource_type: string;
  resource_id: string;
  display_name: string;
  date: string | null;
  detail: string | null;
}

export interface TimelineResponse {
  entries: TimelineEntry[];
  total: number;
}

// --- Eligibility ---

export interface EvidenceItem {
  resource_type: string;
  resource_id: string;
  display: string | null;
  code: string | null;
  date: string | null;
}

export interface EligibilityCriterion {
  criterion: string;
  met: boolean;
  evidence: EvidenceItem[];
  reason: string | null;
}

export interface EligibilityResult {
  patient_id: string;
  status: "eligible" | "not_eligible" | "unknown";
  reasons: string[];
  criteria: EligibilityCriterion[];
  bmi_value: number | null;
}

export interface CohortReportCategory {
  count: number;
  percentage: number;
  patient_ids: string[];
}

export interface UnknownReason {
  reason: string;
  count: number;
  percentage: number;
}

export interface CohortReport {
  total_patients: number;
  eligible: CohortReportCategory;
  not_eligible: CohortReportCategory;
  unknown: CohortReportCategory;
  top_unknown_reasons: UnknownReason[];
}
