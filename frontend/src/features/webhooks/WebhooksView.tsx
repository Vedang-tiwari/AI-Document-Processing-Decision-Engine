import React, { useState, useEffect } from "react";
import { Webhook, Plus, Trash2, RotateCcw, CheckCircle, XCircle, AlertCircle, RefreshCw } from "lucide-react";
import { api } from "../../api/client";
import { WebhookEndpointItem, WebhookDeliveryLog } from "../../types";

export const WebhooksView: React.FC = () => {
  const [endpoints, setEndpoints] = useState<WebhookEndpointItem[]>([]);
  const [selectedEndpointId, setSelectedEndpointId] = useState<string | null>(null);
  const [deliveries, setDeliveries] = useState<WebhookDeliveryLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newEndpointName, setNewEndpointName] = useState("");
  const [newEndpointUrl, setNewEndpointUrl] = useState("");
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  const fetchEndpoints = async () => {
    try {
      setLoading(true);
      const res = await api.listWebhooks();
      setEndpoints(res);
      if (res.length > 0 && !selectedEndpointId) {
        setSelectedEndpointId(res[0].id);
      }
    } catch (err) {
      console.error("Failed to load webhooks:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDeliveries = async (epId: string) => {
    try {
      const logs = await api.listDeliveries(epId);
      setDeliveries(logs);
    } catch (err) {
      console.error("Failed to load deliveries:", err);
    }
  };

  useEffect(() => {
    fetchEndpoints();
  }, []);

  useEffect(() => {
    if (selectedEndpointId) {
      fetchDeliveries(selectedEndpointId);
    }
  }, [selectedEndpointId]);

  const handleCreate = async () => {
    if (!newEndpointName || !newEndpointUrl) return;
    try {
      const res = await api.createWebhook({
        name: newEndpointName,
        url: newEndpointUrl,
      });
      setCreatedSecret(res.secret);
      setNewEndpointName("");
      setNewEndpointUrl("");
      await fetchEndpoints();
    } catch (err: any) {
      alert(`Error registering webhook: ${err.message}`);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this webhook endpoint?")) return;
    try {
      await api.deleteWebhook(id);
      if (selectedEndpointId === id) setSelectedEndpointId(null);
      await fetchEndpoints();
    } catch (err: any) {
      alert(`Error deleting webhook: ${err.message}`);
    }
  };

  const handleRetryDelivery = async (deliveryId: string) => {
    if (!selectedEndpointId) return;
    try {
      await api.retryDelivery(selectedEndpointId, deliveryId);
      alert("Webhook retry delivery triggered.");
      fetchDeliveries(selectedEndpointId);
    } catch (err: any) {
      alert(`Failed to retry delivery: ${err.message}`);
    }
  };

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
            Webhook Integrations
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "4px" }}>
            Event-driven integrations signed with HMAC-SHA256 signatures for document lifecycle and review events.
          </p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          <Plus size={16} />
          Register Endpoint
        </button>
      </div>

      {createdSecret && (
        <div
          style={{
            background: "rgba(16, 185, 129, 0.12)",
            border: "1px solid rgba(16, 185, 129, 0.35)",
            padding: "16px 20px",
            borderRadius: "var(--radius-lg)",
            marginBottom: "24px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 700, color: "#34d399", fontSize: "0.95rem" }}>
                Webhook Signing Secret (HMAC-SHA256)
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Save this secret now to verify signatures via <code style={{ color: "#fff" }}>X-Webhook-Signature</code> header.
              </div>
            </div>
            <button onClick={() => setCreatedSecret(null)} className="btn btn-secondary" style={{ padding: "4px 10px", fontSize: "0.75rem" }}>
              Dismiss
            </button>
          </div>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              background: "#000",
              padding: "10px 14px",
              borderRadius: "var(--radius-md)",
              marginTop: "10px",
              color: "#38bdf8",
              fontSize: "0.85rem",
              wordBreak: "break-all",
            }}
          >
            {createdSecret}
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "24px" }}>
        {/* Endpoints List */}
        <div className="glass-panel" style={{ padding: "20px" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: "16px" }}>
            Registered Endpoints
          </h3>
          {endpoints.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center", padding: "30px 0" }}>
              No endpoints registered. Click "Register Endpoint" above.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {endpoints.map((ep) => {
                const isSelected = selectedEndpointId === ep.id;
                return (
                  <div
                    key={ep.id}
                    onClick={() => setSelectedEndpointId(ep.id)}
                    style={{
                      padding: "14px",
                      borderRadius: "var(--radius-md)",
                      background: isSelected ? "rgba(99, 102, 241, 0.15)" : "rgba(0,0,0,0.2)",
                      border: `1px solid ${isSelected ? "var(--primary)" : "var(--border-subtle)"}`,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{ep.name}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", wordBreak: "break-all", marginTop: "2px" }}>
                          {ep.url}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(ep.id);
                        }}
                        style={{ background: "none", border: "none", color: "var(--accent-rose)", cursor: "pointer" }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Delivery Logs */}
        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>Delivery History</h3>
            {selectedEndpointId && (
              <button
                onClick={() => fetchDeliveries(selectedEndpointId)}
                className="btn btn-secondary"
                style={{ padding: "4px 8px" }}
              >
                <RefreshCw size={14} />
              </button>
            )}
          </div>

          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Event Type</th>
                  <th>Status</th>
                  <th>HTTP Code</th>
                  <th>Attempts</th>
                  <th>Delivered At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: "30px", color: "var(--text-muted)" }}>
                      No delivery events recorded for this endpoint yet.
                    </td>
                  </tr>
                ) : (
                  deliveries.map((del) => (
                    <tr key={del.id}>
                      <td style={{ fontWeight: 600, fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                        {del.event_type}
                      </td>
                      <td>
                        <span
                          style={{
                            fontSize: "0.72rem",
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: "var(--radius-full)",
                            textTransform: "uppercase",
                            background:
                              del.status === "delivered"
                                ? "rgba(16, 185, 129, 0.15)"
                                : "rgba(244, 63, 94, 0.15)",
                            color: del.status === "delivered" ? "#34d399" : "#fb7185",
                          }}
                        >
                          {del.status}
                        </span>
                      </td>
                      <td style={{ fontFamily: "var(--font-mono)" }}>
                        {del.last_http_status ? del.last_http_status : "—"}
                      </td>
                      <td>{del.attempt_count}</td>
                      <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {del.delivered_at
                          ? new Date(del.delivered_at).toLocaleTimeString()
                          : (del.last_error ? `Error: ${del.last_error.slice(0, 30)}...` : "Pending")}
                      </td>
                      <td>
                        <button
                          onClick={() => handleRetryDelivery(del.id)}
                          className="btn btn-secondary"
                          style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                        >
                          <RotateCcw size={12} />
                          Retry
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Registration Modal */}
      {isModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "20px",
          }}
        >
          <div className="glass-panel-elevated" style={{ width: "100%", maxWidth: "480px", padding: "24px" }}>
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "16px" }}>
              Register Webhook Destination
            </h3>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                ENDPOINT NAME
              </label>
              <input
                type="text"
                placeholder="e.g. ERP System Connector"
                value={newEndpointName}
                onChange={(e) => setNewEndpointName(e.target.value)}
                className="form-input"
              />
            </div>
            <div style={{ marginBottom: "20px" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                TARGET HTTPS URL
              </label>
              <input
                type="url"
                placeholder="https://api.mycompany.com/webhooks/invoices"
                value={newEndpointUrl}
                onChange={(e) => setNewEndpointUrl(e.target.value)}
                className="form-input"
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button
                onClick={() => {
                  handleCreate();
                  setIsModalOpen(false);
                }}
                className="btn btn-primary"
                disabled={!newEndpointName || !newEndpointUrl}
              >
                Create Endpoint
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
