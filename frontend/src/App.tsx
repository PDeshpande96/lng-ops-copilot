import { useState } from "react";
import axios from "axios";

type AnalysisResult = {
  summary: string;
  possible_causes: string[];
  recommended_checks: string[];
  confidence: string;
  tools_used: string[];
  sources: string[];
};

export default function App() {
  const [issue, setIssue] = useState(
    "Pump-14 shows overheating and vibration spikes during continuous operation. Has this happened before, and what should the operator check first?"
  );
  const [assetId, setAssetId] = useState("Pump-14");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");

  const analyze = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await axios.post<AnalysisResult>(
        "http://127.0.0.1:8000/analyze",
        {
          issue,
          asset_id: assetId,
        }
      );

      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError("Failed to analyze incident.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-10">
      <div className="mx-auto max-w-6xl">
        <h1 className="text-4xl font-bold text-cyan-400">LNG Ops Copilot</h1>
        <p className="mt-2 text-slate-300">
          Agentic AI incident analysis demo for LNG operations
        </p>

        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg">
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Asset ID
            </label>
            <select
              value={assetId}
              onChange={(e) => setAssetId(e.target.value)}
              className="w-full rounded-lg bg-slate-800 p-3 text-white outline-none"
            >
              <option value="Pump-14">Pump-14</option>
              <option value="Pump-22">Pump-22</option>
            </select>

            <label className="mb-2 mt-4 block text-sm font-medium text-slate-300">
              Incident Description
            </label>
            <textarea
              value={issue}
              onChange={(e) => setIssue(e.target.value)}
              rows={8}
              className="w-full rounded-lg bg-slate-800 p-3 text-white outline-none"
            />

            <button
              onClick={analyze}
              disabled={loading}
              className="mt-4 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Analyze Incident"}
            </button>

            {error && <p className="mt-3 text-red-400">{error}</p>}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg">
            {!result ? (
              <p className="text-slate-400">
                Run an analysis to view the agent output.
              </p>
            ) : (
              <div className="space-y-5">
                <div>
                  <h2 className="text-lg font-semibold text-cyan-400">Summary</h2>
                  <p className="mt-2 text-slate-200">{result.summary}</p>
                </div>

                <div>
                  <h2 className="text-lg font-semibold text-cyan-400">
                    Possible Causes
                  </h2>
                  <ul className="mt-2 list-disc pl-5 text-slate-200">
                    {result.possible_causes.map((item, index) => (
                      <li key={`${item}-${index}`}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h2 className="text-lg font-semibold text-cyan-400">
                    Recommended Checks
                  </h2>
                  <ul className="mt-2 list-disc pl-5 text-slate-200">
                    {result.recommended_checks.map((item, index) => (
                      <li key={`${item}-${index}`}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h2 className="text-lg font-semibold text-cyan-400">
                      Confidence
                    </h2>
                    <p className="mt-2 text-slate-200">{result.confidence}</p>
                  </div>

                  <div>
                    <h2 className="text-lg font-semibold text-cyan-400">
                      Tools Used
                    </h2>
                    <ul className="mt-2 list-disc pl-5 text-slate-200">
                      {result.tools_used.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div>
                  <h2 className="text-lg font-semibold text-cyan-400">Sources</h2>
                  <ul className="mt-2 list-disc pl-5 text-slate-200">
                    {result.sources.map((item, index) => (
                      <li key={`${item}-${index}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}