"use client";

import { useState, useEffect } from "react";
import { format } from "date-fns";

interface LineItem {
  id: number;
  order_id: number;
  line_number: number | null;
  product_code: string | null;
  product_name: string | null;
  description: string | null;
  quantity: number | null;
  unit_price: number | null;
  discount: number;
  line_total: number | null;
}

interface Order {
  id: number;
  order_number: string;
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  customer_name: string | null;
  customer_address: string | null;
  customer_email: string | null;
  customer_phone: string | null;
  subtotal: number | null;
  tax: number | null;
  total: number | null;
  currency: string;
  status: string;
  processing_status: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  line_items: LineItem[];
}

interface OrderDetailProps {
  order: Order;
  onUpdate: (order: Order) => void;
  onClose: () => void;
}

export default function OrderDetail({
  order,
  onUpdate,
  onClose,
}: OrderDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedOrder, setEditedOrder] = useState<Order>(order);

  useEffect(() => {
    setEditedOrder(order);
  }, [order]);

  const handleSave = () => {
    onUpdate(editedOrder);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedOrder(order);
    setIsEditing(false);
  };

  const updateField = (field: keyof Order, value: any) => {
    setEditedOrder({ ...editedOrder, [field]: value });
  };

  const updateLineItem = (index: number, field: keyof LineItem, value: any) => {
    const updatedItems = [...editedOrder.line_items];
    updatedItems[index] = { ...updatedItems[index], [field]: value };

    // Recalculate line total
    const item = updatedItems[index];
    if (item.quantity && item.unit_price) {
      const subtotal = item.quantity * item.unit_price;
      const discountAmount = (subtotal * (item.discount || 0)) / 100;
      item.line_total = subtotal - discountAmount;
    }

    setEditedOrder({ ...editedOrder, line_items: updatedItems });

    // Recalculate order totals
    const newSubtotal = updatedItems.reduce(
      (sum, item) => sum + (item.line_total || 0),
      0
    );
    const newTax = newSubtotal * 0.1; // 10% tax (adjust as needed)
    const newTotal = newSubtotal + newTax;

    setEditedOrder((prev) => ({
      ...prev,
      subtotal: newSubtotal,
      tax: newTax,
      total: newTotal,
      line_items: updatedItems,
    }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Order Details: {order.order_number}</h2>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {order.error_message && (
          <div
            style={{
              margin: "1rem 0",
              padding: "1rem",
              backgroundColor: "#fee",
              border: "1px solid #fcc",
              borderRadius: "8px",
              color: "#c33",
            }}
          >
            <strong>Processing Error:</strong> {order.error_message}
          </div>
        )}

        {order.processing_status &&
          order.processing_status !== "completed" &&
          order.processing_status !== "failed" && (
            <div
              style={{
                margin: "1rem 0",
                padding: "1rem",
                backgroundColor: "#fff3cd",
                border: "1px solid #ffc107",
                borderRadius: "8px",
                color: "#856404",
              }}
            >
              <strong>Processing Status:</strong> {order.processing_status}
            </div>
          )}

        <div style={{ marginBottom: "1.5rem" }}>
          <button
            className="btn btn-primary"
            onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
            style={{ marginRight: "0.5rem" }}
          >
            {isEditing ? "Save Changes" : "Edit"}
          </button>
          {isEditing && (
            <button className="btn btn-secondary" onClick={handleCancel}>
              Cancel
            </button>
          )}
        </div>

        <div className="form-grid">
          <div className="input-group">
            <label>Order Number</label>
            <input
              type="text"
              value={editedOrder.order_number}
              disabled
              style={{ backgroundColor: "#f5f5f5" }}
            />
          </div>

          <div className="input-group">
            <label>Invoice Number</label>
            <input
              type="text"
              value={editedOrder.invoice_number || ""}
              onChange={(e) => updateField("invoice_number", e.target.value)}
              disabled={!isEditing}
            />
          </div>

          <div className="input-group">
            <label>Invoice Date</label>
            <input
              type="date"
              value={
                editedOrder.invoice_date
                  ? editedOrder.invoice_date.split("T")[0]
                  : ""
              }
              onChange={(e) =>
                updateField("invoice_date", e.target.value || null)
              }
              disabled={!isEditing}
            />
          </div>

          <div className="input-group">
            <label>Due Date</label>
            <input
              type="date"
              value={
                editedOrder.due_date ? editedOrder.due_date.split("T")[0] : ""
              }
              onChange={(e) => updateField("due_date", e.target.value || null)}
              disabled={!isEditing}
            />
          </div>

          <div className="input-group">
            <label>Customer Name</label>
            <input
              type="text"
              value={editedOrder.customer_name || ""}
              onChange={(e) => updateField("customer_name", e.target.value)}
              disabled={!isEditing}
            />
          </div>

          <div className="input-group">
            <label>Customer Email</label>
            <input
              type="email"
              value={editedOrder.customer_email || ""}
              onChange={(e) => updateField("customer_email", e.target.value)}
              disabled={!isEditing}
            />
          </div>

          <div className="input-group">
            <label>Customer Phone</label>
            <input
              type="text"
              value={editedOrder.customer_phone || ""}
              onChange={(e) => updateField("customer_phone", e.target.value)}
              disabled={!isEditing}
            />
          </div>

          <div className="input-group">
            <label>Status</label>
            <select
              value={editedOrder.status}
              onChange={(e) => updateField("status", e.target.value)}
              disabled={!isEditing}
              style={{
                width: "100%",
                padding: "0.75rem",
                border: "2px solid #e0e0e0",
                borderRadius: "8px",
                fontSize: "1rem",
              }}
            >
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div className="input-group" style={{ gridColumn: "1 / -1" }}>
            <label>Customer Address</label>
            <textarea
              value={editedOrder.customer_address || ""}
              onChange={(e) => updateField("customer_address", e.target.value)}
              disabled={!isEditing}
              rows={3}
            />
          </div>
        </div>

        <h3 style={{ marginTop: "2rem", marginBottom: "1rem" }}>Line Items</h3>
        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Line #</th>
                <th>Product Code</th>
                <th>Product Name</th>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Discount %</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              {editedOrder.line_items.map((item, index) => (
                <tr key={item.id}>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        value={item.line_number || ""}
                        onChange={(e) =>
                          updateLineItem(
                            index,
                            "line_number",
                            parseInt(e.target.value) || null
                          )
                        }
                        style={{ width: "60px", padding: "0.5rem" }}
                      />
                    ) : (
                      item.line_number
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="text"
                        value={item.product_code || ""}
                        onChange={(e) =>
                          updateLineItem(index, "product_code", e.target.value)
                        }
                        style={{ width: "100px", padding: "0.5rem" }}
                      />
                    ) : (
                      item.product_code
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="text"
                        value={item.product_name || ""}
                        onChange={(e) =>
                          updateLineItem(index, "product_name", e.target.value)
                        }
                        style={{ width: "150px", padding: "0.5rem" }}
                      />
                    ) : (
                      item.product_name
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="text"
                        value={item.description || ""}
                        onChange={(e) =>
                          updateLineItem(index, "description", e.target.value)
                        }
                        style={{ width: "200px", padding: "0.5rem" }}
                      />
                    ) : (
                      item.description
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.01"
                        value={item.quantity || ""}
                        onChange={(e) =>
                          updateLineItem(
                            index,
                            "quantity",
                            parseFloat(e.target.value) || null
                          )
                        }
                        style={{ width: "80px", padding: "0.5rem" }}
                      />
                    ) : (
                      item.quantity
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.01"
                        value={item.unit_price || ""}
                        onChange={(e) =>
                          updateLineItem(
                            index,
                            "unit_price",
                            parseFloat(e.target.value) || null
                          )
                        }
                        style={{ width: "100px", padding: "0.5rem" }}
                      />
                    ) : item.unit_price ? (
                      `$${item.unit_price.toFixed(2)}`
                    ) : (
                      ""
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.01"
                        value={item.discount || 0}
                        onChange={(e) =>
                          updateLineItem(
                            index,
                            "discount",
                            parseFloat(e.target.value) || 0
                          )
                        }
                        style={{ width: "80px", padding: "0.5rem" }}
                      />
                    ) : (
                      `${item.discount || 0}%`
                    )}
                  </td>
                  <td>
                    {item.line_total ? `$${item.line_total.toFixed(2)}` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div
          style={{
            marginTop: "2rem",
            padding: "1.5rem",
            backgroundColor: "#f8f9fa",
            borderRadius: "8px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: "0.5rem",
            }}
          >
            <strong>Subtotal:</strong>
            <strong>${editedOrder.subtotal?.toFixed(2) || "0.00"}</strong>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: "0.5rem",
            }}
          >
            <strong>Tax:</strong>
            <strong>${editedOrder.tax?.toFixed(2) || "0.00"}</strong>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "1.2rem",
              paddingTop: "0.5rem",
              borderTop: "2px solid #ddd",
            }}
          >
            <strong>Total ({editedOrder.currency}):</strong>
            <strong>${editedOrder.total?.toFixed(2) || "0.00"}</strong>
          </div>
        </div>

        <div style={{ marginTop: "1rem", color: "#666", fontSize: "0.9rem" }}>
          Created: {format(new Date(order.created_at), "MMM dd, yyyy HH:mm")}
          {order.updated_at !== order.created_at && (
            <>
              {" "}
              | Updated:{" "}
              {format(new Date(order.updated_at), "MMM dd, yyyy HH:mm")}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
