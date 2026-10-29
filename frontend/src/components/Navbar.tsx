import React from "react";
import {
  FileText,
  LayoutDashboard,
  CheckSquare,
  ShieldCheck,
  Webhook,
  UploadCloud,
  Cpu,
} from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  reviewCount: number;
  onOpenUpload: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  reviewCount,
  onOpenUpload,
}) => {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "documents", label: "Documents", icon: FileText },
    {
      id: "reviews",
      label: "Review Queue",
      icon: CheckSquare,
      badge: reviewCount > 0 ? reviewCount : undefined,
    },
    { id: "rules", label: "Business Rules", icon: ShieldCheck },
    { id: "webhooks", label: "Webhooks", icon: Webhook },
  ];

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border-subtle)",
        background: "rgba(8, 12, 20, 0.8)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: "1440px",
          margin: "0 auto",
          padding: "0 32px",
          height: "68px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #6366f1, #06b6d4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 16px rgba(99, 102, 241, 0.4)",
            }}
          >
            <Cpu size={20} color="#ffffff" />
          </div>
          <div>
            <div
              style={{
                fontSize: "1.1rem",
                fontWeight: 700,
                letterSpacing: "-0.02em",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              DocuFlow
              <span
                style={{
                  fontSize: "0.68rem",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  background: "rgba(99, 102, 241, 0.15)",
                  color: "#818cf8",
                  fontWeight: 600,
                  textTransform: "uppercase",
                }}
              >
                v1.0
              </span>
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
              AI Document Decision Engine
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 14px",
                  borderRadius: "var(--radius-md)",
                  border: "none",
                  background: isActive ? "rgba(99, 102, 241, 0.14)" : "transparent",
                  color: isActive ? "#ffffff" : "var(--text-muted)",
                  fontWeight: isActive ? 600 : 500,
                  fontSize: "0.875rem",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  position: "relative",
                }}
              >
                <Icon size={16} color={isActive ? "#818cf8" : "currentColor"} />
                {item.label}
                {item.badge !== undefined && (
                  <span
                    style={{
                      padding: "1px 6px",
                      borderRadius: "10px",
                      background: "#f59e0b",
                      color: "#000",
                      fontSize: "0.68rem",
                      fontWeight: 700,
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right CTA & System Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "0.75rem",
              color: "var(--accent-emerald)",
              padding: "4px 10px",
              borderRadius: "var(--radius-full)",
              background: "rgba(16, 185, 129, 0.08)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "var(--accent-emerald)",
                boxShadow: "0 0 8px #10b981",
              }}
            />
            Engine Ready
          </div>

          <button
            onClick={onOpenUpload}
            className="btn btn-primary"
            style={{ fontSize: "0.85rem", padding: "8px 16px" }}
          >
            <UploadCloud size={16} />
            Upload Document
          </button>
        </div>
      </div>
    </header>
  );
};
