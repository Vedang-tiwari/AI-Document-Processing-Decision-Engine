import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { DashboardView } from "./features/dashboard/DashboardView";
import { DocumentsView } from "./features/documents/DocumentsView";
import { ReviewQueueView } from "./features/reviews/ReviewQueueView";
import { ReviewWorkspaceView } from "./features/reviews/ReviewWorkspaceView";
import { RulesView } from "./features/rules/RulesView";
import { WebhooksView } from "./features/webhooks/WebhooksView";
import { DocumentUploadModal } from "./features/documents/DocumentUploadModal";
import { DocumentDetailModal } from "./features/documents/DocumentDetailModal";
import { api } from "./api/client";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [reviewWorkspaceDocId, setReviewWorkspaceDocId] = useState<string | null>(null);

  const refreshCounters = async () => {
    try {
      const summary = await api.getSummary();
      setReviewCount(summary.review_required || 0);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    refreshCounters();
    const interval = setInterval(refreshCounters, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleUploadSuccess = (docId: string) => {
    refreshCounters();
    setSelectedDocId(docId);
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setReviewWorkspaceDocId(null);
        }}
        reviewCount={reviewCount}
        onOpenUpload={() => setIsUploadOpen(true)}
      />

      <main className="main-content">
        {/* If user selected a document specifically to review, open ReviewWorkspace */}
        {reviewWorkspaceDocId ? (
          <ReviewWorkspaceView
            documentId={reviewWorkspaceDocId}
            onBack={() => setReviewWorkspaceDocId(null)}
            onActionComplete={() => {
              setReviewWorkspaceDocId(null);
              refreshCounters();
            }}
          />
        ) : (
          <>
            {activeTab === "dashboard" && (
              <DashboardView
                onSelectDocument={(id) => setSelectedDocId(id)}
                onOpenReviewQueue={() => setActiveTab("reviews")}
              />
            )}

            {activeTab === "documents" && (
              <DocumentsView
                onSelectDocument={(id) => setSelectedDocId(id)}
                onOpenUpload={() => setIsUploadOpen(true)}
              />
            )}

            {activeTab === "reviews" && (
              <ReviewQueueView
                onSelectDocument={(id) => setReviewWorkspaceDocId(id)}
              />
            )}

            {activeTab === "rules" && <RulesView />}

            {activeTab === "webhooks" && <WebhooksView />}
          </>
        )}
      </main>

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Detail Inspection Modal */}
      <DocumentDetailModal
        documentId={selectedDocId}
        onClose={() => setSelectedDocId(null)}
        onOpenReview={(id) => {
          setSelectedDocId(null);
          setReviewWorkspaceDocId(id);
        }}
      />
    </div>
  );
};

export default App;
