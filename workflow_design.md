# Order and Return Management System - Workflow Design

## Table of Contents
1. [System Overview](#system-overview)
2. [Order Workflow](#order-workflow)
3. [Return Workflow](#return-workflow)
4. [Payment Workflow](#payment-workflow)
5. [Invoice Generation](#invoice-generation)
6. [Database Schema](#database-schema)
7. [State Machine Diagrams](#state-machine-diagrams)
8. [Implementation Details](#implementation-details)

---

## System Overview

This system manages the complete lifecycle of orders, returns, and payments with automated invoice generation. It uses state machines to control valid transitions and ensures data integrity throughout the process.

### Key Components

- **FastAPI**: REST API for order, return, and payment management
- **SQLAlchemy**: Database ORM for data persistence
- **State Machines**: Control valid state transitions
- **Celery**: Background job processing for invoice generation
- **ReportLab**: PDF generation for invoices and credit memos

---

## Order Workflow

### Order State Machine

```
┌─────────┐
│ PENDING │  (Initial state when order is created)
└────┬────┘
     │ confirm
     ▼
┌──────────┐
│CONFIRMED │  (Order confirmed, payment processed)
└────┬─────┘
     │ start_processing
     ▼
┌────────────┐
│ PROCESSING │  (Order being prepared for shipment)
└────┬───────┘
     │ ship
     ▼
┌─────────┐
│ SHIPPED │  ⭐ Invoice PDF generated automatically
└────┬────┘
     │ deliver
     ▼
┌──────────┐
│DELIVERED │  (Order delivered to customer)
└────┬─────┘
     │ return_order
     ▼
┌──────────┐
│ RETURNED │  (Order returned by customer)
└──────────┘

     ┌─────────┐
     │CANCELLED│  (Can cancel from PENDING or PROCESSING)
     └─────────┘
```

### Order Lifecycle

1. **PENDING**: Order created, awaiting confirmation
2. **CONFIRMED**: Order confirmed, payment processed
3. **PROCESSING**: Order being prepared for shipment
4. **SHIPPED**: Order shipped → **Invoice PDF automatically generated**
5. **DELIVERED**: Order delivered to customer
6. **RETURNED**: Order returned by customer
7. **CANCELLED**: Order cancelled (can happen from PENDING or PROCESSING)

### Order State Transitions

| From State | Action | To State | Notes |
|------------|--------|----------|-------|
| PENDING | `confirm` | CONFIRMED | Payment must be processed |
| CONFIRMED | `start_processing` | PROCESSING | Begin order fulfillment |
| PROCESSING | `ship` | SHIPPED | **Invoice generated** |
| PROCESSING | `cancel` | CANCELLED | Can cancel during processing |
| SHIPPED | `deliver` | DELIVERED | Order delivered |
| DELIVERED | `return_order` | RETURNED | Customer returns order |
| PENDING | `cancel` | CANCELLED | Can cancel before confirmation |

---

## Return Workflow

### Return State Machine

```
┌──────────┐
│INITIATED │  (Return request created)
└────┬─────┘
     │ approve
     ▼
┌──────────┐
│ APPROVED │  (Return approved by admin)
└────┬─────┘
     │ schedule_pickup
     ▼
┌─────────────────┐
│ PICKUP_SCHEDULED │  (Pickup scheduled)
└────┬────────────┘
     │ start_transit
     ▼
┌───────────┐
│ IN_TRANSIT │  (Return item in transit)
└────┬──────┘
     │ receive
     ▼
┌──────────┐
│ RECEIVED │  (Return received at warehouse)
└────┬─────┘
     │ process
     ▼
┌───────────┐
│ PROCESSED │  ⭐ Credit Memo PDF generated automatically
└────┬──────┘
     │ refund
     ▼
┌──────────┐
│ REFUNDED │  (Refund processed)
└──────────┘

     ┌──────────┐
     │ REJECTED │  (Can reject from INITIATED or APPROVED)
     └──────────┘
     
     ┌──────────┐
     │CANCELLED │  (Can cancel from INITIATED or APPROVED)
     └──────────┘
```

### Return Lifecycle

1. **INITIATED**: Return request created by customer
2. **APPROVED**: Return approved by admin
3. **PICKUP_SCHEDULED**: Pickup scheduled for return items
4. **IN_TRANSIT**: Return items in transit to warehouse
5. **RECEIVED**: Return items received at warehouse
6. **PROCESSED**: Return processed and verified → **Credit Memo PDF automatically generated**
7. **REFUNDED**: Refund processed and completed
8. **REJECTED**: Return rejected (can happen from INITIATED or APPROVED)
9. **CANCELLED**: Return cancelled (can happen from INITIATED or APPROVED)

### Return State Transitions

| From State | Action | To State | Notes |
|------------|--------|----------|-------|
| INITIATED | `approve` | APPROVED | Admin approves return |
| INITIATED | `reject` | REJECTED | Admin rejects return |
| INITIATED | `cancel` | CANCELLED | Customer cancels return |
| APPROVED | `schedule_pickup` | PICKUP_SCHEDULED | Schedule pickup |
| APPROVED | `reject` | REJECTED | Can still reject |
| APPROVED | `cancel` | CANCELLED | Can still cancel |
| PICKUP_SCHEDULED | `start_transit` | IN_TRANSIT | Items picked up |
| IN_TRANSIT | `receive` | RECEIVED | Items arrive at warehouse |
| RECEIVED | `process` | PROCESSED | **Credit memo generated** |
| PROCESSED | `refund` | REFUNDED | Refund processed |

---

## Payment Workflow

### Payment States

```
┌─────────┐
│ PENDING │  (Payment initiated)
└────┬────┘
     │ process
     ▼
┌────────────┐
│ PROCESSING │  (Payment being processed)
└────┬───────┘
     │
     ├─► ┌──────────┐
     │   │ COMPLETED │  (Payment successful)
     │   └───────────┘
     │
     └─► ┌────────┐
         │ FAILED │  (Payment failed)
         └────────┘

┌──────────┐
│ REFUNDED │  (Full refund processed)
└──────────┘

┌──────────────────┐
│ PARTIALLY_REFUNDED│  (Partial refund processed)
└───────────────────┘

┌──────────┐
│CANCELLED │  (Payment cancelled)
└──────────┘
```

### Payment State Transitions

| From State | Action | To State | Notes |
|------------|--------|----------|-------|
| PENDING | `process` | PROCESSING | Payment processing starts |
| PROCESSING | (success) | COMPLETED | Payment successful |
| PROCESSING | (failure) | FAILED | Payment failed |
| COMPLETED | `refund` | REFUNDED | Full refund |
| COMPLETED | `partial_refund` | PARTIALLY_REFUNDED | Partial refund |
| PENDING | `cancel` | CANCELLED | Payment cancelled |

---

## Invoice Generation

### Automatic Invoice Generation

The system automatically generates PDF invoices in two scenarios:

#### 1. Order Invoice Generation

**Trigger**: When order state transitions to `SHIPPED`

**Process**:
```
Order State: PROCESSING
     │
     │ Action: "ship"
     ▼
Order State: SHIPPED
     │
     │ Celery Task Queued
     ▼
generate_order_invoice.delay(order_id)
     │
     │ Background Processing
     ▼
PDF Generated: invoices/invoice_order_ORD-XXX_TIMESTAMP.pdf
     │
     │ Database Record Created
     ▼
Invoice record saved in invoices table
```

**Invoice Contains**:
- Invoice number and dates
- Customer billing and shipping information
- Detailed order items (Product, SKU, Quantity, Price)
- Subtotal, Tax, Shipping, Total amounts

#### 2. Return Credit Memo Generation

**Trigger**: When return state transitions to `PROCESSED`

**Process**:
```
Return State: RECEIVED
     │
     │ Action: "process"
     ▼
Return State: PROCESSED
     │
     │ Celery Task Queued
     ▼
generate_return_invoice.delay(return_id)
     │
     │ Background Processing
     ▼
PDF Generated: invoices/credit_memo_return_RET-XXX_TIMESTAMP.pdf
     │
     │ Database Record Created
     ▼
Invoice record saved in invoices table
```

**Credit Memo Contains**:
- Credit memo number and dates
- Original order reference
- Return reason
- Returned items with refund amounts
- Total refund amount

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐
│    Order    │
│─────────────│
│ id (PK)     │
│ order_number│
│ customer_id │
│ status      │
│ total       │
│ ...         │
└──────┬──────┘
       │
       │ 1:N
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ OrderItem   │   │  Payment   │
│─────────────│   │─────────────│
│ id (PK)     │   │ id (PK)     │
│ order_id(FK)│   │ order_id(FK)│
│ product_name│   │ amount      │
│ quantity    │   │ status      │
│ unit_price  │   │ ...         │
└─────────────┘   └─────────────┘
       │
       │
       │ 1:N
       │
       ▼
┌─────────────┐
│   Return    │
│─────────────│
│ id (PK)     │
│ return_number│
│ order_id(FK)│
│ status      │
│ refund_amount│
│ ...         │
└──────┬──────┘
       │
       │ 1:N
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ ReturnItem  │   │  Invoice    │
│─────────────│   │─────────────│
│ id (PK)     │   │ id (PK)     │
│ return_id(FK)│  │ invoice_number│
│ product_name│   │ invoice_type│
│ quantity    │   │ order_id(FK) │
│ refund_amount│  │ return_id(FK)│
└─────────────┘   │ file_path   │
                  │ ...         │
                  └─────────────┘
```

### Tables Overview

#### 1. Orders Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `order_number` | String(50) | Unique order identifier (e.g., ORD-20260104-XXXX) |
| `customer_id` | Integer | Customer identifier |
| `customer_email` | String(255) | Customer email |
| `customer_name` | String(255) | Customer name |
| `status` | Enum | Current order status (PENDING, CONFIRMED, etc.) |
| `previous_status` | Enum | Previous status (for state tracking) |
| `subtotal` | Decimal | Order subtotal |
| `tax` | Decimal | Tax amount |
| `shipping_cost` | Decimal | Shipping cost |
| `total` | Decimal | Total amount |
| `currency` | String(10) | Currency code (USD, EUR, etc.) |
| `shipping_address` | JSON/Text | Shipping address details |
| `billing_address` | JSON/Text | Billing address details |
| `notes` | Text | Order notes |
| `meta_data` | JSON/Text | Additional metadata |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `confirmed_at` | DateTime | Confirmation timestamp |
| `shipped_at` | DateTime | Shipment timestamp |
| `delivered_at` | DateTime | Delivery timestamp |
| `cancelled_at` | DateTime | Cancellation timestamp |

#### 2. Order Items Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `order_id` | Integer (FK) | Reference to orders table |
| `product_id` | Integer | Product identifier |
| `product_name` | String(255) | Product name |
| `product_sku` | String(100) | Product SKU |
| `quantity` | Integer | Item quantity |
| `unit_price` | Decimal | Price per unit |
| `total_price` | Decimal | Total price (quantity × unit_price) |
| `meta_data` | JSON/Text | Additional metadata |
| `created_at` | DateTime | Creation timestamp |

#### 3. Returns Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `return_number` | String(50) | Unique return identifier (e.g., RET-20260104-XXXX) |
| `order_id` | Integer (FK) | Reference to original order |
| `status` | Enum | Current return status |
| `previous_status` | Enum | Previous status |
| `reason` | Enum | Return reason (DEFECTIVE, WRONG_ITEM, etc.) |
| `reason_description` | Text | Detailed reason description |
| `refund_amount` | Decimal | Total refund amount |
| `refund_method` | String(50) | Refund method |
| `currency` | String(10) | Currency code |
| `return_address` | JSON/Text | Return shipping address |
| `tracking_number` | String(100) | Return tracking number |
| `notes` | Text | Return notes |
| `rejection_reason` | Text | Rejection reason (if rejected) |
| `meta_data` | JSON/Text | Additional metadata |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `approved_at` | DateTime | Approval timestamp |
| `pickup_scheduled_at` | DateTime | Pickup scheduling timestamp |
| `received_at` | DateTime | Receipt timestamp |
| `processed_at` | DateTime | Processing timestamp |
| `refunded_at` | DateTime | Refund timestamp |

#### 4. Return Items Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `return_id` | Integer (FK) | Reference to returns table |
| `order_item_id` | Integer (FK) | Reference to original order item |
| `product_id` | Integer | Product identifier |
| `product_name` | String(255) | Product name |
| `product_sku` | String(100) | Product SKU |
| `quantity` | Integer | Returned quantity |
| `refund_amount` | Decimal | Refund amount for this item |
| `condition` | String(50) | Item condition (NEW, USED, DAMAGED, etc.) |
| `condition_notes` | Text | Condition description |
| `created_at` | DateTime | Creation timestamp |

#### 5. Payments Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `payment_number` | String(50) | Unique payment identifier |
| `order_id` | Integer (FK) | Reference to order |
| `status` | Enum | Payment status (PENDING, PROCESSING, COMPLETED, etc.) |
| `method` | Enum | Payment method (CREDIT_CARD, DEBIT_CARD, etc.) |
| `amount` | Decimal | Payment amount |
| `currency` | String(10) | Currency code |
| `transaction_id` | String(255) | External transaction ID |
| `gateway_response` | JSON/Text | Payment gateway response |
| `refund_amount` | Decimal | Refunded amount (if any) |
| `meta_data` | JSON/Text | Additional metadata |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `processed_at` | DateTime | Processing timestamp |
| `refunded_at` | DateTime | Refund timestamp |

#### 6. Invoices Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `invoice_number` | String(100) | Unique invoice identifier |
| `invoice_type` | Enum | Type (ORDER or RETURN) |
| `order_id` | Integer (FK, nullable) | Reference to order (if order invoice) |
| `return_id` | Integer (FK, nullable) | Reference to return (if credit memo) |
| `file_path` | String(500) | Path to PDF file |
| `file_name` | String(255) | PDF filename |
| `file_size` | Integer | File size in bytes |
| `notes` | Text | Additional notes |
| `created_at` | DateTime | Creation timestamp |

### Relationships

- **Order → OrderItems**: One-to-Many (one order has many items)
- **Order → Payments**: One-to-Many (one order can have multiple payments)
- **Order → Returns**: One-to-Many (one order can have multiple returns)
- **Order → Invoices**: One-to-Many (one order can have multiple invoices)
- **Return → ReturnItems**: One-to-Many (one return has many items)
- **Return → Invoices**: One-to-Many (one return can have multiple credit memos)
- **OrderItem → ReturnItem**: One-to-Many (one order item can be returned multiple times)

---

## State Machine Diagrams

### Complete Order State Machine

```
                    ┌─────────┐
                    │ PENDING │◄──────────────────┐
                    └────┬────┘                   │
                         │                        │
                    confirm│                       │
                         │                        │
                         ▼                        │
                    ┌──────────┐                  │
                    │CONFIRMED │                  │
                    └────┬─────┘                  │
                         │                        │
                start_processing│                 │
                         │                        │
                         ▼                        │
                    ┌────────────┐                │
                    │ PROCESSING │                │
                    └────┬───────┘                │
                         │                        │
                    ┌────┴────┐                  │
                    │         │                  │
                   ship│       │cancel            │
                    │         │                  │
                    ▼         ▼                  │
              ┌─────────┐ ┌──────────┐           │
              │ SHIPPED │ │CANCELLED │           │
              └────┬────┘ └──────────┘           │
                   │                             │
              deliver│                            │
                   │                             │
                   ▼                             │
              ┌──────────┐                       │
              │DELIVERED │                       │
              └────┬─────┘                       │
                   │                             │
            return_order│                        │
                   │                             │
                   ▼                             │
              ┌──────────┐                       │
              │ RETURNED │                       │
              └──────────┘                       │
                                                 │
                    ⭐ Invoice PDF               │
                    Generated when               │
                    state = SHIPPED              │
                    ─────────────────────────────┘
```

### Complete Return State Machine

```
                    ┌──────────┐
                    │INITIATED │
                    └────┬─────┘
                         │
                    ┌────┴────┐
                    │         │
              approve│         │reject/cancel
                    │         │
                    ▼         ▼
              ┌──────────┐ ┌──────────┐
              │ APPROVED │ │ REJECTED │
              └────┬─────┘ └──────────┘
                   │
                   │
            ┌──────┴──────┐
            │             │
    schedule_pickup│       │reject/cancel
            │             │
            ▼             ▼
    ┌─────────────────┐ ┌──────────┐
    │ PICKUP_SCHEDULED │ │ REJECTED │
    └────┬────────────┘ └──────────┘
         │
    start_transit│
         │
         ▼
    ┌───────────┐
    │ IN_TRANSIT │
    └────┬──────┘
         │
    receive│
         │
         ▼
    ┌──────────┐
    │ RECEIVED │
    └────┬─────┘
         │
    process│
         │
         ▼
    ┌───────────┐
    │ PROCESSED │
    └────┬──────┘
         │
    refund│
         │
         ▼
    ┌──────────┐
    │ REFUNDED │
    └──────────┘

    ⭐ Credit Memo PDF
    Generated when
    state = PROCESSED
```

---

## Implementation Details

### How State Machines Work

State machines ensure that only valid state transitions are allowed. For example:
- You cannot ship an order that is still PENDING
- You cannot process a return that hasn't been RECEIVED
- You cannot refund a return that hasn't been PROCESSED

**Implementation**:
```python
# State machine validates transitions
if not state_machine.can_transition(action):
    raise ValueError(f"Cannot perform action '{action}' from current state")

# If valid, transition is executed
getattr(state_machine, action)()
```

### How Invoice Generation Works

#### 1. Order Invoice Flow

```
User Action: Ship Order
     │
     ▼
API: PATCH /api/v1/orders/{id}/state {"action": "ship"}
     │
     ▼
OrderService.transition_order_state()
     │
     ├─► State Machine: order.ship()
     │   └─► Order status = SHIPPED
     │
     └─► if action == "ship":
         └─► generate_order_invoice.delay(order.id)
             │
             ▼
         Celery Worker receives task
             │
             ▼
         InvoiceService.generate_order_invoice(order)
             │
             ├─► Load order with items from database
             ├─► Generate PDF using ReportLab
             ├─► Save PDF to invoices/ folder
             └─► Create invoice record in database
```

#### 2. Return Credit Memo Flow

```
User Action: Process Return
     │
     ▼
API: POST /api/v1/returns/{id}/state {"action": "process"}
     │
     ▼
ReturnService.transition_return_state()
     │
     ├─► State Machine: return.process()
     │   └─► Return status = PROCESSED
     │
     └─► if action == "process":
         └─► generate_return_invoice.delay(return_id)
             │
             ▼
         Celery Worker receives task
             │
             ▼
         InvoiceService.generate_return_invoice(return_obj)
             │
             ├─► Load return with items and order from database
             ├─► Generate PDF using ReportLab
             ├─► Save PDF to invoices/ folder
             └─► Create invoice record in database
```

### Background Job Processing

**Technology**: Celery with filesystem broker (for Windows compatibility)

**Why Background Jobs?**
- PDF generation can take time
- Don't want to block API response
- Can retry if generation fails
- Better user experience

**How It Works**:
1. API endpoint queues task: `task.delay(params)`
2. Celery worker picks up task from queue
3. Worker executes task asynchronously
4. Task generates PDF and saves to database
5. User can query invoice via API

### Error Handling

**State Transition Errors**:
- Invalid transition → Returns 400 Bad Request with error message
- Already in target state → Returns 400 Bad Request
- Missing required data → Returns 400 Bad Request

**Invoice Generation Errors**:
- Celery not running → Logs warning, order/return still transitions
- PDF generation fails → Logs error, can retry manually
- File permission issues → Logs error, returns error response

### Data Flow Example

**Complete Order Lifecycle**:

```
1. Create Order
   POST /api/v1/orders
   → Order created (status: PENDING)
   → OrderItems created

2. Process Payment
   POST /api/v1/payments
   → Payment created (status: PENDING)
   → Payment processed (status: COMPLETED)

3. Confirm Order
   PATCH /api/v1/orders/{id}/state {"action": "confirm"}
   → Order status: CONFIRMED

4. Start Processing
   PATCH /api/v1/orders/{id}/state {"action": "start_processing"}
   → Order status: PROCESSING

5. Ship Order
   PATCH /api/v1/orders/{id}/state {"action": "ship"}
   → Order status: SHIPPED
   → Invoice PDF generated (background)
   → Invoice record created

6. Deliver Order
   PATCH /api/v1/orders/{id}/state {"action": "deliver"}
   → Order status: DELIVERED
```

**Complete Return Lifecycle**:

```
1. Create Return
   POST /api/v1/returns
   → Return created (status: INITIATED)
   → ReturnItems created

2. Approve Return
   POST /api/v1/returns/{id}/state {"action": "approve"}
   → Return status: APPROVED

3. Schedule Pickup
   POST /api/v1/returns/{id}/state {"action": "schedule_pickup"}
   → Return status: PICKUP_SCHEDULED

4. Start Transit
   POST /api/v1/returns/{id}/state {"action": "start_transit"}
   → Return status: IN_TRANSIT

5. Receive Return
   POST /api/v1/returns/{id}/state {"action": "receive"}
   → Return status: RECEIVED

6. Process Return
   POST /api/v1/returns/{id}/state {"action": "process"}
   → Return status: PROCESSED
   → Credit Memo PDF generated (background)
   → Invoice record created

7. Refund Return
   POST /api/v1/returns/{id}/state {"action": "refund"}
   → Return status: REFUNDED
```

---

## Key Design Decisions

### 1. State Machines
- **Why**: Ensures data integrity and prevents invalid transitions
- **Benefit**: Clear workflow, easy to understand and maintain

### 2. Asynchronous Invoice Generation
- **Why**: PDF generation can be slow, shouldn't block API
- **Benefit**: Fast API responses, better user experience

### 3. Separate Invoice Table
- **Why**: Track all generated invoices, link to orders/returns
- **Benefit**: Can query invoice history, regenerate if needed

### 4. JSON Fields for Addresses
- **Why**: Flexible address structure, different countries have different formats
- **Benefit**: Easy to extend, no schema changes needed

### 5. Enum Types for Status
- **Why**: Type safety, prevents invalid status values
- **Benefit**: Database-level validation, clear status values

---

## Summary

This system provides:
- ✅ Complete order lifecycle management
- ✅ Complete return lifecycle management
- ✅ Payment processing integration
- ✅ Automatic invoice generation
- ✅ State machine-based workflow control
- ✅ Background job processing
- ✅ RESTful API for all operations
- ✅ Comprehensive database schema
- ✅ Error handling and validation

The design ensures data integrity, provides clear workflows, and automates invoice generation while maintaining flexibility for future enhancements.

