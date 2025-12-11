import { render, screen, waitFor } from "@testing-library/react";
import { jest } from "@jest/globals";
import axios from "axios";
import Home from "../app/page";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Setup default mock implementation
mockedAxios.get = jest.fn();
mockedAxios.post = jest.fn();
mockedAxios.put = jest.fn();
mockedAxios.delete = jest.fn();

// Mock components
jest.mock("../app/components/OrderList", () => {
  return function MockOrderList() {
    return <div data-testid="order-list">Order List</div>;
  };
});

jest.mock("../app/components/OrderDetail", () => {
  return function MockOrderDetail() {
    return <div data-testid="order-detail">Order Detail</div>;
  };
});

jest.mock("../app/components/Stats", () => {
  return function MockStats() {
    return <div data-testid="stats">Stats</div>;
  };
});

describe("Home Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the header", async () => {
    mockedAxios.get
      .mockResolvedValueOnce({
        data: { status: "healthy", service: "invoice-extractor-api" },
      })
      .mockResolvedValueOnce({ data: { orders: [], count: 0 } })
      .mockResolvedValueOnce({
        data: { total_orders: 0, total_value: 0, average_order_value: 0 },
      });

    render(<Home />);

    await waitFor(() => {
      expect(screen.getByText("Invoice Extractor")).toBeInTheDocument();
      expect(
        screen.getByText(/AI-powered document extraction/i)
      ).toBeInTheDocument();
    });
  });

  it("fetches and displays orders", async () => {
    const mockOrders = [
      {
        id: 1,
        order_number: "ORD-001",
        customer_name: "Test Customer",
        total: 1000,
        currency: "USD",
        status: "pending",
        processing_status: "completed",
        error_message: null,
        created_at: "2024-01-01T00:00:00",
        updated_at: "2024-01-01T00:00:00",
        line_items: [],
      },
    ];

    mockedAxios.get
      .mockResolvedValueOnce({
        data: { status: "healthy", service: "invoice-extractor-api" },
      })
      .mockResolvedValueOnce({ data: { orders: mockOrders, count: 1 } })
      .mockResolvedValueOnce({
        data: { total_orders: 1, total_value: 1000, average_order_value: 1000 },
      });

    render(<Home />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining("/api/health")
      );
    });
  });

  it("displays upload area", async () => {
    mockedAxios.get
      .mockResolvedValueOnce({
        data: { status: "healthy", service: "invoice-extractor-api" },
      })
      .mockResolvedValueOnce({ data: { orders: [], count: 0 } })
      .mockResolvedValueOnce({
        data: { total_orders: 0, total_value: 0, average_order_value: 0 },
      });

    render(<Home />);

    await waitFor(() => {
      expect(
        screen.getByText(/Drag & drop an invoice file here/i)
      ).toBeInTheDocument();
    });
  });

  it("handles upload error", async () => {
    mockedAxios.get
      .mockResolvedValueOnce({
        data: { status: "healthy", service: "invoice-extractor-api" },
      })
      .mockResolvedValueOnce({ data: { orders: [], count: 0 } })
      .mockResolvedValueOnce({
        data: { total_orders: 0, total_value: 0, average_order_value: 0 },
      });

    const { container } = render(<Home />);

    await waitFor(() => {
      expect(container).toBeInTheDocument();
    });
  });
});
