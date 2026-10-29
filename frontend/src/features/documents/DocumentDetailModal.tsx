import React, { useState, useEffect } from "react";
import { X, FileText, CheckCircle2, AlertTriangle, ShieldCheck, Download, Eye } from "lucide-react";
import { api } from "../../api/client";

interface DocumentDetailModalProps {
  documentId: string | null;
  onClose: () => void;
  onOpenReview: (id: string) => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  documentId,
  onClose,
  onOpenReview,
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!documentId) return;
    const fetchResults = async () => {
      try {
        setLoading(true);
        const res = await api.getDocumentResults(documentId);
        setData(res);
      } catch (err) {
        console.error("Failed to load document results:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [documentId]);

  if (!documentId) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "20px",
      }}
    >
      <div
        className="glass-panel-elevated"
        style={{
          width: "100%",
          maxWidth: "840px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "28px",
          position: "relative",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            background: "transparent",
            border: "none",
            color: "var(--text-muted)",
            cursor: "pointer",
          }}
        >
          <X size={20} />
        </button>

        {loading ? (
          <div style={{ padding: "60px 0", textAlign: "center", color: "var(--text-muted)" }}>
            Loading extraction results and decisions...
          </div>
        ) : !data ? (
          <div style={{ padding: "40px 0", textAlign: "center", color: "var(--accent-rose)" }}>
            Failed to load extraction details.
          </div>
        ) : (
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
              <FileText size={22} color="var(--primary)" />
              <h2 style={{ fontSize: "1.3rem", fontWeight: 800 }}>Document Inspection</h2>
              <span className={`status-pill status-${data.status}`}>
                {data.status.replace("_", " ")}
              </span>
              {data.decision_outcome && (
                <span
                  style={{
                    fontSize: "0.75rem",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "rgba(255, 255, 255, 0.08)",
                    fontWeight: 600,
                  }}
                >
                  Outcome: {data.decision_outcome}
                </span>
              )}
            </div>

            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "20px" }}>
              Document ID: {data.document_id} • Type: {data.document_type}
            </div>

            {/* Quick Actions */}
            <div style={{ display: "flex", gap: "10px", marginBottom: "24px" }}>
              <a
                href={api.getDocumentFileUrl(data.document_id)}
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
                style={{ fontSize: "0.8rem" }}
              >
                <Eye size={14} />
                View Original Document
              </a>
              {data.status === "review_required" && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenReview(data.document_id);
                  }}
                  className="btn btn-primary"
                  style={{ fontSize: "0.8rem" }}
                >
                  Open in Human Review Workspace
                </button>
              )}
            </div>

            {/* Confidence Banner */}
            {data.confidence_data && (
              <div
                style={{
                  background: "rgba(0,0,0,0.25)",
                  padding: "16px 20px",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-subtle)",
                  marginBottom: "24px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontWeight: 600 }}>
                    CONFIDENCE ASSESSMENT
                  </div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, marginTop: "2px" }}>
                    {Math.round(data.confidence_data.document_score * 100)}% (
                    <span style={{ textTransform: "capitalize", color: data.confidence_data.document_score >= 0.85 ? "#34d399" : "#fbbf24" }}>
                      {data.confidence_data.assessment}
                    </span>
                    )
                  </div>
                </div>
                {data.confidence_data.reasons && data.confidence_data.reasons.length > 0 && (
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", maxWidth: "420px", textAlign: "right" }}>
                    Reasons: {data.confidence_data.reasons.join(", ")}
                  </div>
                )}
              </div>
            )}

            {/* Extracted Fields Table */}
            <div style={{ marginBottom: "24px" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "12px" }}>
                Extracted Fields & Evidence
              </h3>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Extracted Value</th>
                      <th>Source</th>
                      <th>Evidence Snippet</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.extracted_data ? (
                      Object.entries(data.extracted_data).map(([key, val]) => {
                        if (typeof val === "object" && val !== null && !Array.isArray(val)) {
                          return Object.entries(val).map(([subK, subV]) => {
                            const fullKey = `${key}.${subK}`;
                            const ev = data.field_evidence ? data.field_evidence[fullKey] : null;
                            return (
                              <tr key={fullKey}>
                                <td style={{ fontWeight: 600, fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                                  {fullKey}
                                </td>
                                <td>{subV !== null ? String(subV) : "—"}</td>
                                <td>
                                  <span style={{ fontSize: "0.7rem", textTransform: "uppercase" }}>
                                    {ev ? ev.source : "parsed"}
                                  </span>
                                </td>
                                <td style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
                                  {ev ? ev.evidence_text : "—"}
                                </td>
                              </tr>
                            );
                          });
                        }
                        if (Array.isArray(val)) return null;
                        const ev = data.field_evidence ? data.field_evidence[key] : null;
                        return (
                          <tr key={key}>
                            <td style={{ fontWeight: 600, fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                              {key}
                            </td>
                            <td style={{ fontFamily: key.includes("amount") ? "var(--font-mono)" : undefined }}>
                              {val !== null ? String(val) : "—"}
                            </td>
                            <td>
                              <span style={{ fontSize: "0.7rem", textTransform: "uppercase" }}>
                                {ev ? ev.source : "parsed"}
                              </span>
                            </td>
                            <td style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
                              {ev ? ev.evidence_text : "—"}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={4} style={{ textAlign: "center", color: "var(--text-dim)" }}>
                          No structured data extracted.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Rule Evaluations */}
            <div>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <ShieldCheck size={18} color="var(--primary)" />
                Deterministic Rule Evaluations
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {data.rule_evaluations && data.rule_evaluations.length > 0 ? (
                  data.rule_evaluations.map((r: any, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        padding: "10px 14px",
                        borderRadius: "var(--radius-md)",
                        background: "rgba(0,0,0,0.2)",
                        border: "1px solid var(--border-subtle)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        fontSize: "0.8rem",
                      }}
                    >
                      <div>
                        <span style={{ fontWeight: 600 }}>{r.rule_code}</span>: {r.message}
                      </div>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          fontWeight: 700,
                          textTransform: "uppercase",
                          color:
                            r.status === "passed"
                              ? "var(--accent-emerald)"
                              : r.status === "failed"
                              ? "var(--accent-rose)"
                              : "var(--text-dim)",
                        }}
                      >
                        {r.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <div style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}>
                    No rule evaluations recorded.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
