# Order Management System - User Guide

Complete guide on how to use the Order and Return Management System API.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Accessing the API](#accessing-the-api)
3. [Creating Orders](#creating-orders)
4. [Managing Order States](#managing-order-states)
5. [Processing Returns](#processing-returns)
6. [Handling Payments](#handling-payments)
7. [Complete Workflow Examples](#complete-workflow-examples)

---

## Getting Started

### Prerequisites
- Application running on http://localhost:8000
- Web browser or API client (Postman, curl, etc.)

### Access Points
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Accessing the API

### Option 1: Swagger UI (Recommended for Testing)

1. Open http://localhost:8000/docs in your browser
2. You'll see all available endpoints organized by category
3. Click on any endpoint to expand it
4. Click "Try it out" to test the endpoint
5. Fill in the request body (if needed)
6. Click "Execute" to send the request
7. See the response below

### Option 2: Using cURL

```bash
curl -X GET "http://localhost:8000/api/v1/orders" \
  -H "accept: application/json"
```

### Option 3: Using Python Requests

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Get all orders
response = requests.get(f"{base_url}/orders")
print(response.json())
```

---

## Creating Orders

### Step 1: Create a New Order

**Endpoint**: `POST /api/v1/orders`

**Request Body**:
```json
{
  "customer_id": 1,
  "customer_email": "john.doe@example.com",
  "customer_name": "John Doe",
  "items": [
    {
      "product_id": 101,
      "product_name": "Wireless Headphones",
      "product_sku": "WH-001",
      "unit_price": 79.99,
      "quantity": 1
    },
    {
      "product_id": 102,
      "product_name": "USB-C Cable",
      "product_sku": "USB-C-001",
      "unit_price": 12.99,
      "quantity": 2
    }
  ],
  "shipping_address": {
    "street": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "USA"
  },
  "billing_address": {
    "street": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "USA"
  },
  "notes": "Please deliver before 5 PM"
}
```

**Response**:
```json
{
  "id": 1,
  "order_number": "ORD-20240101-ABC12345",
  "customer_id": 1,
  "customer_email": "john.doe@example.com",
  "customer_name": "John Doe",
  "status": "pending",
  "subtotal": 105.97,
  "tax": 10.60,
  "shipping_cost": 5.00,
  "total": 121.57,
  "currency": "USD",
  "items": [...],
  "created_at": "2024-01-01T10:00:00Z"
}
```

**Using Swagger UI**:
1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/orders`
3. Click "Try it out"
4. Paste the JSON above
5. Click "Execute"

**Using cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "customer_email": "john.doe@example.com",
    "customer_name": "John Doe",
    "items": [
      {
        "product_id": 101,
        "product_name": "Wireless Headphones",
        "product_sku": "WH-001",
        "unit_price": 79.99,
        "quantity": 1
      }
    ],
    "shipping_address": {
      "street": "123 Main Street",
      "city": "New York",
      "state": "NY",
      "zip": "10001",
      "country": "USA"
    },
    "billing_address": {
      "street": "123 Main Street",
      "city": "New York",
      "state": "NY",
      "zip": "10001",
      "country": "USA"
    }
  }'
```

### Step 2: Get Order Details

**Endpoint**: `GET /api/v1/orders/{order_id}`

**Example**:
```bash
curl http://localhost:8000/api/v1/orders/1
```

### Step 3: List All Orders

**Endpoint**: `GET /api/v1/orders`

**With Filters**:
```bash
# Get orders for a specific customer
curl "http://localhost:8000/api/v1/orders?customer_id=1"

# Get orders with specific status
curl "http://localhost:8000/api/v1/orders?status=pending"

# Pagination
curl "http://localhost:8000/api/v1/orders?skip=0&limit=10"
```

---

## Managing Order States

Orders go through these states: `pending` → `confirmed` → `processing` → `shipped` → `delivered`

### State Transitions

#### 1. Confirm Order (pending → confirmed)

**Endpoint**: `POST /api/v1/orders/{order_id}/state`

**Request**:
```json
{
  "action": "confirm"
}
```

**cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/orders/1/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "confirm"}'
```

#### 2. Start Processing (confirmed → processing)

```bash
curl -X POST "http://localhost:8000/api/v1/orders/1/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "start_processing"}'
```

#### 3. Ship Order (processing → shipped)

```bash
curl -X POST "http://localhost:8000/api/v1/orders/1/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "ship"}'
```

#### 4. Mark as Delivered (shipped → delivered)

```bash
curl -X POST "http://localhost:8000/api/v1/orders/1/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "deliver"}'
```

#### 5. Cancel Order

**Endpoint**: `POST /api/v1/orders/{order_id}/cancel`

```bash
curl -X POST "http://localhost:8000/api/v1/orders/1/cancel"
```

**Note**: Can only cancel from `pending`, `confirmed`, or `processing` states.

### Available Actions by State

| Current State | Available Actions |
|---------------|-------------------|
| `pending` | `confirm`, `cancel` |
| `confirmed` | `start_processing`, `cancel` |
| `processing` | `ship`, `cancel` |
| `shipped` | `deliver` |
| `delivered` | `return_order` |
| `cancelled` | (no actions) |
| `returned` | (no actions) |

---

## Processing Returns

### Step 1: Initiate Return Request

**Endpoint**: `POST /api/v1/returns`

**Prerequisites**: Order must be in `delivered` or `returned` state

**Request**:
```json
{
  "order_id": 1,
  "reason": "change_of_mind",
  "reason_description": "Changed my mind about the purchase",
  "items": [
    {
      "order_item_id": 1,
      "product_id": 101,
      "product_name": "Wireless Headphones",
      "product_sku": "WH-001",
      "quantity": 1,
      "condition": "new",
      "condition_notes": "Unopened, still in original packaging"
    }
  ],
  "return_address": {
    "street": "456 Return St",
    "city": "New York",
    "state": "NY",
    "zip": "10002",
    "country": "USA"
  },
  "notes": "Please process refund to original payment method"
}
```

**Return Reasons**:
- `defective`
- `wrong_item`
- `not_as_described`
- `damaged`
- `size_issue`
- `change_of_mind`
- `other`

### Step 2: Approve Return

**Endpoint**: `POST /api/v1/returns/{return_id}/approve`

```bash
curl -X POST "http://localhost:8000/api/v1/returns/1/approve"
```

### Step 3: Update Return State

**Endpoint**: `POST /api/v1/returns/{return_id}/state`

**Workflow States**:
1. `initiated` → `approved` (via approve endpoint)
2. `approved` → `pickup_scheduled` (action: `schedule_pickup`)
3. `pickup_scheduled` → `in_transit` (action: `start_transit`)
4. `in_transit` → `received` (action: `receive`)
5. `received` → `processed` (action: `process`)
6. `processed` → `refunded` (action: `refund`)

**Example - Schedule Pickup**:
```bash
curl -X POST "http://localhost:8000/api/v1/returns/1/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "schedule_pickup"}'
```

**Example - Mark as Received**:
```bash
curl -X POST "http://localhost:8000/api/v1/returns/1/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "receive"}'
```

**Example - Process Refund**:
```bash
curl -X POST "http://localhost:8000/api/v1/returns/1/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "refund"}'
```

### Step 4: Reject Return (if needed)

**Endpoint**: `POST /api/v1/returns/{return_id}/reject`

```bash
curl -X POST "http://localhost:8000/api/v1/returns/1/reject?reason=Return%20request%20does%20not%20meet%20policy"
```

---

## Handling Payments

### Step 1: Create Payment

**Endpoint**: `POST /api/v1/payments`

**Request**:
```json
{
  "order_id": 1,
  "method": "credit_card",
  "amount": 121.57,
  "currency": "USD",
  "transaction_id": "TXN-123456789"
}
```

**Payment Methods**:
- `credit_card`
- `debit_card`
- `paypal`
- `bank_transfer`
- `stripe`
- `other`

### Step 2: Process Payment

**Endpoint**: `POST /api/v1/payments/{payment_id}/process`

```bash
curl -X POST "http://localhost:8000/api/v1/payments/1/process"
```

### Step 3: Process Refund

**Endpoint**: `POST /api/v1/payments/{payment_id}/refund`

**Full Refund**:
```json
{
  "reason": "Customer requested refund"
}
```

**Partial Refund**:
```json
{
  "amount": 50.00,
  "reason": "Partial refund for damaged item"
}
```

---

## Complete Workflow Examples

### Example 1: Complete Order Lifecycle

```bash
# 1. Create Order
ORDER_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "customer_email": "customer@example.com",
    "customer_name": "John Doe",
    "items": [{
      "product_id": 101,
      "product_name": "Product 1",
      "product_sku": "SKU-001",
      "unit_price": 29.99,
      "quantity": 1
    }],
    "shipping_address": {"street": "123 Main St", "city": "NY", "state": "NY", "zip": "10001", "country": "USA"},
    "billing_address": {"street": "123 Main St", "city": "NY", "state": "NY", "zip": "10001", "country": "USA"}
  }')

ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.id')

# 2. Create Payment
PAYMENT_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": $ORDER_ID,
    \"method\": \"credit_card\",
    \"amount\": 37.99,
    \"currency\": \"USD\"
  }")

PAYMENT_ID=$(echo $PAYMENT_RESPONSE | jq -r '.id')

# 3. Process Payment
curl -X POST "http://localhost:8000/api/v1/payments/$PAYMENT_ID/process"

# 4. Confirm Order
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "confirm"}'

# 5. Start Processing
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "start_processing"}'

# 6. Ship Order
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "ship"}'

# 7. Mark as Delivered
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "deliver"}'
```

### Example 2: Return Workflow

```bash
# 1. Create Return (order must be delivered)
RETURN_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/returns" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": $ORDER_ID,
    \"reason\": \"change_of_mind\",
    \"items\": [{
      \"order_item_id\": 1,
      \"product_id\": 101,
      \"product_name\": \"Product 1\",
      \"product_sku\": \"SKU-001\",
      \"quantity\": 1
    }]
  }")

RETURN_ID=$(echo $RETURN_RESPONSE | jq -r '.id')

# 2. Approve Return
curl -X POST "http://localhost:8000/api/v1/returns/$RETURN_ID/approve"

# 3. Schedule Pickup
curl -X POST "http://localhost:8000/api/v1/returns/$RETURN_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "schedule_pickup"}'

# 4. Start Transit
curl -X POST "http://localhost:8000/api/v1/returns/$RETURN_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "start_transit"}'

# 5. Mark as Received
curl -X POST "http://localhost:8000/api/v1/returns/$RETURN_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "receive"}'

# 6. Process Return
curl -X POST "http://localhost:8000/api/v1/returns/$RETURN_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "process"}'

# 7. Process Refund
curl -X POST "http://localhost:8000/api/v1/returns/$RETURN_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"action": "refund"}'
```

---

## Python Example Script

Create a file `test_api.py`:

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create an order
order_data = {
    "customer_id": 1,
    "customer_email": "customer@example.com",
    "customer_name": "John Doe",
    "items": [
        {
            "product_id": 101,
            "product_name": "Product 1",
            "product_sku": "SKU-001",
            "unit_price": 29.99,
            "quantity": 2
        }
    ],
    "shipping_address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "country": "USA"
    },
    "billing_address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "country": "USA"
    }
}

# Create order
response = requests.post(f"{BASE_URL}/orders", json=order_data)
order = response.json()
print(f"Created order: {order['order_number']}")
order_id = order['id']

# Confirm order
requests.post(
    f"{BASE_URL}/orders/{order_id}/state",
    json={"action": "confirm"}
)
print("Order confirmed")

# Get order details
response = requests.get(f"{BASE_URL}/orders/{order_id}")
print(f"Order status: {response.json()['status']}")
```

Run it:
```bash
python test_api.py
```

---

## Tips and Best Practices

1. **Always check order status** before performing state transitions
2. **Validate email addresses** - must be valid email format
3. **Ensure items array is not empty** when creating orders
4. **Order must be delivered** before creating a return
5. **Payment must be completed** before processing refunds
6. **Use Swagger UI** for interactive testing and exploration
7. **Check error messages** - they tell you exactly what's wrong

---

## Error Handling

### Common Error Codes

- **400 Bad Request**: Invalid data or business logic error
- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Validation error (check request format)
- **500 Internal Server Error**: Server error (check logs)

### Getting Help

1. Check the error response `detail` field for specific issues
2. Use Swagger UI to see expected request format
3. Review `TROUBLESHOOTING.md` for common issues
4. Check server logs for detailed error information

---

## Next Steps

- Explore all endpoints in Swagger UI: http://localhost:8000/docs
- Try creating a complete order workflow
- Test the return process
- Experiment with different state transitions

Happy coding! 🚀

