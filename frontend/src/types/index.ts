export type DocumentStatus =
  | "queued"
  | "processing"
  | "review_required"
  | "approved"
  | "rejected"
  | "blocked_duplicate"
  | "failed";

export type DecisionOutcome =
  | "auto_eligible"
  | "review_required"
  | "rejected"
  | "blocked_duplicate";

export interface DocumentItem {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  document_type: string;
  status: DocumentStatus;
  decision_outcome: DecisionOutcome | null;
  processing_attempts: number;
  uploaded_by: string | null;
  created_at: string;
  completed_at: string | null;
  confidence_score: number | null;
  supplier_name: string | null;
  total_amount: string | null;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardSummary {
  total_documents: number;
  queued: number;
  processing: number;
  review_required: number;
  approved: number;
  rejected: number;
  blocked_duplicate: number;
  failed: number;
}

export interface ProcessingMetrics {
  median_duration_ms: number;
  p95_duration_ms: number;
  success_rate: number;
  human_review_rate: number;
  duplicate_rate: number;
  average_confidence: number;
  total_processed_samples: number;
}

export interface ValidationIssue {
  code: string;
  severity: "critical" | "high" | "medium" | "low";
  field_path: string;
  message: string;
}

export interface RuleEvaluation {
  rule_code: string;
  rule_version: number;
  status: "passed" | "failed" | "skipped";
  severity: string;
  message: string;
  details: Record<string, any>;
}

export interface ReviewRevision {
  id: string;
  reviewer_id: string | null;
  action: string;
  corrected_data: Record<string, any>;
  comment: string | null;
  created_at: string;
}

export interface ReviewWorkspaceDetail {
  document_id: string;
  original_filename: string;
  mime_type: string;
  document_type: string;
  status: DocumentStatus;
  decision_outcome: DecisionOutcome | null;
  extracted_data: Record<string, any> | null;
  field_evidence: Record<string, any> | null;
  confidence_data: {
    document_score: number;
    assessment: string;
    signals: Record<string, any>;
    reasons: string[];
  } | null;
  validation_results: {
    is_valid: boolean;
    issues: ValidationIssue[];
  } | null;
  rule_evaluations: RuleEvaluation[];
  revisions: ReviewRevision[];
  created_at: string;
}

export interface BusinessRuleItem {
  id?: string;
  rule_code: string;
  name: string;
  description: string;
  document_type: string;
  severity: string;
  enabled: boolean;
  version: number;
  configuration: Record<string, any>;
}

export interface WebhookEndpointItem {
  id: string;
  name: string;
  url: string;
  subscribed_events: string[];
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebhookDeliveryLog {
  id: string;
  endpoint_id: string;
  event_id: string;
  event_type: string;
  status: string;
  attempt_count: number;
  last_http_status: number | null;
  last_error: string | null;
  created_at: string;
  delivered_at: string | null;
  payload: Record<string, any>;
}
