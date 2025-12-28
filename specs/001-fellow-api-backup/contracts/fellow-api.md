# API Contracts: Fellow.app API

**Feature**: 001-fellow-api-backup  
**Date**: 2025-12-24

## Overview

This document defines the expected contract for the Fellow.app API based on standard REST API patterns for meeting management platforms. These contracts guide implementation of the API client and serve as validation schemas for contract tests.

**Note**: Actual Fellow.app API may differ. These contracts are assumptions to be validated against real API documentation.

---

## Authentication

### Endpoint: Authentication Setup

**Assumption**: API uses Bearer token authentication.

**Headers**:
```
Authorization: Bearer {api_token}
Content-Type: application/json
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: Token lacks required permissions

---

## Common Response Patterns

### Success Response
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2025-12-24T12:00:00Z"
  }
}
```

### Paginated Response
```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 10,
    "total_count": 500
  },
  "meta": {
    "timestamp": "2025-12-24T12:00:00Z"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Meeting not found",
    "details": {
      "meeting_id": "mtg_123"
    }
  }
}
```

---

## Endpoints

### 1. List Workspaces

**Method**: `GET`  
**Path**: `/api/v1/workspaces`

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 50, max: 100)

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "ws_abc123",
      "name": "Engineering Team",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2025-12-20T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 1,
    "total_count": 1
  }
}
```

**Error Responses**:
- `401`: Unauthorized
- `429`: Rate limit exceeded
- `500`: Internal server error

---

### 2. List Meetings

**Method**: `GET`  
**Path**: `/api/v1/workspaces/{workspace_id}/meetings`

**Path Parameters**:
- `workspace_id` (string, required): Workspace identifier

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 50, max: 100)
- `updated_since` (ISO 8601 datetime, optional): Filter meetings updated after this timestamp
- `status` (string, optional): Filter by status (scheduled, completed, cancelled)

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "mtg_xyz789",
      "workspace_id": "ws_abc123",
      "title": "Sprint Planning Q1",
      "meeting_date": "2025-12-20T14:00:00Z",
      "duration_minutes": 60,
      "status": "completed",
      "created_at": "2025-12-10T09:00:00Z",
      "updated_at": "2025-12-20T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 5,
    "total_count": 247
  }
}
```

**Error Responses**:
- `400`: Invalid parameters (e.g., invalid date format)
- `404`: Workspace not found
- `429`: Rate limit exceeded

**Rate Limiting**:
- Estimated: 100 requests per minute
- Header: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

### 3. Get Meeting Details

**Method**: `GET`  
**Path**: `/api/v1/meetings/{meeting_id}`

**Path Parameters**:
- `meeting_id` (string, required): Meeting identifier

**Response** (200 OK):
```json
{
  "data": {
    "id": "mtg_xyz789",
    "workspace_id": "ws_abc123",
    "title": "Sprint Planning Q1",
    "meeting_date": "2025-12-20T14:00:00Z",
    "duration_minutes": 60,
    "status": "completed",
    "created_at": "2025-12-10T09:00:00Z",
    "updated_at": "2025-12-20T15:30:00Z",
    "participants": [
      {
        "id": "usr_111",
        "name": "Alice Johnson",
        "email": "alice@company.com",
        "role": "organizer"
      },
      {
        "id": "usr_222",
        "name": "Bob Smith",
        "email": "bob@company.com",
        "role": "attendee"
      }
    ],
    "notes_count": 8,
    "action_items_count": 3
  }
}
```

**Error Responses**:
- `404`: Meeting not found
- `429`: Rate limit exceeded

---

### 4. List Meeting Notes

**Method**: `GET`  
**Path**: `/api/v1/meetings/{meeting_id}/notes`

**Path Parameters**:
- `meeting_id` (string, required): Meeting identifier

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 50, max: 100)

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "note_aaa111",
      "meeting_id": "mtg_xyz789",
      "content": "Discussed Q1 goals: increase test coverage to 80%, reduce bug backlog by 50%",
      "author_id": "usr_111",
      "order": 1,
      "created_at": "2025-12-20T14:15:00Z",
      "updated_at": "2025-12-20T14:15:00Z"
    },
    {
      "id": "note_aaa222",
      "meeting_id": "mtg_xyz789",
      "content": "Action: Bob to create roadmap draft by end of week",
      "author_id": "usr_222",
      "order": 2,
      "created_at": "2025-12-20T14:30:00Z",
      "updated_at": "2025-12-20T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 1,
    "total_count": 8
  }
}
```

**Error Responses**:
- `404`: Meeting not found
- `429`: Rate limit exceeded

**Special Handling**:
- Content may include Unicode, emojis, markdown formatting
- Preserve whitespace and special characters

---

### 5. List Action Items

**Method**: `GET`  
**Path**: `/api/v1/meetings/{meeting_id}/action-items`

**Path Parameters**:
- `meeting_id` (string, required): Meeting identifier

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 50, max: 100)
- `completed` (boolean, optional): Filter by completion status

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "act_bbb111",
      "meeting_id": "mtg_xyz789",
      "description": "Create Q1 roadmap draft",
      "assignee_id": "usr_222",
      "due_date": "2025-12-27",
      "completed": false,
      "completed_at": null,
      "created_at": "2025-12-20T14:30:00Z",
      "updated_at": "2025-12-20T14:30:00Z"
    },
    {
      "id": "act_bbb222",
      "meeting_id": "mtg_xyz789",
      "description": "Review test coverage metrics",
      "assignee_id": "usr_111",
      "due_date": "2025-12-24",
      "completed": true,
      "completed_at": "2025-12-23T16:00:00Z",
      "created_at": "2025-12-20T14:35:00Z",
      "updated_at": "2025-12-23T16:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 1,
    "total_count": 3
  }
}
```

**Error Responses**:
- `404`: Meeting not found
- `429`: Rate limit exceeded

---

### 6. List Users/Participants

**Method**: `GET`  
**Path**: `/api/v1/workspaces/{workspace_id}/users`

**Path Parameters**:
- `workspace_id` (string, required): Workspace identifier

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 50, max: 100)

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "usr_111",
      "name": "Alice Johnson",
      "email": "alice@company.com",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2025-12-20T08:00:00Z"
    },
    {
      "id": "usr_222",
      "name": "Bob Smith",
      "email": "bob@company.com",
      "created_at": "2024-02-10T11:00:00Z",
      "updated_at": "2025-12-19T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 1,
    "total_count": 18
  }
}
```

---

## Rate Limiting

**Expected Behavior**:
- **Rate Limit**: 100-200 requests per minute (to be confirmed)
- **Headers**:
  - `X-RateLimit-Limit`: Total requests allowed per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

**Response** (429 Too Many Requests):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 30 seconds.",
    "details": {
      "retry_after": 30
    }
  }
}
```

**Client Handling**:
1. Check `X-RateLimit-Remaining` header before each request
2. If `429` received, use `Retry-After` header or exponential backoff
3. Default backoff: 2s, 4s, 8s, 16s, 32s (max 5 retries)
4. Configurable request rate limit on client side (default: 10 req/sec)

---

## Error Handling

### Network Errors
- **Timeout**: Retry with exponential backoff (max 3 retries)
- **Connection Error**: Retry immediately once, then exponential backoff

### HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad request | Log error, skip item |
| 401 | Unauthorized | Stop immediately, alert user (invalid credentials) |
| 403 | Forbidden | Stop immediately, alert user (insufficient permissions) |
| 404 | Not found | Log warning, continue with next item |
| 429 | Rate limited | Retry with backoff |
| 500 | Server error | Retry with exponential backoff (max 5 retries) |
| 502/503 | Service unavailable | Retry with exponential backoff (max 5 retries) |

### Retry Strategy

```python
def exponential_backoff(attempt: int, base_delay: float = 2.0) -> float:
    """Calculate delay for exponential backoff."""
    return min(base_delay * (2 ** attempt), 60.0)  # Max 60 seconds

# Retry logic pseudo-code
max_retries = 5
for attempt in range(max_retries):
    try:
        response = make_request()
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', exponential_backoff(attempt))
            sleep(retry_after)
            continue
        elif response.status_code >= 500:
            sleep(exponential_backoff(attempt))
            continue
        else:
            return response
    except NetworkError:
        if attempt < max_retries - 1:
            sleep(exponential_backoff(attempt))
            continue
        raise
```

---

## Pagination Strategy

**Challenge**: API returns results in pages; must fetch all pages.

**Algorithm**:
```python
def fetch_all_meetings(workspace_id: str) -> List[Meeting]:
    """Fetch all meetings with pagination."""
    all_meetings = []
    page = 1
    per_page = 100  # Max allowed
    
    while True:
        response = api_client.get_meetings(
            workspace_id=workspace_id,
            page=page,
            per_page=per_page
        )
        
        meetings = response['data']
        all_meetings.extend(meetings)
        
        pagination = response['pagination']
        if page >= pagination['total_pages']:
            break
        
        page += 1
    
    return all_meetings
```

**Optimization**:
- Use max `per_page` (100) to minimize API calls
- For incremental sync, use `updated_since` parameter to reduce data transfer
- Process each page immediately rather than loading all into memory

---

## Incremental Sync Contract

**Goal**: Fetch only meetings updated since last successful backup.

**Query Parameter**: `updated_since` (ISO 8601 datetime)

**Example Request**:
```
GET /api/v1/workspaces/ws_abc123/meetings?updated_since=2025-12-23T10:00:00Z&per_page=100
```

**Algorithm**:
1. Retrieve `last_sync_timestamp` from `backup_metadata` table
2. Query API with `updated_since={last_sync_timestamp}`
3. For each meeting, fetch updated notes and action items
4. Upsert into database
5. Update `last_sync_timestamp` to current time on success

**Edge Case**: If `updated_since` not supported by API, fall back to full sync with client-side filtering.

---

## Contract Testing

**Purpose**: Validate that Fellow.app API matches expected schema.

**Test Framework**: pytest with httpx-mock or responses library

**Test Cases**:

1. **List Meetings Schema**:
   - Verify response has `data` and `pagination` keys
   - Verify each meeting has required fields: `id`, `title`, `meeting_date`
   - Verify pagination structure

2. **Get Meeting Details Schema**:
   - Verify meeting object structure
   - Verify participants array exists
   - Verify notes_count and action_items_count are integers

3. **List Notes Schema**:
   - Verify content field is string and non-empty
   - Verify author_id references valid user
   - Verify order field is integer

4. **List Action Items Schema**:
   - Verify completed is boolean
   - Verify due_date is valid date format (YYYY-MM-DD)
   - Verify completed_at is null when completed is false

5. **Error Response Schema**:
   - Verify 401/403 returns error object with code and message
   - Verify 429 includes retry_after information

6. **Rate Limiting**:
   - Verify rate limit headers are present
   - Verify 429 response when limit exceeded

**Example Test**:
```python
def test_list_meetings_schema(httpx_mock, api_client):
    """Verify list meetings endpoint returns expected schema."""
    httpx_mock.add_response(
        url="https://api.fellow.app/api/v1/workspaces/ws_test/meetings",
        json={
            "data": [
                {
                    "id": "mtg_test",
                    "workspace_id": "ws_test",
                    "title": "Test Meeting",
                    "meeting_date": "2025-12-24T10:00:00Z",
                    "status": "scheduled",
                    "created_at": "2025-12-20T10:00:00Z",
                    "updated_at": "2025-12-23T10:00:00Z"
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_pages": 1,
                "total_count": 1
            }
        }
    )
    
    meetings = api_client.list_meetings("ws_test")
    
    assert len(meetings) == 1
    meeting = meetings[0]
    assert meeting.id == "mtg_test"
    assert meeting.title == "Test Meeting"
    assert isinstance(meeting.meeting_date, datetime)
```

---

## API Base URL

**Expected**: `https://api.fellow.app` (to be confirmed)

**Configuration**:
- Store base URL in environment variable: `FELLOW_API_BASE_URL`
- Default to `https://api.fellow.app` if not set
- Allow override for testing/staging environments

---

## Summary

This contract document defines:
- ✅ Authentication mechanism (Bearer token)
- ✅ All expected endpoints for data extraction
- ✅ Response schemas for validation
- ✅ Pagination strategy
- ✅ Rate limiting handling
- ✅ Error response patterns
- ✅ Incremental sync approach
- ✅ Contract testing requirements

**Next Step**: Validate against actual Fellow.app API documentation and adjust contracts as needed.
