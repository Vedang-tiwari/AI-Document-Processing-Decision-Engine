import React, { useEffect, useState } from "react";
import {
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle,
  Copy,
  XCircle,
  Zap,
  TrendingUp,
  Activity,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { api } from "../../api/client";
import { DashboardSummary, ProcessingMetrics, DocumentItem } from "../../types";

interface DashboardViewProps {
  onSelectDocument: (id: string) => void;
  onOpenReviewQueue: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onSelectDocument,
  onOpenReviewQueue,
}) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [metrics, setMetrics] = useState<ProcessingMetrics | null>(null);
  const [recentDocs, setRecentDocs] = useState<DocumentItem[]>([]);
  const [recentErrors, setRecentErrors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sumRes, metRes, docsRes, errRes] = await Promise.all([
        api.getSummary(),
        api.getMetrics(),
        api.listDocuments({ page: 1, page_size: 5 }),
        api.getRecentErrors(),
      ]);
      setSummary(sumRes);
      setMetrics(metRes);
      setRecentDocs(docsRes.items);
      setRecentErrors(errRes);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div>
      {/* Top Banner */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "28px",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.03em" }}>
            Operational Overview
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "4px" }}>
            Real-time document ingestion throughput, machine learning extraction confidence, and deterministic decision metrics.
          </p>
        </div>
        <button onClick={fetchData} className="btn btn-secondary" disabled={loading}>
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh Metrics
        </button>
      </div>

      {/* KPI Cards Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        <div className="metric-card">
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>TOTAL RECEIVED</span>
            <FileText size={18} color="var(--primary)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, marginTop: "8px" }}>
            {summary?.total_documents ?? 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "4px" }}>
            All incoming documents
          </div>
        </div>

        <div className="metric-card">
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>PROCESSING</span>
            <Activity size={18} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, marginTop: "8px", color: "var(--accent-cyan)" }}>
            {(summary?.processing ?? 0) + (summary?.queued ?? 0)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "4px" }}>
            {summary?.queued ?? 0} queued, {summary?.processing ?? 0} active
          </div>
        </div>

        <div
          className="metric-card"
          style={{ borderColor: summary?.review_required ? "rgba(245, 158, 11, 0.4)" : undefined }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>HUMAN REVIEW</span>
            <AlertTriangle size={18} color="var(--accent-amber)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, marginTop: "8px", color: "var(--accent-amber)" }}>
            {summary?.review_required ?? 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "4px" }}>
            Discrepancies / Low confidence
          </div>
        </div>

        <div className="metric-card">
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>AUTO APPROVED</span>
            <CheckCircle size={18} color="var(--accent-emerald)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, marginTop: "8px", color: "var(--accent-emerald)" }}>
            {summary?.approved ?? 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "4px" }}>
            Clean business validation
          </div>
        </div>

        <div className="metric-card">
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>BLOCKED DUPLICATES</span>
            <Copy size={18} color="var(--accent-purple)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, marginTop: "8px", color: "var(--accent-purple)" }}>
            {summary?.blocked_duplicate ?? 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "4px" }}>
            Hash & business key checks
          </div>
        </div>

        <div className="metric-card">
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>PROCESSING FAILURES</span>
            <XCircle size={18} color="var(--accent-rose)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, marginTop: "8px", color: "var(--accent-rose)" }}>
            {summary?.failed ?? 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "4px" }}>
            Technical parser/task issues
          </div>
        </div>
      </div>

      {/* Operational Latency & SLA Analytics */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "20px",
          marginBottom: "32px",
        }}
      >
        <div className="glass-panel" style={{ padding: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <Clock size={20} color="#818cf8" />
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>Processing Latency</h3>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div
              style={{
                background: "rgba(0,0,0,0.2)",
                padding: "16px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>MEDIAN DURATION</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-main)", marginTop: "4px" }}>
                {metrics?.median_duration_ms ? `${metrics.median_duration_ms.toFixed(0)} ms` : "0 ms"}
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--accent-emerald)", marginTop: "4px" }}>
                p50 pipeline speed
              </div>
            </div>
            <div
              style={{
                background: "rgba(0,0,0,0.2)",
                padding: "16px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>95TH PERCENTILE</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-main)", marginTop: "4px" }}>
                {metrics?.p95_duration_ms ? `${metrics.p95_duration_ms.toFixed(0)} ms` : "0 ms"}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#38bdf8", marginTop: "4px" }}>
                p95 worst-case latency
              </div>
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <TrendingUp size={20} color="#34d399" />
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>Quality & Automation Rates</h3>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div
              style={{
                background: "rgba(0,0,0,0.2)",
                padding: "16px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>EXTRACTION CONFIDENCE</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-main)", marginTop: "4px" }}>
                {metrics?.average_confidence ? `${(metrics.average_confidence * 100).toFixed(0)}%` : "0%"}
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--accent-emerald)", marginTop: "4px" }}>
                Evidence coverage score
              </div>
            </div>
            <div
              style={{
                background: "rgba(0,0,0,0.2)",
                padding: "16px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>HUMAN REVIEW RATE</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-main)", marginTop: "4px" }}>
                {metrics?.human_review_rate ? `${(metrics.human_review_rate * 100).toFixed(0)}%` : "0%"}
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--accent-amber)", marginTop: "4px" }}>
                Routed to reviewers
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Review Queue Alert Card */}
      {summary && summary.review_required > 0 && (
        <div
          style={{
            background: "linear-gradient(90deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05))",
            border: "1px solid rgba(245, 158, 11, 0.35)",
            borderRadius: "var(--radius-lg)",
            padding: "18px 24px",
            marginBottom: "32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                background: "rgba(245, 158, 11, 0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <AlertTriangle size={20} color="#fbbf24" />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1rem" }}>
                {summary.review_required} {summary.review_required === 1 ? "Document Requires" : "Documents Require"} Human Intervention
              </div>
              <div style={{ fontSize: "0.825rem", color: "var(--text-muted)" }}>
                Arithmetic mismatches, unregistered suppliers, or threshold exceptions are awaiting review.
              </div>
            </div>
          </div>
          <button onClick={onOpenReviewQueue} className="btn btn-primary" style={{ background: "#f59e0b", color: "#000" }}>
            Open Review Queue
            <ArrowRight size={16} />
          </button>
        </div>
      )}

      {/* Recent Submissions Table */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "16px",
          }}
        >
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>Recent Submissions</h3>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Document File</th>
                <th>Type</th>
                <th>Supplier</th>
                <th>Total</th>
                <th>Status</th>
                <th>Confidence</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {recentDocs.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: "32px", color: "var(--text-muted)" }}>
                    No documents uploaded yet. Click "Upload Document" to process your first invoice.
                  </td>
                </tr>
              ) : (
                recentDocs.map((doc) => (
                  <tr key={doc.id} onClick={() => onSelectDocument(doc.id)}>
                    <td style={{ fontWeight: 600 }}>{doc.original_filename}</td>
                    <td>
                      <span
                        style={{
                          fontSize: "0.75rem",
                          textTransform: "uppercase",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: "rgba(255, 255, 255, 0.06)",
                        }}
                      >
                        {doc.document_type}
                      </span>
                    </td>
                    <td>{doc.supplier_name || "—"}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                      {doc.total_amount ? `INR ${parseFloat(doc.total_amount).toLocaleString()}` : "—"}
                    </td>
                    <td>
                      <span className={`status-pill status-${doc.status}`}>
                        {doc.status.replace("_", " ")}
                      </span>
                    </td>
                    <td>
                      {doc.confidence_score !== null && (
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <div
                            style={{
                              width: "48px",
                              height: "6px",
                              borderRadius: "3px",
                              background: "rgba(255,255,255,0.1)",
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${(doc.confidence_score ?? 0) * 100}%`,
                                height: "100%",
                                background:
                                  (doc.confidence_score ?? 0) >= 0.85
                                    ? "var(--accent-emerald)"
                                    : "var(--accent-amber)",
                              }}
                            />
                          </div>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            {Math.round((doc.confidence_score ?? 0) * 100)}%
                          </span>
                        </div>
                      )}
                    </td>
                    <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {new Date(doc.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
