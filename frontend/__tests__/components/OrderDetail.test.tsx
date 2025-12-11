import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import OrderDetail from "../../app/components/OrderDetail";

const mockOrder = {
  id: 1,
  order_number: "ORD-001",
  invoice_number: "INV-001",
  invoice_date: "2024-01-15",
  due_date: "2024-02-15",
  customer_name: "Test Customer",
  customer_address: "123 Test St",
  customer_email: "test@example.com",
  customer_phone: "123-456-7890",
  subtotal: 1000.0,
  tax: 100.0,
  total: 1100.0,
  currency: "USD",
  status: "pending",
  processing_status: "completed",
  error_message: null,
  created_at: "2024-01-01T00:00:00",
  updated_at: "2024-01-01T00:00:00",
  line_items: [
    {
      id: 1,
      order_id: 1,
      line_number: 1,
      product_code: "PROD-001",
      product_name: "Product 1",
      description: "Description 1",
      quantity: 2,
      unit_price: 500.0,
      discount: 0,
      line_total: 1000.0,
    },
  ],
};

describe("OrderDetail Component", () => {
  const mockOnUpdate = jest.fn();
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders order details", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText("Order Details: ORD-001")).toBeInTheDocument();
    expect(screen.getByDisplayValue("INV-001")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Test Customer")).toBeInTheDocument();
  });

  it("renders line items table", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText("Product 1")).toBeInTheDocument();
    expect(screen.getByText("PROD-001")).toBeInTheDocument();
  });

  it("opens edit mode when Edit button is clicked", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    const editButton = screen.getByText("Edit");
    fireEvent.click(editButton);

    expect(screen.getByText("Save Changes")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("allows editing customer name", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    fireEvent.click(screen.getByText("Edit"));

    const customerNameInput = screen.getByDisplayValue("Test Customer");
    fireEvent.change(customerNameInput, {
      target: { value: "Updated Customer" },
    });

    expect(customerNameInput).toHaveValue("Updated Customer");
  });

  it("saves changes when Save Changes is clicked", async () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    fireEvent.click(screen.getByText("Edit"));
    fireEvent.change(screen.getByDisplayValue("Test Customer"), {
      target: { value: "Updated Customer" },
    });
    fireEvent.click(screen.getByText("Save Changes"));

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalled();
    });
  });

  it("cancels editing when Cancel is clicked", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    fireEvent.click(screen.getByText("Edit"));
    fireEvent.change(screen.getByDisplayValue("Test Customer"), {
      target: { value: "Changed Name" },
    });
    fireEvent.click(screen.getByText("Cancel"));

    expect(screen.getByDisplayValue("Test Customer")).toBeInTheDocument();
  });

  it("closes modal when close button is clicked", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByText("×");
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("updates line item quantity", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    fireEvent.click(screen.getByText("Edit"));

    // Find quantity input in the table
    const quantityInputs = screen.getAllByDisplayValue("2");
    if (quantityInputs.length > 0) {
      fireEvent.change(quantityInputs[0], { target: { value: "5" } });
      expect(quantityInputs[0]).toHaveValue(5);
    }
  });

  it("displays totals correctly", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    // Use getAllByText since line_total might also show $1000.00
    const subtotals = screen.getAllByText("$1000.00");
    expect(subtotals.length).toBeGreaterThan(0);
    expect(screen.getByText("$100.00")).toBeInTheDocument(); // Tax
    expect(screen.getByText("$1100.00")).toBeInTheDocument(); // Total
    // Verify subtotal label exists
    expect(screen.getByText("Subtotal:")).toBeInTheDocument();
  });

  it("displays status dropdown", () => {
    render(
      <OrderDetail
        order={mockOrder}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    fireEvent.click(screen.getByText("Edit"));

    // Status select should be present after clicking Edit
    // Find by label text first, then check value
    const statusLabel = screen.getByText("Status");
    expect(statusLabel).toBeInTheDocument();

    // Find the select element near the label
    const statusSelect = statusLabel.parentElement?.querySelector("select");
    expect(statusSelect).toBeInTheDocument();
    expect(statusSelect).toHaveValue("pending");
  });

  it("displays error message when present", () => {
    const orderWithError = {
      ...mockOrder,
      processing_status: "failed",
      error_message: "Processing failed: Test error message",
    };

    render(
      <OrderDetail
        order={orderWithError}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText(/Processing Error/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Processing failed: Test error message/i)
    ).toBeInTheDocument();
  });

  it("displays processing status when processing", () => {
    const orderProcessing = {
      ...mockOrder,
      processing_status: "processing",
    };

    render(
      <OrderDetail
        order={orderProcessing}
        onUpdate={mockOnUpdate}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText(/Processing Status/i)).toBeInTheDocument();
    expect(screen.getByText("processing")).toBeInTheDocument();
  });
});
