import { useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

const SAMPLE_REQUEST = {
  order_id: "TEST1001",
  merchant: "Test Kitchen",
  zone: "clintonville",
  tier: "professional",
  delivery_distance: 3.4,
  pickup_distance: 2.1,
  return_distance: 2.5,
  order_value: 26.25,
  offered_payout: 8.75,
  tip: 4.0,
  estimated_total_minutes: 24,
  merchant_risk_score: 0.35,
  zone_pressure_score: 1.2,
  is_batched_order: false,
  sales_tax_rate: 0.075,
  commission_rate: 0.18,
  processing_rate: 0.03,
  fixed_processing_fee: 0.3,
  promo_support: 0.0,
  merchant_id: "M-001",
  customer_month_orders: 14,
  customer_points: 220,
};

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export default function App() {
  const [requestText, setRequestText] = useState<string>(
    JSON.stringify(SAMPLE_REQUEST, null, 2)
  );
  const [resultText, setResultText] = useState<string>("");
  const [statusText, setStatusText] = useState<string>("Checking backend...");
  const [healthOk, setHealthOk] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastError, setLastError] = useState<string>("");

  const endpoint = useMemo(() => `${API_BASE}/evaluate-order`, []);

  async function checkHealth() {
    try {
      const response = await fetch(`${API_BASE}/health`, {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Health check failed with status ${response.status}`);
      }

      const data = await response.json();
      setHealthOk(true);
      setStatusText(
        `Backend connected on ${API_BASE} · ${JSON.stringify(data)}`
      );
      setLastError("");
    } catch (error) {
      setHealthOk(false);
      setStatusText(`Backend unavailable on ${API_BASE}`);
      setLastError(error instanceof Error ? error.message : "Unknown error");
    }
  }

  useEffect(() => {
    void checkHealth();
  }, []);

  async function runSimulation() {
    setIsRunning(true);
    setLastError("");

    try {
      let parsedPayload: JsonValue;
      try {
        parsedPayload = JSON.parse(requestText) as JsonValue;
      } catch {
        throw new Error("Request JSON is invalid. Fix the JSON and try again.");
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(parsedPayload),
      });

      const rawText = await response.text();

      let parsedResponse: unknown = rawText;
      try {
        parsedResponse = JSON.parse(rawText);
      } catch {
        parsedResponse = rawText;
      }

      if (!response.ok) {
        setResultText(
          typeof parsedResponse === "string"
            ? parsedResponse
            : JSON.stringify(parsedResponse, null, 2)
        );
        throw new Error(`API returned status ${response.status}`);
      }

      setResultText(JSON.stringify(parsedResponse, null, 2));
      setStatusText(`Simulation completed successfully · ${endpoint}`);
      setHealthOk(true);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown request error";
      setLastError(message);
      setStatusText(`Simulation failed · ${endpoint}`);
      if (!resultText) {
        setResultText(
          JSON.stringify(
            {
              status: "error",
              message,
            },
            null,
            2
          )
        );
      }
    } finally {
      setIsRunning(false);
    }
  }

  function resetSample() {
    setRequestText(JSON.stringify(SAMPLE_REQUEST, null, 2));
    setResultText("");
    setLastError("");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top, #0f3d6e 0%, #081426 45%, #040814 100%)",
        color: "#e8f3ff",
        fontFamily:
          "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        padding: "32px 20px",
      }}
    >
      <div style={{ maxWidth: 1400, margin: "0 auto" }}>
        <header style={{ marginBottom: 28 }}>
          <h1
            style={{
              fontSize: 48,
              fontWeight: 800,
              lineHeight: 1.05,
              margin: 0,
              textAlign: "center",
            }}
          >
            ChopExpress Logistics Simulator
          </h1>

          <p
            style={{
              marginTop: 14,
              textAlign: "center",
              fontSize: 18,
              color: "#9fd0ff",
              maxWidth: 1000,
              marginLeft: "auto",
              marginRight: "auto",
            }}
          >
            Driver fairness, dispatch viability, insurance, merchant finance,
            tax, settlement, driver tax reserve, and customer loyalty in one
            evaluation flow.
          </p>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.1fr 0.9fr",
            gap: 24,
            alignItems: "start",
          }}
        >
          <section
            style={{
              background: "rgba(10, 24, 44, 0.82)",
              border: "1px solid rgba(120, 190, 255, 0.28)",
              borderRadius: 20,
              padding: 22,
              boxShadow: "0 18px 40px rgba(0, 0, 0, 0.28)",
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: 18,
                fontSize: 28,
                textAlign: "center",
              }}
            >
              Simulation Request
            </h2>

            <textarea
              value={requestText}
              onChange={(e) => setRequestText(e.target.value)}
              spellCheck={false}
              style={{
                width: "100%",
                minHeight: 470,
                resize: "vertical",
                borderRadius: 16,
                border: "1px solid rgba(120, 190, 255, 0.28)",
                background: "#07111f",
                color: "#b9f6ca",
                padding: 18,
                fontSize: 15,
                lineHeight: 1.5,
                fontFamily:
                  "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace",
                boxSizing: "border-box",
                outline: "none",
              }}
            />

            <div
              style={{
                display: "flex",
                gap: 14,
                marginTop: 18,
                flexWrap: "wrap",
              }}
            >
              <button
                onClick={() => void runSimulation()}
                disabled={isRunning}
                style={buttonPrimary}
              >
                {isRunning ? "Running..." : "Run Order Simulation"}
              </button>

              <button onClick={resetSample} style={buttonSecondary}>
                Reset Sample
              </button>

              <button onClick={() => void checkHealth()} style={buttonSecondary}>
                Recheck Backend
              </button>
            </div>

            <div
              style={{
                marginTop: 18,
                padding: "14px 16px",
                borderRadius: 14,
                border: `1px solid ${
                  healthOk
                    ? "rgba(74, 222, 128, 0.4)"
                    : "rgba(248, 113, 113, 0.4)"
                }`,
                background: healthOk
                  ? "rgba(22, 101, 52, 0.18)"
                  : "rgba(127, 29, 29, 0.18)",
                color: healthOk ? "#bbf7d0" : "#fecaca",
                fontWeight: 600,
              }}
            >
              {statusText}
              {lastError ? (
                <div style={{ marginTop: 8, fontWeight: 500 }}>{lastError}</div>
              ) : null}
            </div>
          </section>

          <section
            style={{
              background: "rgba(10, 24, 44, 0.82)",
              border: "1px solid rgba(120, 190, 255, 0.28)",
              borderRadius: 20,
              padding: 22,
              boxShadow: "0 18px 40px rgba(0, 0, 0, 0.28)",
              minHeight: 720,
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: 18,
                fontSize: 28,
                textAlign: "center",
              }}
            >
              Simulation Output
            </h2>

            <div
              style={{
                marginBottom: 16,
                padding: 14,
                borderRadius: 14,
                background: "rgba(9, 19, 35, 0.8)",
                border: "1px solid rgba(120, 190, 255, 0.2)",
                color: "#dbeafe",
              }}
            >
              <div style={{ marginBottom: 6 }}>
                <strong>Frontend:</strong> running on localhost:5173
              </div>
              <div style={{ marginBottom: 6 }}>
                <strong>Backend:</strong> expected on 127.0.0.1:8000
              </div>
              <div>
                <strong>Endpoint:</strong> {endpoint}
              </div>
            </div>

            <pre
              style={{
                minHeight: 610,
                margin: 0,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                borderRadius: 16,
                border: "1px solid rgba(120, 190, 255, 0.28)",
                background: "#07111f",
                color: resultText ? "#f8fafc" : "#7dd3fc",
                padding: 18,
                fontSize: 14,
                lineHeight: 1.55,
                overflow: "auto",
                fontFamily:
                  "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace",
              }}
            >
              {resultText ||
                `No simulation result yet.

1. Confirm backend is running:
   python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000

2. Click "Run Order Simulation"

3. Result JSON will appear here.`}
            </pre>
          </section>
        </div>
      </div>
    </div>
  );
}

const buttonPrimary: React.CSSProperties = {
  border: "none",
  borderRadius: 12,
  padding: "14px 20px",
  fontSize: 16,
  fontWeight: 700,
  cursor: "pointer",
  background: "linear-gradient(135deg, #34d399, #22c55e)",
  color: "#062312",
  boxShadow: "0 10px 24px rgba(34, 197, 94, 0.25)",
};

const buttonSecondary: React.CSSProperties = {
  border: "1px solid rgba(120, 190, 255, 0.28)",
  borderRadius: 12,
  padding: "14px 20px",
  fontSize: 16,
  fontWeight: 700,
  cursor: "pointer",
  background: "rgba(14, 31, 56, 0.9)",
  color: "#dbeafe",
};