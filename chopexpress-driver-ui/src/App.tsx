import { useEffect, useState } from "react";
import { MapPin, DollarSign, Truck } from "lucide-react";

type Order = {
  id: string;
  pickup: string;
  dropoff: string;
  miles: number;
  offer: number;
  status?: string;
};

export default function App() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [earnings, setEarnings] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    async function loadOrders() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch("http://127.0.0.1:8000/orders");

        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data = await response.json();

        const normalizedOrders: Order[] = Array.isArray(data)
          ? data.map((order: any, index: number) => ({
              id: order.id ?? `ORD-${index + 1}`,
              pickup: order.pickup ?? order.merchant_name ?? "Pickup location",
              dropoff: order.dropoff ?? order.customer_name ?? "Dropoff location",
              miles: Number(order.miles ?? order.total_economic_miles ?? 0),
              offer: Number(order.offer ?? order.chopexpress_pay ?? 0),
              status: order.status ?? "available",
            }))
          : [];

        setOrders(normalizedOrders);

        const total = normalizedOrders.reduce((sum, order) => sum + order.offer, 0);
        setEarnings(Number(total.toFixed(2)));
      } catch (err) {
        console.error("Failed to load backend orders:", err);

        const fallbackOrders: Order[] = [
          {
            id: "ORD-1001",
            pickup: "Chipotle High St",
            dropoff: "OSU Dorms",
            miles: 3.1,
            offer: 9.5,
            status: "available",
          },
          {
            id: "ORD-1002",
            pickup: "McDonald's Hudson",
            dropoff: "Clintonville",
            miles: 2.4,
            offer: 7.25,
            status: "available",
          },
          {
            id: "ORD-1003",
            pickup: "KFC Morse Rd",
            dropoff: "Easton Area",
            miles: 4.2,
            offer: 11.0,
            status: "available",
          },
        ];

        setOrders(fallbackOrders);
        setEarnings(
          Number(fallbackOrders.reduce((sum, order) => sum + order.offer, 0).toFixed(2))
        );
        setError("Backend orders endpoint not available. Showing demo orders.");
      } finally {
        setLoading(false);
      }
    }

    loadOrders();
  }, []);

  function handleAcceptOrder(orderId: string) {
    setOrders((prev) =>
      prev.map((order) =>
        order.id === orderId ? { ...order, status: "accepted" } : order
      )
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0f172a",
        color: "#f8fafc",
        fontFamily: "Arial, sans-serif",
        padding: "32px",
      }}
    >
      <div
        style={{
          maxWidth: "960px",
          margin: "0 auto",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            marginBottom: "24px",
          }}
        >
          <Truck size={34} />
          <div>
            <h1 style={{ margin: 0 }}>ChopExpress Driver Console</h1>
            <p style={{ margin: "6px 0 0 0", color: "#cbd5e1" }}>
              Fairness-first logistics driver interface
            </p>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              background: "#111827",
              border: "1px solid #334155",
              borderRadius: "12px",
              padding: "18px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <DollarSign size={20} />
              <strong>Earnings Snapshot</strong>
            </div>
            <div style={{ fontSize: "28px", marginTop: "12px", fontWeight: 700 }}>
              ${earnings.toFixed(2)}
            </div>
          </div>

          <div
            style={{
              background: "#111827",
              border: "1px solid #334155",
              borderRadius: "12px",
              padding: "18px",
            }}
          >
            <strong>Available Orders</strong>
            <div style={{ fontSize: "28px", marginTop: "12px", fontWeight: 700 }}>
              {orders.filter((o) => o.status !== "accepted").length}
            </div>
          </div>
        </div>

        {error && (
          <div
            style={{
              background: "#3f1d1d",
              border: "1px solid #7f1d1d",
              color: "#fecaca",
              padding: "14px 16px",
              borderRadius: "10px",
              marginBottom: "20px",
            }}
          >
            {error}
          </div>
        )}

        {loading ? (
          <div
            style={{
              background: "#111827",
              border: "1px solid #334155",
              borderRadius: "12px",
              padding: "20px",
            }}
          >
            Loading orders...
          </div>
        ) : (
          <div style={{ display: "grid", gap: "16px" }}>
            {orders.map((order) => (
              <div
                key={order.id}
                style={{
                  background: "#111827",
                  border: "1px solid #334155",
                  borderRadius: "12px",
                  padding: "20px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: "16px",
                    flexWrap: "wrap",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "8px" }}>
                      {order.id}
                    </div>

                    <h3
                      style={{
                        margin: "0 0 10px 0",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <MapPin size={18} />
                      Pickup: {order.pickup}
                    </h3>

                    <p style={{ margin: "6px 0" }}>Dropoff: {order.dropoff}</p>
                    <p style={{ margin: "6px 0" }}>Miles: {order.miles}</p>
                    <p style={{ margin: "6px 0", fontWeight: 700 }}>
                      Offer: ${order.offer.toFixed(2)}
                    </p>
                    <p style={{ margin: "6px 0", color: "#94a3b8" }}>
                      Status: {order.status}
                    </p>
                  </div>

                  <button
                    onClick={() => handleAcceptOrder(order.id)}
                    disabled={order.status === "accepted"}
                    style={{
                      background: order.status === "accepted" ? "#475569" : "#16a34a",
                      color: "#ffffff",
                      padding: "10px 18px",
                      border: "none",
                      borderRadius: "8px",
                      cursor: order.status === "accepted" ? "not-allowed" : "pointer",
                      fontWeight: 700,
                      minWidth: "140px",
                    }}
                  >
                    {order.status === "accepted" ? "Accepted" : "Accept Order"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}