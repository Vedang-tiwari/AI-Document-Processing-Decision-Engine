import React, { useState, useEffect } from "react";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  Save,
  Clock,
  History,
  FileText,
  ShieldCheck,
  Check,
  Eye,
} from "lucide-react";
import { api } from "../../api/client";
import { ReviewWorkspaceDetail } from "../../types";

interface ReviewWorkspaceViewProps {
  documentId: string;
  onBack: () => void;
  onActionComplete: () => void;
}

export const ReviewWorkspaceView: React.FC<ReviewWorkspaceViewProps> = ({
  documentId,
  onBack,
  onActionComplete,
}) => {
  const [detail, setDetail] = useState<ReviewWorkspaceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [comment, setComment] = useState("");
  const [notice, setNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Form field state
  const [formData, setFormData] = useState({
    supplier_name: "",
    supplier_tax_id: "",
    invoice_number: "",
    invoice_date: "",
    due_date: "",
    currency: "INR",
    subtotal: "0.00",
    tax_amount: "0.00",
    total_amount: "0.00",
    purchase_order_reference: "",
  });

  const fetchDetail = async () => {
    try {
      setLoading(true);
      const data = await api.getReviewDetail(documentId);
      setDetail(data);

      const ext = data.extracted_data || {};
      const supp = ext.supplier || {};
      setFormData({
        supplier_name: supp.name || "",
        supplier_tax_id: supp.tax_id || "",
        invoice_number: ext.invoice_number || "",
        invoice_date: ext.invoice_date || "",
        due_date: ext.due_date || "",
        currency: ext.currency || "INR",
        subtotal: ext.subtotal || "0.00",
        tax_amount: ext.tax_amount || "0.00",
        total_amount: ext.total_amount || "0.00",
        purchase_order_reference: ext.purchase_order_reference || "",
      });
    } catch (err: any) {
      setNotice({ type: "error", text: err.message || "Failed to load review workspace." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [documentId]);

  const handleSaveCorrections = async () => {
    try {
      setIsSaving(true);
      setNotice(null);
      await api.submitCorrections(
        documentId,
        {
          "supplier.name": formData.supplier_name,
          "supplier.tax_id": formData.supplier_tax_id || null,
          invoice_number: formData.invoice_number,
          invoice_date: formData.invoice_date,
          due_date: formData.due_date || null,
          currency: formData.currency,
          subtotal: formData.subtotal,
          tax_amount: formData.tax_amount,
          total_amount: formData.total_amount,
          purchase_order_reference: formData.purchase_order_reference || null,
        },
        comment || "Manual field correction"
      );
      setNotice({ type: "success", text: "Corrections saved and revalidated successfully." });
      await fetchDetail();
    } catch (err: any) {
      setNotice({ type: "error", text: err.message || "Failed to save corrections." });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDecision = async (decision: "approved" | "rejected") => {
    const actionWord = decision === "approved" ? "Approve" : "Reject";
    if (!window.confirm(`Are you sure you want to ${actionWord} document ${detail?.original_filename}?`)) {
      return;
    }
    try {
      setIsSaving(true);
      setNotice(null);
      await api.submitDecision(documentId, decision, comment);
      alert(`Document has been successfully ${decision}.`);
      onActionComplete();
    } catch (err: any) {
      setNotice({ type: "error", text: err.message || `Failed to record ${decision} decision.` });
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "80px 20px" }}>
        <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>Loading review workspace...</div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div style={{ textAlign: "center", padding: "80px 20px" }}>
        <div style={{ color: "var(--accent-rose)", marginBottom: "16px" }}>Failed to load document details.</div>
        <button onClick={onBack} className="btn btn-secondary">
          Back to Queue
        </button>
      </div>
    );
  }

  // Calculate live arithmetic reconciliation
  const sub = parseFloat(formData.subtotal) || 0;
  const tax = parseFloat(formData.tax_amount) || 0;
  const tot = parseFloat(formData.total_amount) || 0;
  const diff = Math.abs(sub + tax - tot);
  const isReconciled = diff <= 1.0;

  return (
    <div>
      {/* Top Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button onClick={onBack} className="btn btn-secondary" style={{ padding: "8px 12px" }}>
            <ArrowLeft size={16} />
            Back
          </button>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h2 style={{ fontSize: "1.3rem", fontWeight: 800 }}>{detail.original_filename}</h2>
              <span className={`status-pill status-${detail.status}`}>
                {detail.status.replace("_", " ")}
              </span>
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              ID: {detail.document_id} • Type: {detail.document_type}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            onClick={handleSaveCorrections}
            disabled={isSaving}
            className="btn btn-secondary"
          >
            <Save size={16} />
            Save & Revalidate
          </button>
          <button
            onClick={() => handleDecision("rejected")}
            disabled={isSaving}
            className="btn btn-danger"
          >
            <XCircle size={16} />
            Reject Invoice
          </button>
          <button
            onClick={() => handleDecision("approved")}
            disabled={isSaving}
            className="btn btn-success"
          >
            <CheckCircle size={16} />
            Approve Invoice
          </button>
        </div>
      </div>

      {notice && (
        <div
          style={{
            padding: "12px 18px",
            borderRadius: "var(--radius-md)",
            marginBottom: "20px",
            background: notice.type === "success" ? "rgba(16, 185, 129, 0.15)" : "rgba(244, 63, 94, 0.15)",
            border: `1px solid ${notice.type === "success" ? "rgba(16, 185, 129, 0.3)" : "rgba(244, 63, 94, 0.3)"}`,
            color: notice.type === "success" ? "#34d399" : "#fb7185",
            fontSize: "0.875rem",
          }}
        >
          {notice.text}
        </div>
      )}

      {/* Side-by-Side Review Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1.15fr",
          gap: "24px",
          alignItems: "start",
        }}
      >
        {/* Left: Original Document Viewer */}
        <div className="glass-panel" style={{ padding: "20px", height: "780px", display: "flex", flexDirection: "column" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "12px",
              paddingBottom: "8px",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 600, fontSize: "0.9rem" }}>
              <Eye size={16} color="var(--primary)" />
              Original Document Preview
            </div>
            <a
              href={api.getDocumentFileUrl(documentId)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
              style={{ padding: "4px 10px", fontSize: "0.75rem" }}
            >
              Open in Tab
            </a>
          </div>

          <div
            style={{
              flex: 1,
              borderRadius: "var(--radius-md)",
              overflow: "hidden",
              border: "1px solid var(--border-subtle)",
              background: "#05070c",
            }}
          >
            <iframe
              src={api.getDocumentFileUrl(documentId)}
              title="Document Preview"
              style={{ width: "100%", height: "100%", border: "none" }}
            />
          </div>
        </div>

        {/* Right: Editable Extraction Form & Validation Rules */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Validation Warnings Alert */}
          {detail.validation_results && detail.validation_results.issues.length > 0 && (
            <div
              style={{
                background: "rgba(245, 158, 11, 0.1)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                borderRadius: "var(--radius-lg)",
                padding: "16px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#fbbf24", fontWeight: 700, fontSize: "0.9rem", marginBottom: "8px" }}>
                <AlertTriangle size={16} />
                Validation Issues Detected ({detail.validation_results.issues.length})
              </div>
              <ul style={{ paddingLeft: "20px", fontSize: "0.8rem", color: "var(--text-main)" }}>
                {detail.validation_results.issues.map((iss, i) => (
                  <li key={i} style={{ marginBottom: "4px" }}>
                    <strong style={{ textTransform: "uppercase", fontSize: "0.72rem", color: iss.severity === "critical" ? "#f87171" : "#fbbf24" }}>
                      [{iss.severity}]
                    </strong>{" "}
                    {iss.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Form */}
          <div className="glass-panel" style={{ padding: "24px" }}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: "16px" }}>
              Extracted Invoice Data
            </h3>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  SUPPLIER / VENDOR NAME
                </label>
                <input
                  type="text"
                  value={formData.supplier_name}
                  onChange={(e) => setFormData({ ...formData, supplier_name: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  TAX IDENTIFIER (GSTIN/VAT)
                </label>
                <input
                  type="text"
                  value={formData.supplier_tax_id}
                  onChange={(e) => setFormData({ ...formData, supplier_tax_id: e.target.value })}
                  className="form-input"
                />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  INVOICE NUMBER
                </label>
                <input
                  type="text"
                  value={formData.invoice_number}
                  onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                  className="form-input form-input-mono"
                />
              </div>
              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  PURCHASE ORDER REF
                </label>
                <input
                  type="text"
                  value={formData.purchase_order_reference}
                  onChange={(e) => setFormData({ ...formData, purchase_order_reference: e.target.value })}
                  className="form-input form-input-mono"
                />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  INVOICE DATE (YYYY-MM-DD)
                </label>
                <input
                  type="text"
                  value={formData.invoice_date}
                  onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  DUE DATE (YYYY-MM-DD)
                </label>
                <input
                  type="text"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  className="form-input"
                />
              </div>
            </div>

            {/* Financial Amounts & Live Reconciliation */}
            <div
              style={{
                background: "rgba(0,0,0,0.25)",
                padding: "16px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
                marginBottom: "20px",
              }}
            >
              <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-muted)", marginBottom: "12px" }}>
                FINANCIAL AMOUNTS & ARITHMETIC
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.2fr", gap: "14px" }}>
                <div>
                  <label style={{ fontSize: "0.72rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                    SUBTOTAL ({formData.currency})
                  </label>
                  <input
                    type="text"
                    value={formData.subtotal}
                    onChange={(e) => setFormData({ ...formData, subtotal: e.target.value })}
                    className="form-input form-input-mono"
                  />
                </div>
                <div>
                  <label style={{ fontSize: "0.72rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                    TAX AMOUNT ({formData.currency})
                  </label>
                  <input
                    type="text"
                    value={formData.tax_amount}
                    onChange={(e) => setFormData({ ...formData, tax_amount: e.target.value })}
                    className="form-input form-input-mono"
                  />
                </div>
                <div>
                  <label style={{ fontSize: "0.72rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                    TOTAL AMOUNT ({formData.currency})
                  </label>
                  <input
                    type="text"
                    value={formData.total_amount}
                    onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                    className="form-input form-input-mono"
                  />
                </div>
              </div>

              {/* Real-time Math check pill */}
              <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem" }}>
                {isReconciled ? (
                  <span style={{ color: "var(--accent-emerald)", display: "flex", alignItems: "center", gap: "4px", fontWeight: 600 }}>
                    <Check size={14} /> Arithmetic Reconciled ({sub.toFixed(2)} + {tax.toFixed(2)} = {tot.toFixed(2)})
                  </span>
                ) : (
                  <span style={{ color: "var(--accent-rose)", display: "flex", alignItems: "center", gap: "4px", fontWeight: 600 }}>
                    <AlertTriangle size={14} /> Mismatch: Subtotal + Tax = {(sub + tax).toFixed(2)}, Diff: {diff.toFixed(2)}
                  </span>
                )}
              </div>
            </div>

            {/* Comment */}
            <div>
              <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                REVIEWER COMMENT / AUDIT NOTE
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Explain the reasons for corrections or approval decision..."
                rows={3}
                className="form-input"
              />
            </div>
          </div>

          {/* Rule Evaluations Section */}
          <div className="glass-panel" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
              <ShieldCheck size={16} color="var(--primary)" />
              Business Rule Outcomes
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {detail.rule_evaluations.map((rule, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px 12px",
                    borderRadius: "var(--radius-md)",
                    background: "rgba(0,0,0,0.2)",
                    border: "1px solid var(--border-subtle)",
                    fontSize: "0.8rem",
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 600 }}>{rule.rule_code}</span>: {rule.message}
                  </div>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      color: rule.status === "passed" ? "var(--accent-emerald)" : (rule.status === "failed" ? "var(--accent-rose)" : "var(--text-muted)"),
                    }}
                  >
                    {rule.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Revision History */}
          {detail.revisions.length > 0 && (
            <div className="glass-panel" style={{ padding: "20px" }}>
              <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <History size={16} color="var(--accent-purple)" />
                Audit Revision History ({detail.revisions.length})
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.78rem" }}>
                {detail.revisions.map((rev) => (
                  <div
                    key={rev.id}
                    style={{
                      padding: "8px 12px",
                      borderRadius: "var(--radius-md)",
                      background: "rgba(0,0,0,0.2)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600 }}>
                      <span style={{ textTransform: "capitalize" }}>{rev.action}</span>
                      <span style={{ color: "var(--text-dim)" }}>
                        {new Date(rev.created_at).toLocaleString()}
                      </span>
                    </div>
                    {rev.comment && (
                      <div style={{ color: "var(--text-muted)", marginTop: "2px" }}>
                        "{rev.comment}"
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
