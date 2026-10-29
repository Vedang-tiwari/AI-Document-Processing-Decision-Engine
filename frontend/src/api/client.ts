import {
  DashboardSummary,
  ProcessingMetrics,
  DocumentListResponse,
  DocumentItem,
  ReviewWorkspaceDetail,
  BusinessRuleItem,
  WebhookEndpointItem,
  WebhookDeliveryLog,
} from "../types";

const BASE_URL = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.error && errorJson.error.message) {
        errorMsg = errorJson.error.message;
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Dashboard
  getSummary: () => request<DashboardSummary>("/dashboard/summary"),
  getMetrics: () => request<ProcessingMetrics>("/dashboard/processing-metrics"),
  getRecentErrors: () => request<any[]>("/dashboard/recent-errors"),

  // Documents
  listDocuments: (params?: {
    status?: string;
    document_type?: string;
    page?: number;
    page_size?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.status) sp.set("status", params.status);
    if (params?.document_type) sp.set("document_type", params.document_type);
    if (params?.page) sp.set("page", params.page.toString());
    if (params?.page_size) sp.set("page_size", params.page_size.toString());
    const qs = sp.toString();
    return request<DocumentListResponse>(`/documents${qs ? `?${qs}` : ""}`);
  },

  getDocument: (id: string) => request<any>(`/documents/${id}`),
  getDocumentResults: (id: string) => request<any>(`/documents/${id}/results`),

  uploadDocument: async (file: File, documentType?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    if (documentType) {
      formData.append("document_type", documentType);
    }
    return request<{ document_id: string; status: string; message: string }>(
      "/documents",
      {
        method: "POST",
        body: formData,
      }
    );
  },

  retryDocument: (id: string) =>
    request<{ document_id: string; status: string; message: string }>(
      `/documents/${id}/retry`,
      { method: "POST" }
    ),

  getDocumentFileUrl: (id: string) => `${BASE_URL}/documents/${id}/file`,

  // Reviews
  listReviewQueue: (page = 1, pageSize = 20) =>
    request<{ items: any[]; total: number; page: number; page_size: number }>(
      `/reviews?page=${page}&page_size=${pageSize}`
    ),

  getReviewDetail: (id: string) => request<ReviewWorkspaceDetail>(`/reviews/${id}`),

  submitCorrections: (id: string, corrections: Record<string, any>, comment?: string) =>
    request<{ status: string; message: string }>(`/reviews/${id}/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ corrections, comment }),
    }),

  submitDecision: (id: string, decision: "approved" | "rejected", comment?: string) =>
    request<{ document_id: string; status: string; decision: string; message: string }>(
      `/reviews/${id}/decision`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, comment }),
      }
    ),

  // Rules
  listRules: () => request<BusinessRuleItem[]>("/rules"),
  patchRule: (ruleCode: string, data: { enabled?: boolean; configuration?: any }) =>
    request<any>(`/rules/${ruleCode}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  // Webhooks
  listWebhooks: () => request<WebhookEndpointItem[]>("/webhooks"),
  createWebhook: (data: { name: string; url: string; subscribed_events?: string[]; enabled?: boolean }) =>
    request<any>("/webhooks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  deleteWebhook: (id: string) =>
    request<void>(`/webhooks/${id}`, { method: "DELETE" }),
  listDeliveries: (webhookId: string) =>
    request<WebhookDeliveryLog[]>(`/webhooks/${webhookId}/deliveries`),
  retryDelivery: (webhookId: string, deliveryId: string) =>
    request<any>(`/webhooks/${webhookId}/deliveries/${deliveryId}/retry`, {
      method: "POST",
    }),
};
