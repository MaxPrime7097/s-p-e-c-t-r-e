import React, { useEffect, useRef, useState } from "react";
import SuggestionsPanel from "./components/SuggestionsPanel";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const EMPTY_SUGGESTION = {
  issue: "No issue detected yet.",
  suggestion: "Upload a screenshot to start analysis.",
  severity: "low",
  fix_code: null,
  explanation: "Realtime updates will appear here.",
  patch: null,
  language: "unknown",
};

function App() {
  const [latestSuggestion, setLatestSuggestion] = useState(EMPTY_SUGGESTION);
  const lastSpokenIssueRef = useRef("");

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const response = await fetch(`${API_URL}/latest`);
        if (!response.ok) return;
        const data = await response.json();
        setLatestSuggestion(data);
      } catch (error) {
        // Silent fail for demo polling loop.
      }
    };

    fetchLatest();
    const interval = setInterval(fetchLatest, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const issue = latestSuggestion?.issue || "";
    const severity = (latestSuggestion?.severity || "low").toLowerCase();

    if (severity === "high" && issue && issue !== lastSpokenIssueRef.current && "speechSynthesis" in window) {
      const message = `Warning. ${issue} detected.`;
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(message));
      lastSpokenIssueRef.current = issue;
    }
  }, [latestSuggestion]);

  return (
    <div style={{ fontFamily: "Arial, sans-serif", margin: "2rem" }}>
      <h1>S.P.E.C.T.R.E</h1>
      <p>System for Proactive Engineering and Code Technical Real-time Evaluation</p>
      <SuggestionsPanel latestSuggestion={latestSuggestion} onSuggestionUpdate={setLatestSuggestion} />
    </div>
  );
}

export default App;
