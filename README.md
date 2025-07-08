# Location Based Series

A comprehensive ERPNext app that provides advanced location-based warehouse and address filtering capabilities for purchase and sales documents. This app extends ERPNext's location functionality to enable separate billing and shipping/dispatch operations with intelligent warehouse filtering.

## 🌟 Features

### 📦 **Purchase Documents Support**
- **Purchase Order (PO)**: Separate shipping location with filtered warehouses
- **Purchase Invoice (PI)**: Location-based warehouse filtering for invoicing
- **Purchase Receipt (PR)**: Intelligent warehouse selection based on location

### 🚚 **Sales Documents Support**
- **Sales Order (SO)**: Dispatch location with filtered warehouses
- **Sales Invoice (SI)**: Location-based warehouse filtering for sales
- **Delivery Note (DN)**: Intelligent warehouse selection for deliveries

### 🏢 **Advanced Location Management**
- **Main Location**: Controls billing/company addresses and general warehouse filtering
- **Shipping Location**: For purchase documents - filters shipping addresses and warehouses separately
- **Dispatch Location**: For sales documents - filters dispatch addresses and warehouses separately

### 🔄 **Smart Auto-Fill**
- **One-to-One Relationships**: Automatically fills shipping/dispatch addresses when location is selected
- **Warehouse Filtering**: Filters warehouses based on selected location (group and non-group warehouses supported)
- **Address Validation**: Ensures addresses are linked to the selected location

### ✅ **Comprehensive Validation**
- **Document State Validation**: Prevents location changes after document submission
- **Warehouse Validation**: Ensures selected warehouses are valid for the location
- **Address Validation**: Validates address selection against location
- **Error Handling**: Clear error messages for invalid selections

## 🚀 Quick Start

### Installation

```bash
# Install the app
bench get-app location_based_series
bench install-app location_based_series

# Run installation script
bench --site your-site.com console
```

In the console:
```python
from location_based_series.install import install_shipping_location
install_shipping_location()
```

**Important**: After installation, you must manually add Location as an accounting dimension (see Setup section below).

### Setup

1. **Add Location as Accounting Dimension**:
   - Go to **Setup > Customize > Accounting Dimensions**
   - Click **New**
   - Set **Document Type** to "Location"
   - Set **Label** to "Location"
   - Set **Fieldname** to "location"
   - Check **Apply to All Child Tables**
   - Save the accounting dimension

2. **Create Locations**: Set up Location documents with linked warehouses and addresses
3. **Configure Fields**: Ensure each Location has `linked_warehouse` and `linked_address` fields
4. **Test Documents**: Create test PO, PI, PR, SO, SI, and DN documents

## 📋 Usage Guide

### Purchase Documents Workflow

1. **Create Purchase Document** (PO/PI/PR)
2. **Select Main Location** (for billing operations)
3. **Optionally Select Shipping Location** (for shipping operations)
4. **Auto-filled Address**: Shipping address automatically fills based on shipping location
5. **Filtered Warehouses**: Only warehouses linked to shipping location are available
6. **Validation**: System validates all selections before submission

### Sales Documents Workflow

1. **Create Sales Document** (SO/SI/DN)
2. **Select Main Location** (for company operations)
3. **Optionally Select Dispatch Location** (for dispatch operations)
4. **Auto-filled Address**: Dispatch address automatically fills based on dispatch location
5. **Filtered Warehouses**: Only warehouses linked to dispatch location are available
6. **Validation**: System validates all selections before submission

### Field Behavior

| Field | Behavior |
|-------|----------|
| **Main Location** | Controls billing-related warehouses and addresses |
| **Shipping Location** | Controls shipping-related warehouses and addresses (Purchase docs) |
| **Dispatch Location** | Controls dispatch-related warehouses and addresses (Sales docs) |
| **Shipping Address** | Auto-filled when shipping location is selected |
| **Dispatch Address** | Auto-filled when dispatch location is selected |
| **Warehouse Fields** | Filtered based on active location (shipping/dispatch takes precedence) |

## 🔧 Technical Implementation

### Server-Side Components

#### Core Utility Functions
- `location_based_warehouse_query()`: Filters warehouses by main location
- `shipping_location_based_warehouse_query()`: Filters warehouses by shipping location
- `dispatch_location_based_warehouse_query()`: Filters warehouses by dispatch location
- `shipping_location_based_address_query()`: Filters addresses by shipping location
- `dispatch_location_based_address_query()`: Filters addresses by dispatch location

#### Validation Functions
- `validate_warehouse_against_location()`: Validates warehouse selection
- `validate_shipping_address_against_shipping_location()`: Validates shipping address
- `validate_dispatch_address_against_dispatch_location()`: Validates dispatch address

#### Auto-Fill Functions
- `auto_set_shipping_address_for_shipping_location()`: Auto-fills shipping address
- `auto_set_dispatch_address_for_dispatch_location()`: Auto-fills dispatch address

### Client-Side Components

#### Shared Utility Module (`location_utils.js`)
- `setLocationQueries()`: Sets up warehouse and address queries
- `handleLocationChange()`: Handles location field changes
- `autoFillAddress()`: Auto-fills addresses
- `resetWarehouseFields()`: Resets warehouse fields when location is cleared

#### Document-Specific Scripts
- Optimized scripts for PO, PI, PR, SO, SI, and DN
- Each script reduced from ~200+ lines to ~30 lines
- Consistent API across all document types

### Database Schema

#### Custom Fields Added
- `shipping_location` (Link - Location): Added to PO, PI, PR documents
- `dispatch_location` (Link - Location): Added to SO, SI, DN documents

#### Field Positions
- **Purchase Documents**: After `location` field
- **Sales Documents**: After appropriate column breaks for optimal UI layout

## 🛡️ Validation Rules

### Document State Restrictions
- **Draft State (docstatus = 0)**: All location fields can be modified
- **Submitted State (docstatus = 1)**: Location fields are locked
- **Cancelled State (docstatus = 2)**: All fields are locked

### Field Validation
- **Location Fields**: Must be valid Location documents
- **Address Fields**: Must be linked to the selected location
- **Warehouse Fields**: Must be linked to the selected location
- **Auto-fill**: Addresses are automatically filled when location is selected

### Error Messages
- "Shipping location field cannot be modified after submission"
- "Dispatch location field cannot be modified after submission"
- "Warehouse '{warehouse}' is not valid for location '{location}'"
- "Address '{address}' is not valid for location '{location}'"

## 🔍 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Location not available** | Ensure Location document exists and is not disabled |
| **Location field not appearing** | Add Location as accounting dimension in Setup > Customize > Accounting Dimensions |
| **Warehouse not filtering** | Check if Location has linked warehouse |
| **Address not auto-filling** | Verify Location has linked address |
| **Validation errors** | Check document status and field relationships |
| **Client scripts not working** | Clear browser cache and reload |

### Debug Steps

1. **Check Console Logs**: Look for JavaScript errors in browser console
2. **Verify Custom Fields**: Ensure location fields are properly installed
3. **Verify Accounting Dimension**: Ensure Location is added as an accounting dimension
4. **Test Location Setup**: Verify Location documents have correct linked fields
5. **Clear Cache**: Run `bench clear-cache` and refresh browser

## 📊 Performance & Optimization

### Code Optimization
- **Reduced Redundancy**: ~32% code reduction through generic functions
- **Shared Utilities**: Single source of truth for location logic
- **Optimized Queries**: Efficient database queries with proper indexing
- **Caching**: Results cached to reduce database load

### Performance Benefits
- **Smaller File Sizes**: Optimized client scripts (85% reduction)
- **Better Caching**: Shared modules cached more effectively
- **Memory Efficiency**: Less duplicate code in memory
- **Query Optimization**: Generic functions allow better query optimization

## 🔮 Future Enhancements

### Planned Features
- **Multiple Locations**: Support for multiple shipping/dispatch locations per document
- **Location Groups**: Hierarchical location management
- **Advanced Filtering**: More sophisticated warehouse and address filtering rules
- **API Integration**: REST API endpoints for location management
- **Reporting**: Enhanced reporting on location-based operations

### Extension Points
- **Custom Validation**: Support for custom validation rules
- **Location Types**: Support for different types of locations
- **Integration**: Better integration with other ERPNext modules
- **Mobile Support**: Enhanced mobile interface support

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/location_based_series.git

# Install in development mode
bench get-app location_based_series --branch develop
bench install-app location_based_series

# Run tests
bench --site your-site.com run-tests --app location_based_series
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check this README and inline code comments
- **Issues**: Create an issue in the project repository
- **Community**: Ask questions in Frappe/ERPNext community forums
- **Email**: Contact support at support@yourcompany.com

### Reporting Bugs
When reporting bugs, please include:
- ERPNext version
- App version
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs

## 📈 Changelog

### Version 1.1.0 (Current)
- ✅ Added dispatch location support for sales documents
- ✅ Enhanced validation and error handling
- ✅ Improved performance and caching
- ✅ Code optimization and redundancy reduction (~32%)
- ✅ Comprehensive documentation

### Version 1.0.0
- ✅ Initial release with shipping location support
- ✅ Basic warehouse and address filtering
- ✅ Auto-fill functionality
- ✅ Validation rules

## 🏆 Why Choose Location Based Series?

### ✅ **Comprehensive Coverage**
- Supports all major ERPNext documents (PO, PI, PR, SO, SI, DN)
- Handles both purchase and sales workflows
- Covers main, shipping, and dispatch locations

### ✅ **Intelligent Automation**
- Auto-fills addresses based on location selection
- Filters warehouses intelligently (group and non-group support)
- Validates all selections automatically

### ✅ **Enterprise Ready**
- Robust validation and error handling
- Performance optimized with caching
- Scalable architecture for future enhancements

### ✅ **Developer Friendly**
- Clean, optimized codebase
- Comprehensive documentation
- Easy to extend and customize

### ✅ **User Friendly**
- Intuitive interface
- Clear error messages
- Seamless integration with ERPNext

---

**Ready to streamline your location-based operations? Install Location Based Series today!**

[Install Now](#installation) | [View Documentation](#usage-guide) | [Report Issues](https://github.com/your-username/location_based_series/issues)