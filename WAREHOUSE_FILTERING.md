# Location-Based Warehouse Filtering

This functionality implements server-side warehouse filtering based on location for all transactional documents (Sales Invoice, Purchase Invoice, Sales Order, Purchase Order, Delivery Note, Purchase Receipt).

## How it Works

### 1. Location-Warehouse Linking
- Each Location document should have a `linked_warehouse` field
- This warehouse can be either:
  - **Group Warehouse**: Shows all descendant non-group warehouses
  - **Non-Group Warehouse**: Auto-selects that specific warehouse

### 2. Server-Side Filtering
- When a location is selected, warehouse fields are filtered to show only valid warehouses
- This applies to both document-level and child table warehouse fields
- Invalid warehouses are blocked during validation

### 3. Auto-Selection
- If a location has only one valid warehouse, it will be auto-selected in:
  - Document-level warehouse fields (`warehouse`, `set_warehouse`, `source_warehouse`, `target_warehouse`)
  - Child table warehouse fields (`warehouse`, `s_warehouse`, `t_warehouse`, etc.)

## Installation

### For New Installations
The functionality is automatically installed when you install the app.

### For Existing Installations
Run one of these commands:

#### Method 1: Using Patch (Recommended)
```bash
bench migrate
```

#### Method 2: Manual Installation
```python
# In Frappe Console
frappe.call('location_based_series.commands.install_scripts.install_warehouse_filtering')
```

#### Method 3: Reinstall Scripts
```python
# In Frappe Console
frappe.call('location_based_series.commands.install_scripts.reinstall_warehouse_filtering')
```

## Configuration

### 1. Setup Location Documents
Ensure your Location documents have:
- `linked_warehouse` field pointing to the relevant warehouse
- Proper warehouse hierarchy if using group warehouses

### 2. Warehouse Structure
- **Group Warehouse**: Set `is_group = 1`, contains child warehouses
- **Leaf Warehouse**: Set `is_group = 0`, actual storage location

## Features

### 1. Document-Level Validation
- Validates all warehouse fields against location
- Shows clear error messages with valid warehouse options
- Prevents saving with invalid warehouse selections

### 2. Child Table Support
- Handles warehouse fields in item tables
- Auto-populates warehouse fields when possible
- Validates child table warehouse selections

### 3. Real-Time Filtering
- Updates warehouse options when location changes
- Clears invalid selections automatically
- Provides immediate feedback to users

### 4. Server-Side Implementation
- No dependency on custom field JSON configurations
- Uses server-side query methods for better performance
- Handles complex warehouse hierarchies efficiently

## Supported Documents

- Sales Invoice
- Purchase Invoice
- Sales Order
- Purchase Order
- Delivery Note
- Purchase Receipt

## Supported Warehouse Fields

### Document Level
- `warehouse`
- `set_warehouse`
- `source_warehouse`
- `target_warehouse`

### Child Tables
- `warehouse`
- `s_warehouse`
- `t_warehouse`
- `source_warehouse`
- `target_warehouse`

## Error Messages

The system provides clear error messages:
- "No valid warehouses found for location '{location}'"
- "Warehouse '{warehouse}' is not valid for location '{location}'. Valid warehouses are: {list}"

## Troubleshooting

### Scripts Not Working
1. Check if client scripts are installed:
   ```sql
   SELECT name, dt, enabled FROM `tabClient Script` 
   WHERE name LIKE 'Location Based Warehouse Filter%';
   ```

2. Reinstall scripts:
   ```python
   frappe.call('location_based_series.commands.install_scripts.reinstall_warehouse_filtering')
   ```

### Warehouse Not Showing
1. Verify location has `linked_warehouse` field set
2. Check warehouse is not disabled
3. For group warehouses, ensure there are non-group descendants

### Auto-Selection Not Working
1. Ensure location has exactly one valid warehouse
2. Check validation functions are not throwing errors
3. Verify document has the expected warehouse fields

## Uninstallation

To remove the warehouse filtering functionality:

```python
# In Frappe Console
frappe.call('location_based_series.commands.install_scripts.uninstall_warehouse_filtering')
```

This will remove all client scripts but keep the server-side validation functions active. 