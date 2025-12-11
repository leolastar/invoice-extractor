"use client";

import { format } from "date-fns";

interface Order {
  id: number;
  order_number: string;
  invoice_number: string | null;
  invoice_date: string | null;
  customer_name: string | null;
  total: number | null;
  currency: string;
  status: string;
  processing_status: string | null;
  error_message: string | null;
  created_at: string;
}

interface OrderListProps {
  orders: Order[];
  selectedOrder: Order | null;
  onSelectOrder: (order: Order) => void;
  onDeleteOrder: (orderId: number) => void;
}

export default function OrderList({
  orders,
  selectedOrder,
  onSelectOrder,
  onDeleteOrder,
}: OrderListProps) {
  if (orders.length === 0) {
    return (
      <div className="card">
        <p style={{ textAlign: "center", color: "#666", padding: "2rem" }}>
          No invoices processed yet. Upload an invoice to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 style={{ marginBottom: "1.5rem" }}>
        Processed Invoices ({orders.length})
      </h2>
      <div className="grid">
        {orders.map((order) => (
          <div
            key={order.id}
            className="order-card"
            onClick={() => onSelectOrder(order)}
            style={{
              border:
                selectedOrder?.id === order.id ? "3px solid #667eea" : "none",
            }}
          >
            <h3>{order.order_number}</h3>
            {order.invoice_number && (
              <div className="meta">Invoice: {order.invoice_number}</div>
            )}
            {order.customer_name && (
              <div className="meta">Customer: {order.customer_name}</div>
            )}
            {order.invoice_date && (
              <div className="meta">
                Date: {format(new Date(order.invoice_date), "MMM dd, yyyy")}
              </div>
            )}
            <div className="meta">
              Status:{" "}
              <span
                className={`badge badge-${
                  order.status === "completed"
                    ? "success"
                    : order.status === "failed"
                    ? "danger"
                    : "warning"
                }`}
              >
                {order.status}
              </span>
              {order.processing_status &&
                order.processing_status !== order.status && (
                  <span
                    className={`badge badge-${
                      order.processing_status === "completed"
                        ? "success"
                        : order.processing_status === "failed"
                        ? "danger"
                        : "warning"
                    }`}
                    style={{ marginLeft: "0.5rem" }}
                  >
                    {order.processing_status}
                  </span>
                )}
            </div>
            {order.error_message && (
              <div
                className="meta"
                style={{
                  color: "#dc3545",
                  fontSize: "0.85rem",
                  marginTop: "0.5rem",
                }}
              >
                Error: {order.error_message}
              </div>
            )}
            {order.total && (
              <div className="total">
                {order.currency} {order.total.toFixed(2)}
              </div>
            )}
            <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
              <button
                className="btn btn-primary"
                style={{ flex: 1 }}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectOrder(order);
                }}
              >
                View Details
              </button>
              <button
                className="btn btn-danger"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteOrder(order.id);
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
