import React, { useState, useEffect } from "react";
import { ShieldCheck, ToggleLeft, ToggleRight, Check, RefreshCw } from "lucide-react";
import { api } from "../../api/client";
import { BusinessRuleItem } from "../../types";

export const RulesView: React.FC = () => {
  const [rules, setRules] = useState<BusinessRuleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingCode, setUpdatingCode] = useState<string | null>(null);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const res = await api.listRules();
      setRules(res);
    } catch (err) {
      console.error("Failed to load business rules:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleToggle = async (rule: BusinessRuleItem) => {
    try {
      setUpdatingCode(rule.rule_code);
      const nextState = !rule.enabled;
      await api.patchRule(rule.rule_code, { enabled: nextState });
      setRules((prev) =>
        prev.map((r) => (r.rule_code === rule.rule_code ? { ...r, enabled: nextState } : r))
      );
    } catch (err: any) {
      alert(`Failed to update rule ${rule.rule_code}: ${err.message}`);
    } finally {
      setUpdatingCode(null);
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
            Deterministic Business Rules
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "4px" }}>
            Declarative policies governing automatic approval criteria, tolerance limits, and routing logic.
          </p>
        </div>
        <button onClick={fetchRules} className="btn btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Reload Rules
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
        {rules.map((rule) => {
          const isUpdating = updatingCode === rule.rule_code;
          return (
            <div
              key={rule.rule_code}
              className="glass-panel"
              style={{
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                opacity: rule.enabled ? 1 : 0.6,
                transition: "opacity 0.2s ease",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px", marginBottom: "10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <ShieldCheck size={20} color="var(--primary)" />
                    <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>{rule.name}</h3>
                  </div>
                  <button
                    onClick={() => handleToggle(rule)}
                    disabled={isUpdating}
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: rule.enabled ? "var(--accent-emerald)" : "var(--text-dim)",
                    }}
                  >
                    {rule.enabled ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
                  </button>
                </div>

                <div style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-dim)", marginBottom: "8px" }}>
                  {rule.rule_code} • v{rule.version}
                </div>

                <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "16px" }}>
                  {rule.description}
                </p>
              </div>

              <div>
                <div
                  style={{
                    background: "rgba(0,0,0,0.25)",
                    padding: "12px",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.75rem",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <div style={{ fontWeight: 600, color: "var(--text-dim)", marginBottom: "4px" }}>
                    CONFIGURATION & TOLERANCES
                  </div>
                  <pre
                    style={{
                      fontFamily: "var(--font-mono)",
                      color: "var(--text-main)",
                      whiteSpace: "pre-wrap",
                      fontSize: "0.72rem",
                    }}
                  >
                    {JSON.stringify(rule.configuration, null, 2)}
                  </pre>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px", fontSize: "0.75rem" }}>
                  <span style={{ color: "var(--text-dim)" }}>
                    Target: <strong>{rule.document_type}</strong>
                  </span>
                  <span
                    style={{
                      padding: "2px 8px",
                      borderRadius: "var(--radius-full)",
                      fontSize: "0.68rem",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      background:
                        rule.severity === "critical"
                          ? "rgba(244, 63, 94, 0.15)"
                          : "rgba(245, 158, 11, 0.15)",
                      color: rule.severity === "critical" ? "#fb7185" : "#fbbf24",
                    }}
                  >
                    {rule.severity}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
