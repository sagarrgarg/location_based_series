# Migration from Client Scripts to Doc.js Files

## Overview

The location_based_series app has been updated to use **doc.js files** instead of client scripts for warehouse filtering functionality. This change ensures that the filtering logic is not visible in the client script backend.

## What Changed

### Before (Client Scripts)
- Warehouse filtering logic was implemented as client scripts
- Scripts were visible in Setup > Customize > Client Script
- Scripts were installed/uninstalled via hooks.py

### After (Doc.js Files)
- Warehouse filtering logic is now in individual doc.js files
- Files are located in `public/js/` directory
- Automatically loaded via `hooks.py` doctype_js configuration
- Not visible in client script backend

## Files Created

The following doc.js files have been created:

- `public/js/sales_invoice.js`
- `public/js/purchase_invoice.js`
- `public/js/sales_order.js`
- `public/js/purchase_order.js`
- `public/js/delivery_note.js`
- `public/js/purchase_receipt.js`

## Configuration Changes

### hooks.py Updates
- Added `doctype_js` configuration to load doc.js files
- Removed client script installation/uninstallation hooks
- Added function to clear existing client scripts during installation

### install.py Updates
- Added `clear_existing_client_scripts()` function
- This function removes any existing client scripts created by the app

## Migration Process

### Automatic Migration
When you install/update the app, it will automatically:
1. Clear any existing client scripts created by this app
2. Load the new doc.js files via hooks.py

### Manual Migration (if needed)
If you need to manually migrate, you can run:

```bash
bench --site your-site.com migrate-to-docjs
```

## Benefits

1. **Security**: Logic is not visible in client script backend
2. **Performance**: Doc.js files are loaded more efficiently
3. **Maintainability**: Easier to maintain and version control
4. **Standard Practice**: Follows Frappe's recommended approach for doctype-specific JavaScript

## Verification

After migration, you can verify the change by:

1. Checking that no client scripts exist for the target doctypes in Setup > Customize > Client Script
2. Confirming that warehouse filtering still works in the target documents
3. Verifying that the doc.js files are loaded (check browser developer tools)

## Rollback (if needed)

If you need to rollback to client scripts:

1. Comment out the `doctype_js` configuration in hooks.py
2. Uncomment the client script installation hooks
3. Reinstall the app

## Support

The functionality remains exactly the same - only the implementation method has changed. All warehouse filtering features continue to work as before. 