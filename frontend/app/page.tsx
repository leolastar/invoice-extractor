"use client";

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useDropzone } from "react-dropzone";
import OrderList from "./components/OrderList";
import OrderDetail from "./components/OrderDetail";
import Stats from "./components/Stats";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

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

export default function Home() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  const fetchOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_URL}/api/orders`);
      setOrders(response.data.orders);
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error || err.message || "Failed to fetch orders";
      console.error("Error fetching orders:", err);
      setError(
        `Failed to fetch orders: ${errorMsg}. Is the backend running at ${API_URL}?`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/stats`);
      setStats(response.data);
    } catch (err) {
      console.error("Failed to fetch stats:", err);
      // Don't show error for stats, it's not critical
    }
  }, []);

  useEffect(() => {
    // Check backend health first
    const checkBackendHealth = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/health`);
        console.log("Backend health check:", response.data);
        // Backend is healthy, fetch data
        fetchOrders();
        fetchStats();
      } catch (err: any) {
        console.error("Backend health check failed:", err);
        setError(
          `Cannot connect to backend at ${API_URL}. Please ensure the backend service is running. ` +
            `Error: ${err.message || "Connection refused"}`
        );
      }
    };

    checkBackendHealth();
  }, [fetchOrders, fetchStats]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setUploading(true);
      setError(null);
      setSuccess(null);

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await axios.post(`${API_URL}/api/upload`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        setSuccess("Invoice uploaded and queued for processing!");
        await fetchOrders();
        await fetchStats();
        setSelectedOrder(response.data.order);

        // Poll for task status if task_id is provided
        if (response.data.task_id) {
          pollTaskStatus(response.data.task_id, response.data.order_id);
        }

        // Clear success message after 5 seconds
        setTimeout(() => setSuccess(null), 5000);
      } catch (err: any) {
        setError(err.response?.data?.error || "Failed to process invoice");
      } finally {
        setUploading(false);
      }
    },
    [fetchOrders, fetchStats]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/*": [".png", ".jpg", ".jpeg", ".gif"],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  const handleOrderUpdate = async (updatedOrder: Order) => {
    try {
      await axios.put(`${API_URL}/api/orders/${updatedOrder.id}`, updatedOrder);
      setSuccess("Order updated successfully!");
      await fetchOrders();
      await fetchStats();
      setSelectedOrder(updatedOrder);
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to update order");
    }
  };

  const pollTaskStatus = async (
    taskId: string,
    orderId: number,
    maxAttempts: number = 30
  ) => {
    let attempts = 0;
    const pollInterval = setInterval(async () => {
      attempts++;
      try {
        const response = await axios.get(`${API_URL}/api/tasks/${taskId}`);
        const taskState = response.data.state;

        if (taskState === "SUCCESS") {
          clearInterval(pollInterval);
          setSuccess("Invoice processed successfully!");
          await fetchOrders();
          await fetchStats();
          // Update selected order if it's the one being processed
          if (selectedOrder?.id === orderId) {
            const updatedOrders = await axios.get(`${API_URL}/api/orders`);
            const updatedOrder = updatedOrders.data.orders.find(
              (o: Order) => o.id === orderId
            );
            if (updatedOrder) setSelectedOrder(updatedOrder);
          }
          setTimeout(() => setSuccess(null), 5000);
        } else if (taskState === "FAILURE") {
          clearInterval(pollInterval);
          await fetchOrders();
          await fetchStats();
          // Get the order to show error message
          const orderResponse = await axios.get(
            `${API_URL}/api/orders/${orderId}`
          );
          const failedOrder = orderResponse.data;
          if (failedOrder.error_message) {
            setError(`Processing failed: ${failedOrder.error_message}`);
          } else {
            setError(
              `Processing failed: ${response.data.error || "Unknown error"}`
            );
          }
          if (selectedOrder?.id === orderId) {
            setSelectedOrder(failedOrder);
          }
        } else if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          setError(
            "Processing is taking longer than expected. Please refresh to check status."
          );
        }
      } catch (err) {
        // Continue polling on error
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
        }
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleOrderDelete = async (orderId: number) => {
    if (!confirm("Are you sure you want to delete this order?")) return;

    try {
      await axios.delete(`${API_URL}/api/orders/${orderId}`);
      setSuccess("Order deleted successfully!");
      await fetchOrders();
      await fetchStats();
      if (selectedOrder?.id === orderId) {
        setSelectedOrder(null);
      }
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to delete order");
    }
  };

  return (
    <main>
      <div className="header">
        <div className="container">
          <h1>Invoice Extractor</h1>
          <p>AI-powered document extraction and management system</p>
        </div>
      </div>

      <div className="container">
        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        <Stats stats={stats} />

        <div className="card">
          <h2 style={{ marginBottom: "1rem" }}>Upload Invoice</h2>
          <div
            {...getRootProps()}
            style={{
              border: "2px dashed",
              borderColor: isDragActive ? "#667eea" : "#ccc",
              borderRadius: "12px",
              padding: "3rem",
              textAlign: "center",
              cursor: uploading ? "not-allowed" : "pointer",
              backgroundColor: isDragActive ? "#f0f4ff" : "#fafafa",
              transition: "all 0.3s ease",
              opacity: uploading ? 0.6 : 1,
            }}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p style={{ marginLeft: "1rem" }}>Processing invoice...</p>
              </div>
            ) : (
              <>
                <p style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>
                  {isDragActive
                    ? "Drop the file here..."
                    : "Drag & drop an invoice file here, or click to select"}
                </p>
                <p style={{ color: "#666", fontSize: "0.9rem" }}>
                  Supports PDF and image files (PNG, JPG, JPEG, GIF)
                </p>
              </>
            )}
          </div>
        </div>

        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        ) : (
          <>
            <OrderList
              orders={orders}
              selectedOrder={selectedOrder}
              onSelectOrder={setSelectedOrder}
              onDeleteOrder={handleOrderDelete}
            />

            {selectedOrder && (
              <OrderDetail
                order={selectedOrder}
                onUpdate={handleOrderUpdate}
                onClose={() => setSelectedOrder(null)}
              />
            )}
          </>
        )}
      </div>
    </main>
  );
}
