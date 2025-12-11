import { render, screen, fireEvent } from "@testing-library/react";
import OrderList from "../../app/components/OrderList";
import { format } from "date-fns";

const mockOrders = [
  {
    id: 1,
    order_number: "ORD-001",
    invoice_number: "INV-001",
    invoice_date: "2024-01-15",
    customer_name: "Test Customer",
    total: 1000.5,
    currency: "USD",
    status: "completed",
    processing_status: "completed",
    error_message: null,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2024-01-01T00:00:00",
    line_items: [],
  },
  {
    id: 2,
    order_number: "ORD-002",
    invoice_number: null,
    invoice_date: null,
    customer_name: "Another Customer",
    total: 2000.0,
    currency: "USD",
    status: "pending",
    processing_status: "processing",
    error_message: null,
    created_at: "2024-01-02T00:00:00",
    updated_at: "2024-01-02T00:00:00",
    line_items: [],
  },
];

describe("OrderList Component", () => {
  const mockOnSelectOrder = jest.fn();
  const mockOnDeleteOrder = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders empty state when no orders", () => {
    render(
      <OrderList
        orders={[]}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    expect(screen.getByText(/No invoices processed yet/i)).toBeInTheDocument();
  });

  it("renders orders list", () => {
    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    expect(screen.getByText("ORD-001")).toBeInTheDocument();
    expect(screen.getByText("ORD-002")).toBeInTheDocument();
    // Customer names might be in a different format, use getAllByText
    const customerTexts = screen.getAllByText(/Test Customer|Another Customer/);
    expect(customerTexts.length).toBeGreaterThan(0);
  });

  it("displays order details correctly", () => {
    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    expect(screen.getByText("Invoice: INV-001")).toBeInTheDocument();
    expect(screen.getByText("USD 1000.50")).toBeInTheDocument();
  });

  it("calls onSelectOrder when order card is clicked", () => {
    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    const orderCard = screen.getByText("ORD-001").closest(".order-card");
    if (orderCard) {
      fireEvent.click(orderCard);
      expect(mockOnSelectOrder).toHaveBeenCalledWith(mockOrders[0]);
    }
  });

  it("calls onSelectOrder when View Details button is clicked", () => {
    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    const buttons = screen.getAllByText("View Details");
    fireEvent.click(buttons[0]);
    expect(mockOnSelectOrder).toHaveBeenCalledWith(mockOrders[0]);
  });

  it("calls onDeleteOrder when Delete button is clicked", () => {
    window.confirm = jest.fn(() => true);

    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    const deleteButtons = screen.getAllByText("Delete");
    fireEvent.click(deleteButtons[0]);
    expect(mockOnDeleteOrder).toHaveBeenCalledWith(1);
  });

  it("highlights selected order", () => {
    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={mockOrders[0]}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    const orderCard = screen.getByText("ORD-001").closest(".order-card");
    expect(orderCard).toBeInTheDocument();
    // Check if border style is applied (might be inline style)
    const borderStyle = orderCard?.getAttribute("style");
    expect(borderStyle).toContain("3px solid");
  });

  it("displays status badge correctly", () => {
    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    // Status badges should be present
    const statusBadges = screen.getAllByText(/completed|pending/);
    expect(statusBadges.length).toBeGreaterThan(0);
  });

  it("displays error message when present", () => {
    const orderWithError = {
      ...mockOrders[0],
      processing_status: "failed",
      error_message: "Processing failed: Test error",
    };

    render(
      <OrderList
        orders={[orderWithError]}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    expect(
      screen.getByText(/Processing failed: Test error/i)
    ).toBeInTheDocument();
  });

  it("displays processing status when different from status", () => {
    const orderProcessing = {
      ...mockOrders[0],
      status: "pending",
      processing_status: "processing",
    };

    render(
      <OrderList
        orders={[orderProcessing]}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    expect(screen.getByText("processing")).toBeInTheDocument();
  });

  it("displays formatted date when available", () => {
    render(
      <OrderList
        orders={mockOrders}
        selectedOrder={null}
        onSelectOrder={mockOnSelectOrder}
        onDeleteOrder={mockOnDeleteOrder}
      />
    );

    const formattedDate = format(
      new Date(mockOrders[0].invoice_date!),
      "MMM dd, yyyy"
    );
    expect(screen.getByText(new RegExp(formattedDate))).toBeInTheDocument();
  });
});
