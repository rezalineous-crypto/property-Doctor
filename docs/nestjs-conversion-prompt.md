# NestJS Conversion Prompt

Use the following prompt to convert this Django REST API project to a NestJS backend:

---

**Prompt:**

```
I want to convert an existing Django REST Framework project to a NestJS backend. 

The current project is a PropertyMetrics API with the following structure and features:

## Project Overview
A Django REST API for managing real estate properties and tracking their performance metrics (revenue, occupancy, bookings, expenses).

## Technology Stack to Replace
- Django 6.0.3 → NestJS with TypeScript
- Django REST Framework → NestJS with proper Controllers and Services
- SQLite3 → PostgreSQL or keep SQLite for simplicity
- django-filter → NestJS with class-validator and custom filters

## Existing Models

### Property Model
- id: Auto-increment primary key
- name: string (max 200)
- address: text
- type: enum (apartment, house, condo, townhouse, commercial)
- manager: string (max 200)
- created_at: timestamp
- updated_at: timestamp

### PropertyMetrics Model
- id: Auto-increment primary key
- property: ForeignKey to Property (one-to-many)
- month: Date (first day of month)
- revenue: decimal (12 digits, 2 decimal places)
- occupancy: decimal (5 digits, 2 decimal places, 0-100)
- bookings: positive integer
- expenses: decimal (12 digits, 2 decimal places)
- created_at: timestamp
- updated_at: timestamp

## Existing API Endpoints

### Properties
- GET /api/properties/ - List all with filtering (type, manager), search (name, manager, address), ordering
- POST /api/properties/ - Create property
- GET /api/properties/{id}/ - Get single property
- PUT /api/properties/{id}/ - Full update
- PATCH /api/properties/{id}/ - Partial update
- DELETE /api/properties/{id}/ - Delete property
- POST /api/properties/import/ - CSV import (name, address, type, manager columns)

### Metrics
- POST /api/metrics/import/ - CSV import (property_name, month, revenue, occupancy, bookings, expenses columns)

## CSV Import Features
- Both imports support update_or_create behavior
- Validates required columns
- Validates enum values (property types, occupancy range)
- Returns detailed results with created/updated counts and error list

## Filter/Query Parameters Used
- type, type__in (exact filter)
- manager, manager__contains (exact and contains)
- search (name, manager, address)
- ordering (name, type, manager, created_at, updated_at)

Please create a complete NestJS project structure that includes:

1. Module structure with Properties and Metrics modules
2. DTOs for creating/updating properties and metrics with validation
3. Entities matching the current models using TypeORM
4. Controllers matching the existing API endpoints
5. Services with business logic including CSV parsing
6. Proper error handling and response formats
7. Filtering and pagination support
8. Swagger/OpenAPI documentation
9. A README with setup instructions

Use the same API routes (/api/properties/ and /api/metrics/import/).
Ensure the CSV import logic matches the existing behavior exactly.
```

---

## Additional Notes for the Conversion

When running the conversion prompt, consider these specifics:

1. **Database**: Recommend using TypeORM with SQLite for development (matching current db.sqlite3) or PostgreSQL for production

2. **CSV Parsing**: NestJS can use `csv-parser` or `papaparse` npm packages

3. **Validation**: Use `class-validator` and `class-transformer` for DTO validation

4. **Filtering**: Implement custom filtering or use `nestjs-query` for advanced filtering

5. **API Documentation**: Add Swagger using `@nestjs/swagger` package

6. **Error Handling**: Use NestJS exception filters for consistent error responses

---

## Alternative Prompt (Shorter Version)

If you prefer a more concise prompt:

```
Convert this Django REST API to NestJS:
- Property model: name, address, type (apartment/house/condo/townhouse/commercial), manager, timestamps
- PropertyMetrics: property (FK), month, revenue, occupancy (0-100), bookings, expenses, timestamps
- Endpoints: CRUD for /api/properties/ with filtering/search/ordering, POST /api/properties/import/ for CSV, POST /api/metrics/import/ for metrics CSV
- CSV imports should do update_or_create and return created/updated counts with errors
- Use TypeORM, add Swagger docs, include validation
```
