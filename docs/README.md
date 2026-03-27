# PropertyMetrics API Documentation

## Overview

PropertyMetrics is a Django REST Framework-based API application for managing real estate properties and their performance metrics. It allows users to manage properties (apartments, houses, condos, townhouses, commercial spaces) and track key performance indicators such as revenue, occupancy rates, bookings, and expenses.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Technology Stack](#technology-stack)
3. [API Endpoints](#api-endpoints)
4. [Models](#models)
5. [Serializers](#serializers)
6. [CSV Import Formats](#csv-import-formats)
7. [Filtering and Search](#filtering-and-search)
8. [Setup Instructions](#setup-instructions)

---

## Project Structure

```
propertyMetrics/
├── propertyMetrics/          # Main Django project settings
│   ├── settings.py          # Django configuration
│   ├── urls.py              # Root URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── properties/              # Properties app
│   ├── models.py            # Property model
│   ├── views.py             # Property CRUD & import views
│   ├── serializers.py      # Property serializer
│   ├── urls.py              # Property URL routing
│   └── admin.py             # Django admin configuration
├── metrices/                # Metrics app (note: intentionally misspelled)
│   ├── models.py            # PropertyMetrics model
│   ├── views.py             # Metrics import views
│   ├── serializers.py       # Metrics serializer
│   ├── urls.py              # Metrics URL routing
│   └── admin.py             # Django admin configuration
└── db.sqlite3               # SQLite database
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 6.0.3 |
| API Framework | Django REST Framework |
| Database | SQLite3 |
| Filtering | django-filter |
| Python | 3.x |

---

## API Endpoints

### Base URLs
- Properties API: `/api/`
- Metrics API: `/api/metrics/`

### Properties Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/properties/` | List all properties |
| POST | `/api/properties/` | Create a new property |
| GET | `/api/properties/{id}/` | Retrieve a single property |
| PUT | `/api/properties/{id}/` | Update a property (full) |
| PATCH | `/api/properties/{id}/` | Update a property (partial) |
| DELETE | `/api/properties/{id}/` | Delete a property |
| POST | `/api/properties/import/` | Import properties from CSV |

### Metrics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/metrics/import/` | Import metrics from CSV |

---

## Models

### Property Model

Represents a real estate property in the system.

**Location:** [`properties/models.py`](propertyMetrics/properties/models.py:4)

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `name` | CharField (200) | Property name |
| `address` | TextField | Property address |
| `type` | CharField (50) | Property type (apartment, house, condo, townhouse, commercial) |
| `manager` | CharField (200) | Property manager name |
| `created_at` | DateTimeField | Creation timestamp (auto) |
| `updated_at` | DateTimeField | Last update timestamp (auto) |

**Property Types:**
- `apartment` - Apartment
- `house` - House
- `condo` - Condo
- `townhouse` - Townhouse
- `commercial` - Commercial space

---

### PropertyMetrics Model

Represents monthly performance metrics for a property.

**Location:** [`metrices/models.py`](propertyMetrics/metrices/models.py:5)

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `property` | ForeignKey | Reference to Property model |
| `month` | DateField | First day of the month (YYYY-MM-DD) |
| `revenue` | DecimalField | Monthly revenue (max 12 digits, 2 decimal places) |
| `occupancy` | DecimalField | Occupancy percentage (0-100%) |
| `bookings` | PositiveIntegerField | Number of bookings |
| `expenses` | DecimalField | Monthly expenses |
| `created_at` | DateTimeField | Creation timestamp (auto) |
| `updated_at` | DateTimeField | Last update timestamp (auto) |

**Constraints:**
- Unique together: `property` + `month`

---

## Serializers

### PropertySerializer

Serializes the Property model for JSON API responses.

**Location:** [`properties/serializers.py`](propertyMetrics/properties/serializers.py:5)

```python
{
    "id": 1,
    "name": "Sunset Apartments",
    "address": "123 Sunset Blvd, Los Angeles, CA",
    "type": "apartment",
    "manager": "John Doe",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### PropertyMetricsSerializer

Serializes the PropertyMetrics model with related property name.

**Location:** [`metrices/serializers.py`](propertyMetrics/metrices/serializers.py:5)

```python
{
    "id": 1,
    "property": 1,
    "property_name": "Sunset Apartments",
    "month": "2024-01-01",
    "revenue": "15000.00",
    "occupancy": "85.50",
    "bookings": 25,
    "expenses": "5000.00",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

**Validation:**
- `occupancy` must be between 0 and 100

---

## CSV Import Formats

### Property Import CSV

**Endpoint:** `POST /api/properties/import/`

**Required Columns:**
| Column | Description | Example |
|--------|-------------|---------|
| `name` | Property name (unique) | Sunset Apartments |
| `address` | Property address | 123 Sunset Blvd |
| `type` | Property type | apartment |
| `manager` | Manager name | John Doe |

**Example CSV:**
```csv
name,address,type,manager
Sunset Apartments,123 Sunset Blvd,apartment,John Doe
Ocean House,456 Beach Road,house,Jane Smith
Downtown Condo,789 Main St,condo,Bob Wilson
```

**Valid Property Types:** `apartment`, `house`, `condo`, `townhouse`, `commercial`

**Behavior:**
- Creates new property if name doesn't exist
- Updates existing property if name matches
- Returns detailed results including created/updated counts and errors

---

### Metrics Import CSV

**Endpoint:** `POST /api/metrics/import/`

**Required Columns:**
| Column | Description | Example |
|--------|-------------|---------|
| `property_name` | Name of existing property | Sunset Apartments |
| `month` | Month in YYYY-MM format | 2024-01 |
| `revenue` | Revenue amount | 15000.00 |
| `occupancy` | Occupancy percentage (0-100) | 85.50 |
| `bookings` | Number of bookings | 25 |
| `expenses` | Expenses amount | 5000.00 |

**Example CSV:**
```csv
property_name,month,revenue,occupancy,bookings,expenses
Sunset Apartments,2024-01,15000.00,85.50,25,5000.00
Sunset Apartments,2024-02,16500.00,90.00,28,5200.00
Ocean House,2024-01,12000.00,75.00,15,4000.00
```

**Behavior:**
- Property must exist in database (referenced by name)
- Month format must be YYYY-MM
- Occupancy must be between 0 and 100
- Creates new metrics if property+month combination doesn't exist
- Updates existing metrics if combination exists
- Returns detailed results including created/updated counts and errors

---

## Filtering and Search

### Property Filtering

The Properties endpoint supports advanced filtering:

**Filter Fields (exact match):**
- `type` - Filter by property type
- `type__in` - Filter by multiple types
- `manager` - Exact manager match
- `manager__contains` - Manager name contains

**Search Fields:**
- `name` - Search in property name
- `manager` - Search in manager name
- `address` - Search in address

**Ordering Fields:**
- `name` - Sort by name
- `type` - Sort by type
- `manager` - Sort by manager
- `created_at` - Sort by creation date
- `updated_at` - Sort by update date

**Example Queries:**

```bash
# Filter by type
GET /api/properties/?type=apartment

# Filter by multiple types
GET /api/properties/?type__in=apartment,condo

# Search properties
GET /api/properties/?search=sunset

# Order by creation date
GET /api/properties/?ordering=created_at

# Combined filtering
GET /api/properties/?type=apartment&manager__contains=John&ordering=-created_at
```

---

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Django 6.0.3
- Django REST Framework
- django-filter

### Installation

1. **Navigate to project directory:**
   ```bash
   cd propertyMetrics
   ```

2. **Install dependencies:**
   ```bash
   pip install django djangorestframework django-filter
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server:**
   ```bash
   python manage.py runserver
   ```

### Access Points

| Service | URL |
|---------|-----|
| Admin Panel | http://localhost:8000/admin/ |
| API Root | http://localhost:8000/api/ |
| Properties API | http://localhost:8000/api/properties/ |
| Metrics API | http://localhost:8000/api/metrics/import/ |

---

## Error Responses

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 207 | Multi-Status (partial success with errors) |
| 400 | Bad Request |
| 404 | Not Found |

### Example Error Responses

**Missing File:**
```json
{
    "error": "No file provided"
}
```

**Invalid CSV Format:**
```json
{
    "error": "CSV must contain columns: ['name', 'address', 'type', 'manager']"
}
```

**Validation Error:**
```json
{
    "error": "Invalid type 'invalid'. Must be one of: apartment, house, condo, townhouse, commercial"
}
```

---

## Admin Configuration

Both models are registered with the Django admin interface for easy data management.

**Admin URL:** `/admin/`

The admin provides:
- List view with search and filtering
- Add/Edit forms for properties and metrics
- Delete functionality
- Date-based filtering for metrics

---

## Response Formats

### Success Response (Property Import)
```json
{
    "status": "success",
    "message": "Successfully imported 5 new, updated 2 existing records",
    "results": {
        "created": 5,
        "updated": 2,
        "errors": []
    }
}
```

### Partial Success Response
```json
{
    "status": "completed_with_errors",
    "message": "Imported 3 new, updated 1 existing records",
    "results": {
        "created": 3,
        "updated": 1,
        "errors": [
            {
                "row": 5,
                "error": "Invalid type 'invalid_type'. Must be one of: apartment, house, condo, townhouse, commercial"
            }
        ]
    }
}
```

---

## License

This project is provided as-is for property management and metrics tracking purposes.
