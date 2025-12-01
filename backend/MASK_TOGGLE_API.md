# Mask Logic Toggle API Documentation

## Overview

These endpoints allow administrators to view and toggle the mask detection logic inversion setting. This is useful when the mask detection model's output needs to be inverted (e.g., if the model was trained with opposite labels).

---

## Endpoints

### 1. Get Mask Logic State

**Endpoint:** `GET /admin/mask-logic`

**Authentication:** Required (Admin only)

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "inverted": true,
  "description": "If true: mask_pred < 0.5 = MASK, mask_pred >= 0.5 = NO MASK"
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (non-admin user)

**Example:**
```bash
curl -X GET http://localhost:5000/admin/mask-logic \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 2. Toggle Mask Logic

**Endpoint:** `POST /admin/mask-logic/toggle`

**Authentication:** Required (Admin only)

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "inverted": false,
  "message": "Mask logic normal"
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (non-admin user)

**Example:**
```bash
curl -X POST http://localhost:5000/admin/mask-logic/toggle \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## How It Works

### Mask Detection Logic

The mask detection model outputs a value between 0 and 1:

**When `inverted = true` (default):**
- `mask_pred < 0.5` → **MASK detected**
- `mask_pred >= 0.5` → **NO MASK detected**

**When `inverted = false`:**
- `mask_pred > 0.5` → **MASK detected**
- `mask_pred <= 0.5` → **NO MASK detected**

### Why Toggle?

Different mask detection models may be trained with different label conventions:
- Some models output high values for "mask present"
- Others output high values for "no mask present"

The toggle allows you to correct the interpretation without retraining the model.

---

## Usage in Admin Dashboard

### Frontend Integration

```javascript
// Get current state
const getMaskLogic = async () => {
  const response = await fetch('http://localhost:5000/admin/mask-logic', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.inverted;
};

// Toggle state
const toggleMaskLogic = async () => {
  const response = await fetch('http://localhost:5000/admin/mask-logic/toggle', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  console.log(data.message); // "Mask logic inverted" or "Mask logic normal"
  return data.inverted;
};
```

### React Example

```jsx
const [maskInverted, setMaskInverted] = useState(true);

useEffect(() => {
  // Load initial state
  getMaskLogic().then(setMaskInverted);
}, []);

const handleToggle = async () => {
  const newState = await toggleMaskLogic();
  setMaskInverted(newState);
};

return (
  <div>
    <label>
      <input 
        type="checkbox" 
        checked={maskInverted} 
        onChange={handleToggle}
      />
      Invert Mask Logic
    </label>
    <p>
      Current: {maskInverted ? 'Inverted' : 'Normal'}
    </p>
  </div>
);
```

---

## Testing

Run the test script:

```bash
cd backend
python test_mask_toggle.py
```

Expected output:
```
==================================================
Testing Mask Logic Toggle API
==================================================
✅ Login successful

1. Getting current mask logic state...
📊 Current Mask Logic:
   Inverted: True
   Description: If true: mask_pred < 0.5 = MASK, mask_pred >= 0.5 = NO MASK

2. Toggling mask logic...
🔄 Mask Logic Toggled:
   Success: True
   New State: False
   Message: Mask logic normal

3. Getting new mask logic state...
📊 Current Mask Logic:
   Inverted: False
   Description: If true: mask_pred < 0.5 = MASK, mask_pred >= 0.5 = NO MASK

✅ Toggle successful! State changed.

4. Toggling back to original state...
🔄 Mask Logic Toggled:
   Success: True
   New State: True
   Message: Mask logic inverted

5. Verifying original state restored...
📊 Current Mask Logic:
   Inverted: True
   Description: If true: mask_pred < 0.5 = MASK, mask_pred >= 0.5 = NO MASK

✅ All tests passed! Toggle works correctly.
==================================================
Test Complete
==================================================
```

---

## Security Notes

- ✅ Admin-only access (JWT required)
- ✅ Role validation on every request
- ✅ State changes logged to console
- ✅ No database persistence (resets on server restart)

## Future Enhancements

- [ ] Persist state to database
- [ ] Add audit log for state changes
- [ ] Add API to set specific value (not just toggle)
- [ ] Add validation/testing mode before applying
