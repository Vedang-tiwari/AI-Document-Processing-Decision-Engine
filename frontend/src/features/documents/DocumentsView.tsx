import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  FileText,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { api } from "../../api/client";
import { DocumentItem } from "../../types";

interface DocumentsViewProps {
  onSelectDocument: (id: string) => void;
  onOpenUpload: () => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({
  onSelectDocument,
  onOpenUpload,
}) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const res = await api.listDocuments({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
      });
      setDocuments(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [page, statusFilter]);

  // Client-side search filter for filename or supplier
  const filteredDocuments = documents.filter((doc) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      doc.original_filename.toLowerCase().includes(q) ||
      (doc.supplier_name && doc.supplier_name.toLowerCase().includes(q))
    );
  });

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div>
      {/* Header */}
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
            All Documents
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "4px" }}>
            Repository of all accepted invoices, receipts, and supporting attachments.
          </p>
        </div>
        <button onClick={onOpenUpload} className="btn btn-primary">
          Upload Document
        </button>
      </div>

      {/* Filter Bar */}
      <div
        className="glass-panel"
        style={{
          padding: "16px 20px",
          marginBottom: "20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1, minWidth: "260px" }}>
          <div style={{ position: "relative", width: "100%" }}>
            <Search
              size={16}
              style={{
                position: "absolute",
                left: "12px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-dim)",
              }}
            />
            <input
              type="text"
              placeholder="Search by filename or supplier name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input"
              style={{ paddingLeft: "36px" }}
            />
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Filter size={16} color="var(--text-muted)" />
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600 }}>STATUS:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="form-input"
            style={{ width: "180px" }}
          >
            <option value="">All Statuses</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="review_required">Review Required</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="blocked_duplicate">Blocked Duplicate</option>
            <option value="failed">Failed</option>
          </select>

          <button onClick={fetchDocs} className="btn btn-secondary" style={{ padding: "8px 12px" }}>
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Supplier</th>
              <th>Total Amount</th>
              <th>Status</th>
              <th>Outcome</th>
              <th>Confidence</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredDocuments.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                  {loading ? "Loading documents..." : "No documents match the current criteria."}
                </td>
              </tr>
            ) : (
              filteredDocuments.map((doc) => (
                <tr key={doc.id} onClick={() => onSelectDocument(doc.id)}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <FileText size={18} color="var(--primary)" />
                      <div>
                        <div style={{ fontWeight: 600 }}>{doc.original_filename}</div>
                        <div style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>
                          {(doc.file_size_bytes / 1024).toFixed(1)} KB • {doc.mime_type}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: "rgba(255, 255, 255, 0.06)",
                        textTransform: "uppercase",
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
                    {doc.decision_outcome ? (
                      <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 500 }}>
                        {doc.decision_outcome.replace("_", " ")}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    {doc.confidence_score !== null ? (
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
                    ) : (
                      "—"
                    )}
                  </td>
                  <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDocument(doc.id);
                      }}
                      className="btn btn-secondary"
                      style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                    >
                      <ExternalLink size={12} />
                      View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: "20px",
          color: "var(--text-muted)",
          fontSize: "0.85rem",
        }}
      >
        <div>
          Showing {filteredDocuments.length} of {total} documents
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn btn-secondary"
            style={{ padding: "6px 12px" }}
          >
            <ChevronLeft size={16} />
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="btn btn-secondary"
            style={{ padding: "6px 12px" }}
          >
            Next
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
