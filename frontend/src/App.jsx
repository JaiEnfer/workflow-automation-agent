import { startTransition, useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const starterGoal = "Summarize this document";

function formatTimestamp(timestamp) {
  if (!timestamp) {
    return "Unknown time";
  }

  try {
    return new Date(timestamp * 1000).toLocaleString();
  } catch {
    return "Unknown time";
  }
}

function statusTone(status) {
  if (status === "ok") {
    return "success";
  }
  if (status === "needs_input") {
    return "warning";
  }
  return "neutral";
}

function cleanAnswer(text) {
  if (!text) {
    return "No answer returned yet.";
  }

  return text
    .replace(/^Done\.\s*/i, "")
    .replace(/summarize_text:\s*/gi, "")
    .replace(/^\{?['"]?summary['"]?:\s*/i, "")
    .replace(/\}\s*$/g, "")
    .replace(/\\n/g, "\n")
    .trim();
}

function App() {
  const [goal, setGoal] = useState(starterGoal);
  const [typedText, setTypedText] = useState("");
  const [pdfFile, setPdfFile] = useState(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [runResponse, setRunResponse] = useState(null);
  const [runs, setRuns] = useState([]);
  const [lastRunId, setLastRunId] = useState("");
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [followUpValues, setFollowUpValues] = useState({});

  async function fetchRuns() {
    setLoadingRuns(true);
    try {
      const response = await fetch(`${API_BASE_URL}/runs?limit=10`);
      if (!response.ok) {
        throw new Error(`Failed to load runs (${response.status})`);
      }
      const data = await response.json();
      startTransition(() => {
        setRuns(data.runs || []);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to load runs");
    } finally {
      setLoadingRuns(false);
    }
  }

  useEffect(() => {
    fetchRuns();
  }, []);

  function resetComposer() {
    setGoal(starterGoal);
    setTypedText("");
    setPdfFile(null);
    setFileInputKey((value) => value + 1);
    setRunResponse(null);
    setLastRunId("");
    setFollowUpValues({});
    setErrorMessage("");
  }

  function applyRunResponse(data) {
    setRunResponse(data);
    if (data.run_id) {
      setLastRunId(data.run_id);
    }
    if (data.status === "needs_input") {
      const initialValues = {};
      for (const item of data.missing_fields || []) {
        initialValues[item.field] = "";
      }
      setFollowUpValues(initialValues);
    } else {
      setFollowUpValues({});
    }
  }

  async function submitRun() {
    setErrorMessage("");

    if (!typedText.trim() && !pdfFile) {
      setErrorMessage("Paste some text or upload a PDF before running.");
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("user_goal", goal);
      formData.append("context_json", "{}");
      formData.append("typed_text", typedText);
      if (pdfFile) {
        formData.append("pdf_file", pdfFile);
      }

      const response = await fetch(`${API_BASE_URL}/run-ingest`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Run failed (${response.status})`);
      }

      applyRunResponse(data);
      fetchRuns();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Run failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function continueRun() {
    setErrorMessage("");
    if (!lastRunId) {
      setErrorMessage("No run available to continue yet.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/continue`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          run_id: lastRunId,
          context_patch: followUpValues,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Continue failed (${response.status})`);
      }

      applyRunResponse(data);
      fetchRuns();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Continue failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="simpleShell">
      <main className="simpleWorkspace">
        <section className="heroCard">
          <div>
            <p className="eyebrow">Document Assistant</p>
            <h1 className="pageTitle">Upload a PDF or paste text and get a readable summary</h1>
            <p className="pageCopy">
              The app extracts text, asks your local AI model to summarize it, and gives you a
              clean response without JSON.
            </p>
          </div>
        </section>

        {errorMessage ? <div className="alert error">{errorMessage}</div> : null}

        <section className="simpleGrid">
          <article className="card simpleComposer">
            <div className="cardHeading">
              <div>
                <p className="eyebrow">Input</p>
                <h3>What should I summarize?</h3>
              </div>
              <div className="actionRow">
                <button className="ghostLightButton" onClick={resetComposer}>
                  Reset
                </button>
                <button className="primaryButton" onClick={submitRun} disabled={submitting}>
                  {submitting ? "Working..." : "Summarize"}
                </button>
              </div>
            </div>

            <label className="fieldLabel" htmlFor="goal">
              Goal
            </label>
            <input
              id="goal"
              className="textInput"
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
            />

            <label className="fieldLabel" htmlFor="typedText">
              Paste text
            </label>
            <textarea
              id="typedText"
              className="textField"
              value={typedText}
              onChange={(event) => setTypedText(event.target.value)}
              placeholder="Paste the text you want summarized."
            />

            <div className="uploadDivider">or</div>

            <label className="fieldLabel" htmlFor="pdfFile">
              Upload PDF
            </label>
            <input
              key={fileInputKey}
              id="pdfFile"
              className="fileInput"
              type="file"
              accept=".pdf,application/pdf"
              onChange={(event) => setPdfFile(event.target.files?.[0] || null)}
            />
            {pdfFile ? <p className="fieldHelp">Selected PDF: {pdfFile.name}</p> : null}
          </article>

          <article className="card simpleResult">
            <div className="cardHeading">
              <div>
                <p className="eyebrow">Result</p>
                <h3>Your summary</h3>
              </div>
              {runResponse ? (
                <span className={`statusBadge ${statusTone(runResponse.status)}`}>
                  {runResponse.status}
                </span>
              ) : null}
            </div>

            {runResponse ? (
              <div className="answerBlock">
                <p className="answerText">{cleanAnswer(runResponse.final_answer)}</p>
              </div>
            ) : (
              <div className="emptyState">
                Your summary will appear here after you upload a PDF or paste text.
              </div>
            )}

            {runResponse?.status === "needs_input" ? (
              <div className="followUpBlock">
                <h4>More information needed</h4>
                <p className="fieldHelp">
                  The backend needs a little more information before it can continue.
                </p>
                <div className="missingGrid">
                  {(runResponse.missing_fields || []).map((item) => (
                    <label className="miniField" key={`${item.tool}-${item.field}`}>
                      <span>{item.field}</span>
                      <input
                        className="textInput"
                        type="text"
                        value={followUpValues[item.field] || ""}
                        onChange={(event) =>
                          setFollowUpValues((current) => ({
                            ...current,
                            [item.field]: event.target.value,
                          }))
                        }
                      />
                      <small>{item.reason}</small>
                    </label>
                  ))}
                </div>
                <button className="primaryButton" onClick={continueRun} disabled={submitting}>
                  {submitting ? "Submitting..." : "Continue"}
                </button>
              </div>
            ) : null}
          </article>
        </section>

        <section className="card historyCard">
          <div className="cardHeading">
            <div>
              <p className="eyebrow">Recent Runs</p>
              <h3>Previous summaries</h3>
            </div>
            <button className="ghostLightButton" onClick={fetchRuns} disabled={loadingRuns}>
              {loadingRuns ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {runs.length ? (
            <div className="historyList">
              {runs.map((run) => (
                <div className="historyItem" key={run.run_id}>
                  <div className="historyItemTop">
                    <span className={`statusBadge ${statusTone(run.status)}`}>{run.status}</span>
                    <span className="timestamp">{formatTimestamp(run.created_at)}</span>
                  </div>
                  <strong>{run.user_goal}</strong>
                  <p>{cleanAnswer(run.final_answer)}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="emptyState">No summaries yet.</div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
