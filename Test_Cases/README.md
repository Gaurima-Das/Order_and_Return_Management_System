# Test Cases and Coverage Report

This directory contains comprehensive unit tests and coverage reports for the Order and Return Management System.

## Test Structure

```
Test_Cases/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── pytest.ini               # Pytest configuration
├── .coveragerc              # Coverage configuration
├── test_order_service.py    # Order service tests
├── test_return_service.py   # Return service tests
├── test_payment_service.py  # Payment service tests
├── test_invoice_service.py  # Invoice service tests
├── test_order_api.py        # Order API endpoint tests
├── test_return_api.py       # Return API endpoint tests
├── test_payment_api.py      # Payment API endpoint tests
├── test_invoice_api.py      # Invoice API endpoint tests
├── test_state_machines.py   # State machine tests
├── coverage_html/           # HTML coverage report (generated)
└── coverage.xml             # XML coverage report (generated)
```

## Running Tests

### Run All Tests
```bash
pytest Test_Cases/
```

### Run with Coverage
```bash
pytest Test_Cases/ --cov=app --cov-report=html --cov-report=term
```

### Run Specific Test File
```bash
pytest Test_Cases/test_order_service.py
```

### Run Specific Test
```bash
pytest Test_Cases/test_order_service.py::test_create_order
```

### Run with Verbose Output
```bash
pytest Test_Cases/ -v
```

## Coverage Reports

### HTML Report
After running tests with coverage, open:
```
Test_Cases/coverage_html/index.html
```

### Terminal Report
Coverage summary is displayed in the terminal after running tests.

### XML Report
XML coverage report is generated at:
```
Test_Cases/coverage.xml
```

## Test Coverage

The tests cover:

### Services (Business Logic)
- ✅ Order Service
  - Order creation
  - Order retrieval
  - Order listing with filters
  - Order updates
  - State transitions
  - Invalid transitions

- ✅ Return Service
  - Return creation
  - Return retrieval
  - Return listing with filters
  - Return updates
  - State transitions
  - Full workflow testing

- ✅ Payment Service
  - Payment creation
  - Payment processing
  - Full and partial refunds
  - Payment status management

- ✅ Invoice Service
  - Order invoice PDF generation
  - Return credit memo PDF generation
  - File system operations

### API Endpoints
- ✅ Order endpoints
  - POST /api/v1/orders
  - GET /api/v1/orders
  - GET /api/v1/orders/{id}
  - PATCH /api/v1/orders/{id}
  - POST /api/v1/orders/{id}/state
  - POST /api/v1/orders/{id}/cancel

- ✅ Return endpoints
  - POST /api/v1/returns
  - GET /api/v1/returns
  - GET /api/v1/returns/{id}
  - PATCH /api/v1/returns/{id}
  - POST /api/v1/returns/{id}/state
  - POST /api/v1/returns/{id}/approve
  - POST /api/v1/returns/{id}/reject

- ✅ Payment endpoints
  - POST /api/v1/payments
  - GET /api/v1/payments
  - GET /api/v1/payments/{id}
  - PATCH /api/v1/payments/{id}
  - POST /api/v1/payments/{id}/process
  - POST /api/v1/payments/{id}/refund

- ✅ Invoice endpoints
  - GET /api/v1/invoices/order/{order_id}
  - GET /api/v1/invoices/return/{return_id}
  - GET /api/v1/invoices/{invoice_id}
  - GET /api/v1/invoices/{invoice_id}/download

### State Machines
- ✅ Order State Machine
  - Valid transitions
  - Invalid transitions
  - Available transitions

- ✅ Return State Machine
  - Valid transitions
  - Invalid transitions
  - Full workflow

## Test Fixtures

The `conftest.py` file provides reusable fixtures:

- `db_session`: Synchronous database session
- `async_db_session`: Asynchronous database session
- `client`: FastAPI test client
- `sample_order_data`: Sample order data
- `sample_order`: Sample order in database
- `sample_return_data`: Sample return data
- `sample_return`: Sample return in database
- `sample_payment`: Sample payment in database
- `sample_invoice`: Sample invoice in database

## Coverage Goals

- **Minimum Coverage**: 70%
- **Target Coverage**: 80%+
- **Critical Paths**: 90%+

## Running Tests in CI/CD

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    pytest Test_Cases/ --cov=app --cov-report=xml --cov-report=term

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./Test_Cases/coverage.xml
```

## Notes

- Tests use in-memory SQLite database for fast execution
- Each test is isolated with its own database session
- PDF files generated during tests are cleaned up automatically
- Async tests use `pytest-asyncio` for proper async support

## Troubleshooting

### Import Errors
Make sure you're running tests from the project root:
```bash
cd /path/to/order_management_app
pytest Test_Cases/
```

### Database Errors
Tests use in-memory SQLite, so no database setup is needed. If you see database errors, check that SQLAlchemy models are properly imported.

### Async Test Errors
Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

### Coverage Not Showing
Make sure `pytest-cov` is installed:
```bash
pip install pytest-cov
```

