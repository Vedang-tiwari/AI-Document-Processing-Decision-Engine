import React, { useState, useEffect } from "react";
import { CheckSquare, AlertTriangle, ArrowRight, RefreshCw, FileText } from "lucide-react";
import { api } from "../../api/client";

interface ReviewQueueViewProps {
  onSelectDocument: (id: string) => void;
}

export const ReviewQueueView: React.FC<ReviewQueueViewProps> = ({ onSelectDocument }) => {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const res = await api.listReviewQueue(1, 50);
      setItems(res.items);
    } catch (err) {
      console.error("Failed to load review queue:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "24px",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.03em" }}>
            Human Review Queue
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "4px" }}>
            Documents flagged by business rules, validation mismatches, or confidence thresholds requiring authorized approval.
          </p>
        </div>
        <button onClick={fetchQueue} className="btn btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh Queue
        </button>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Supplier</th>
              <th>Total Amount</th>
              <th>Validation Issues</th>
              <th>Confidence</th>
              <th>Queued Since</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>
                  {loading ? "Loading review queue..." : "✨ The review queue is empty! All documents have been resolved."}
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.document_id} onClick={() => onSelectDocument(item.document_id)}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <FileText size={18} color="var(--accent-amber)" />
                      <div>
                        <div style={{ fontWeight: 600 }}>{item.original_filename}</div>
                        <div style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>
                          {item.document_type}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>{item.supplier_name || "—"}</td>
                  <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                    {item.total_amount ? `INR ${parseFloat(item.total_amount).toLocaleString()}` : "—"}
                  </td>
                  <td>
                    {item.validation_issue_count > 0 ? (
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          color: "#fbbf24",
                          fontSize: "0.8rem",
                          fontWeight: 600,
                        }}
                      >
                        <AlertTriangle size={14} />
                        {item.validation_issue_count} issue{item.validation_issue_count > 1 ? "s" : ""}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}>None</span>
                    )}
                  </td>
                  <td>
                    {item.confidence_score !== null ? (
                      <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        {Math.round((item.confidence_score ?? 0) * 100)}%
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDocument(item.document_id);
                      }}
                      className="btn btn-primary"
                      style={{ padding: "6px 12px", fontSize: "0.8rem" }}
                    >
                      Review
                      <ArrowRight size={14} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
