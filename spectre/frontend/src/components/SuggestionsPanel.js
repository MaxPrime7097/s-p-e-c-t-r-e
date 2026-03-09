import React, { useMemo, useState } from "react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const severityColor = {
  high: "#d32f2f",
  medium: "#ef6c00",
  low: "#2e7d32",
};

function SuggestionsPanel({ latestSuggestion, onSuggestionUpdate }) {
  const [file, setFile] = useState(null);
  const [filePath, setFilePath] = useState("");
  const [loading, setLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [error, setError] = useState("");
  const [applyStatus, setApplyStatus] = useState("");

  const normalized = useMemo(
    () => ({
      issue: latestSuggestion?.issue || "No issue detected.",
      suggestion: latestSuggestion?.suggestion || "No fix suggestion available.",
      severity: (latestSuggestion?.severity || "low").toLowerCase(),
      fix_code: latestSuggestion?.fix_code || null,
      explanation: latestSuggestion?.explanation || "No explanation available.",
      patch: latestSuggestion?.patch || null,
      language: latestSuggestion?.language || "unknown",
    }),
    [latestSuggestion]
  );

  const badgeColor = severityColor[normalized.severity] || severityColor.low;

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("image", file);

      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to analyze image.");
      onSuggestionUpdate(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFix = async () => {
    if (!normalized.patch || !filePath.trim()) {
      setApplyStatus("Provide file path and ensure patch is available.");
      return;
    }

    setApplyLoading(true);
    setApplyStatus("");

    try {
      const response = await fetch(`${API_URL}/apply-fix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath, patch: normalized.patch }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to apply patch.");
      setApplyStatus(`Patch applied to: ${data.file_path}`);
    } catch (applyError) {
      setApplyStatus(`Apply failed: ${applyError.message}`);
    } finally {
      setApplyLoading(false);
    }
  };

  return (
    <div style={{ border: "1px solid #ddd", padding: "1rem", borderRadius: 8, maxWidth: 840 }}>
      <h2>Realtime Suggestions</h2>

      <div style={{ marginBottom: "1rem" }}>
        <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={handleAnalyze} disabled={!file || loading} style={{ marginLeft: "0.75rem" }}>
          {loading ? "Analyzing..." : "Analyze Screenshot"}
        </button>
      </div>

      {error ? <p style={{ color: "#d32f2f" }}>Error: {error}</p> : null}

      <div style={{ marginTop: "0.5rem", background: "#fff8e1", padding: "0.75rem", borderRadius: 4 }}>
        <strong>⚠ Issue</strong>
        <p>{normalized.issue}</p>
      </div>

      <div style={{ marginTop: "0.75rem", background: "#f4f6f8", padding: "0.75rem", borderRadius: 4 }}>
        <strong>Suggestion</strong>
        <p>{normalized.suggestion}</p>
      </div>

      <div style={{ marginTop: "0.75rem" }}>
        <strong>Severity:</strong>{" "}
        <span
          style={{
            color: "white",
            background: badgeColor,
            padding: "0.2rem 0.6rem",
            borderRadius: "999px",
            fontWeight: 700,
            textTransform: "uppercase",
            fontSize: "0.75rem",
          }}
        >
          {normalized.severity}
        </span>
      </div>

      <div style={{ marginTop: "0.75rem" }}>
        <strong>Language:</strong> {normalized.language}
      </div>

      <div style={{ marginTop: "0.75rem", background: "#eef3ff", padding: "0.75rem", borderRadius: 4 }}>
        <strong>Explanation</strong>
        <p style={{ whiteSpace: "pre-wrap" }}>{normalized.explanation}</p>
      </div>

      <div style={{ marginTop: "0.75rem", background: "#101828", color: "#f8fafc", padding: "0.75rem", borderRadius: 4 }}>
        <strong>Suggested fix code</strong>
        <pre style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
          {normalized.fix_code || "No code snippet available."}
        </pre>
      </div>

      <div style={{ marginTop: "0.75rem", background: "#0f172a", color: "#e2e8f0", padding: "0.75rem", borderRadius: 4 }}>
        <strong>Patch</strong>
        <pre style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>{normalized.patch || "No patch available."}</pre>
      </div>

      <div style={{ marginTop: "1rem" }}>
        <input
          type="text"
          value={filePath}
          onChange={(e) => setFilePath(e.target.value)}
          placeholder="File path to apply patch (e.g. /workspace/project/src/App.js)"
          style={{ width: "70%", marginRight: "0.5rem" }}
        />
        <button onClick={handleApplyFix} disabled={applyLoading || !normalized.patch}>
          {applyLoading ? "Applying..." : "Apply Fix"}
        </button>
      </div>

      {applyStatus ? <p style={{ marginTop: "0.5rem" }}>{applyStatus}</p> : null}
    </div>
  );
}

export default SuggestionsPanel;
