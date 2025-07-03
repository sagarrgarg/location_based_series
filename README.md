## Location Based Series

Adds location-based naming conventions and validation for transactional documents like Sales and Purchase Invoices.

### Features

- **Location-based Document Naming**: Automatic naming based on location and fiscal year
- **Warehouse Filtering**: Filters warehouse options based on selected location
- **Document Validation**: Ensures location consistency across documents

### Warehouse Filtering

The app automatically filters warehouse options in the following documents based on the selected location:

- Sales Invoice
- Purchase Invoice
- Sales Order
- Purchase Order
- Delivery Note
- Purchase Receipt

#### Implementation

Warehouse filtering is implemented using **doc.js files** (not client scripts) to ensure the logic is not visible in the client script backend. The filtering logic is loaded automatically via `hooks.py` configuration.

#### Migration from Client Scripts

If you were previously using client scripts for warehouse filtering, you can migrate to the new doc.js approach:

```bash
bench --site your-site.com migrate-to-docjs
```

### Installation

1. Install the app: `bench --site your-site.com install-app location_based_series`
2. The app will automatically clear any existing client scripts and load the new doc.js files

### License

MIT