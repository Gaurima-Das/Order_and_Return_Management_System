# Complete Return Workflow Guide

## Full Return State Flow

```
initiated → approve → approved → schedule_pickup → pickup_scheduled → start_transit → in_transit → receive → received → process → processed → refund → refunded
                                                                                                                                    ↑
                                                                                                                          Credit memo generated here
```

## Step-by-Step API Calls

### 1. Create Return
```bash
POST /api/v1/returns
{
  "order_id": 1,
  "reason": "DEFECTIVE",
  "items": [...]
}
```
**State:** `initiated`

### 2. Approve Return
```bash
POST /api/v1/returns/{return_id}/state
{
  "action": "approve"
}
```
**State:** `approved`

### 3. Schedule Pickup
```bash
POST /api/v1/returns/{return_id}/state
{
  "action": "schedule_pickup"
}
```
**State:** `pickup_scheduled`

### 4. Start Transit
```bash
POST /api/v1/returns/{return_id}/state
{
  "action": "start_transit"
}
```
**State:** `in_transit`

### 5. Receive Return
```bash
POST /api/v1/returns/{return_id}/state
{
  "action": "receive"
}
```
**State:** `received`

### 6. Process Return (Credit Memo Generated Here)
```bash
POST /api/v1/returns/{return_id}/state
{
  "action": "process"
}
```
**State:** `processed` → **Credit memo PDF generated automatically**

### 7. Refund Return
```bash
POST /api/v1/returns/{return_id}/state
{
  "action": "refund"
}
```
**State:** `refunded`

## Important Notes

1. **Credit memo is generated at "processed" state** - This happens automatically when you use action `"process"` from `"received"` state.

2. **All steps must be followed in order** - You cannot skip states. For example:
   - Cannot go from `approved` directly to `received`
   - Must go: `approved` → `pickup_scheduled` → `in_transit` → `received` → `processed`

3. **Action names are case-insensitive** - The API normalizes action names, so `"process"`, `"Process"`, or `"PROCESS"` all work.

## Troubleshooting Credit Memo Generation

### If credit memo is not generated:

1. **Check Celery worker is running**
   - Look for: `celery@hostname ready.`
   - Must be running when you process the return

2. **Verify return is in correct state**
   ```bash
   GET /api/v1/returns/{return_id}
   ```
   - Must be in `received` state before using `process` action
   - After processing, should be in `processed` state

3. **Check Celery terminal logs**
   - Look for: `Task generate_return_invoice[...] received`
   - Look for: `=== Starting credit memo generation for return X ===`
   - Check for any ERROR messages

4. **Verify workflow was followed**
   - Ensure you went through all intermediate states:
     - `approved` → `schedule_pickup` → `start_transit` → `receive` → `process`

5. **Check invoices folder**
   ```bash
   # Files should be named:
   credit_memo_return_RET-YYYYMMDD-XXXXXX_TIMESTAMP.pdf
   ```

## Quick Test

To test credit memo generation directly (without going through full workflow):

```bash
python generate_credit_memos_for_refunded.py
```

This will generate credit memos for any returns in `processed` or `refunded` state.

## API Endpoint

The main endpoint for state transitions is:

```
POST /api/v1/returns/{return_id}/state
Content-Type: application/json

{
  "action": "process"  // or "approve", "schedule_pickup", "start_transit", "receive", "refund"
}
```

## Alternative: Direct Approve Endpoint

You can also use the convenience endpoint:

```
POST /api/v1/returns/{return_id}/approve
```

This is equivalent to:
```
POST /api/v1/returns/{return_id}/state
{
  "action": "approve"
}
```

