import React, { useState, useRef } from "react";
import { UploadCloud, X, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "../../api/client";

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (documentId: string) => void;
}

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<string>("invoice");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    const validTypes = ["application/pdf", "image/png", "image/jpeg"];
    if (!validTypes.includes(selectedFile.type)) {
      setError("Unsupported file format. Please upload a PDF, PNG, or JPEG file.");
      return;
    }
    const maxMb = 20;
    if (selectedFile.size > maxMb * 1024 * 1024) {
      setError(`File exceeds the maximum limit of ${maxMb} MB.`);
      return;
    }
    setFile(selectedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setIsUploading(true);
      setError(null);
      const res = await api.uploadDocument(file, documentType);
      onUploadSuccess(res.document_id);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to upload document.");
    } finally {
      setIsUploading(false);
    }
  };

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
          maxWidth: "540px",
          padding: "28px",
          position: "relative",
          animation: "scaleIn 0.2s ease-out",
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

        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "8px" }}>
          Upload Business Document
        </h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "20px" }}>
          The engine will parse text, run OCR on scanned pages, extract fields, and evaluate business rules.
        </p>

        {error && (
          <div
            style={{
              padding: "12px 16px",
              borderRadius: "var(--radius-md)",
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.35)",
              color: "#f87171",
              fontSize: "0.85rem",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "16px",
            }}
          >
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        {/* Document Type Selector */}
        <div style={{ marginBottom: "18px" }}>
          <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            EXPECTED DOCUMENT TYPE
          </label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="form-input"
          >
            <option value="invoice">Vendor Invoice (Primary MVP)</option>
            <option value="purchase_order">Purchase Order</option>
            <option value="receipt">Receipt / Payment Voucher</option>
            <option value="contract">Commercial Contract</option>
          </select>
        </div>

        {/* Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${isDragging ? "var(--primary)" : "var(--border-subtle)"}`,
            borderRadius: "var(--radius-lg)",
            padding: "36px 20px",
            textAlign: "center",
            cursor: "pointer",
            background: isDragging ? "rgba(99, 102, 241, 0.08)" : "rgba(0, 0, 0, 0.2)",
            transition: "all 0.15s ease",
            marginBottom: "24px",
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            style={{ display: "none" }}
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                validateAndSetFile(e.target.files[0]);
              }
            }}
          />

          {file ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
              <CheckCircle2 size={36} color="var(--accent-emerald)" />
              <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{file.name}</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for processing
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
              <UploadCloud size={38} color="#818cf8" />
              <div style={{ fontWeight: 600, fontSize: "0.95rem", marginTop: "4px" }}>
                Drag and drop document here, or click to browse
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
                Supports PDF, PNG, and JPEG files up to 20 MB
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
          <button onClick={onClose} className="btn btn-secondary" disabled={isUploading}>
            Cancel
          </button>
          <button
            onClick={handleUpload}
            className="btn btn-primary"
            disabled={!file || isUploading}
          >
            {isUploading ? "Uploading & Enqueuing..." : "Start Processing"}
          </button>
        </div>
      </div>
    </div>
  );
};
