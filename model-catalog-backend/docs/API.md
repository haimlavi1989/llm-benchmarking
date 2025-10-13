# API Documentation

## Overview

The Model Catalog Backend API provides endpoints for managing ML model catalogs. The API follows RESTful principles and uses JSON for data exchange.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.modelcatalog.com`

## Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

## Endpoints

### Health Check

#### GET /health

Check the health status of the API.

**Response:**
```json
{
  "status": "healthy"
}
```

### Root

#### GET /

Get basic information about the API.

**Response:**
```json
{
  "message": "Model Catalog Backend API",
  "version": "0.1.0"
}
```

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

```json
{
  "detail": "Error message",
  "type": "error_type",
  "status_code": 400
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse. Rate limit headers are included in responses:

- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Pagination

List endpoints support pagination using query parameters:

- `page`: Page number (default: 1)
- `size`: Page size (default: 20, max: 100)

Response includes pagination metadata:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```
