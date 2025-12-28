# Fellow.app API Contracts

**Feature**: Notes-Only Backup  
**Branch**: `002-notes-only-backup`  
**Date**: 2025-12-28

## Overview

This document defines the API contracts for Fellow.app endpoints used by the notes-only backup feature. Only the POST /api/v1/notes endpoint is required per the feature specification.

## Authentication

**Method**: Bearer Token Authentication

**Header**:
```
Authorization: Bearer {api_token}
```

**Token Source**: Environment variable `FELLOW_API_TOKEN` or configuration file

**Error Response** (401 Unauthorized):
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired API token"
}
```

## Base URL

```
https://api.fellow.app
```

## Endpoints

### POST /api/v1/notes

**Purpose**: Retrieve all notes accessible to the authenticated user with pagination support.

**Method**: POST

**Endpoint**: `/api/v1/notes`

**Headers**:
```
Authorization: Bearer {api_token}
Content-Type: application/json
Accept: application/json
```

**Request Body**:
```json
{
  "page": 1,
  "per_page": 100,
  "updated_after": "2025-12-27T00:00:00Z"
}
```

**Request Parameters**:

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| page | integer | No | Page number for pagination | 1 |
| per_page | integer | No | Results per page | 100 |
| updated_after | string (ISO 8601) | No | Filter notes updated after this timestamp | null |

**Success Response** (200 OK):

```json
{
  "notes": [
    {
      "id": "note_abc123def456",
      "content": "This is the note content with full Unicode support: 🎉 こんにちは",
      "author": {
        "id": "user_xyz789",
        "name": "John Doe"
      },
      "created_at": "2025-12-20T14:30:00Z",
      "updated_at": "2025-12-27T10:15:00Z"
    },
    {
      "id": "note_ghi789jkl012",
      "content": "Another note example",
      "author": {
        "id": "user_abc123",
        "name": "Jane Smith"
      },
      "created_at": "2025-12-21T09:00:00Z",
      "updated_at": "2025-12-21T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total_pages": 13,
    "total_count": 1234
  }
}
```

**Response Fields**:

**notes** (array of objects):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique note identifier |
| content | string | Yes | Full note text content |
| author.id | string | Yes | Author's user ID |
| author.name | string | Yes | Author's display name |
| created_at | string (ISO 8601) | Yes | Note creation timestamp |
| updated_at | string (ISO 8601) | Yes | Last update timestamp |

**pagination** (object):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| page | integer | Yes | Current page number |
| per_page | integer | Yes | Results per page |
| total_pages | integer | Yes | Total number of pages |
| total_count | integer | Yes | Total number of notes |

**Error Responses**:

**400 Bad Request** - Invalid parameters:
```json
{
  "error": "Bad Request",
  "message": "Invalid page parameter: must be positive integer",
  "field": "page"
}
```

**401 Unauthorized** - Authentication failure:
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired API token"
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Please retry after specified time.",
  "retry_after": 60
}
```

**Response Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1735382400
```

**500 Internal Server Error** - Server error:
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred. Please try again later."
}
```

**503 Service Unavailable** - Temporary outage:
```json
{
  "error": "Service Unavailable",
  "message": "Service is temporarily unavailable. Please retry after specified time.",
  "retry_after": 300
}
```

## Rate Limiting

**Limits**: 
- 100 requests per minute per API token (inferred from headers)
- Rate limit headers included in all responses

**Strategy**:
- Monitor X-RateLimit-Remaining header
- Implement exponential backoff on 429 responses
- Use retry_after value from 429 response body
- Add jitter to prevent thundering herd

**Backoff Algorithm**:
```
wait_time = min(base_delay * (2 ^ attempt) + random(0, 1000ms), max_delay)
base_delay = 1 second
max_delay = 60 seconds
max_attempts = 5
```

## Pagination Handling

**Strategy**:
1. Start with page=1
2. Continue fetching pages until page >= total_pages
3. Accumulate all notes from all pages
4. Handle pagination metadata changes between requests gracefully

**Example Pagination Loop**:
```python
all_notes = []
page = 1
total_pages = 1

while page <= total_pages:
    response = post_notes(page=page, per_page=100)
    all_notes.extend(response["notes"])
    total_pages = response["pagination"]["total_pages"]
    page += 1
```

## Data Validation

**Client-Side Validation** (before processing):

1. **Response Structure**:
   - Verify "notes" array exists
   - Verify "pagination" object exists
   - Verify required fields in each note

2. **Field Validation**:
   - id: non-empty string
   - content: string (can be empty)
   - author.id: non-empty string
   - author.name: non-empty string
   - timestamps: valid ISO 8601 format

3. **Error Handling**:
   - Invalid timestamp: Log warning, use None
   - Missing optional field: Use None/null
   - Missing required field: Log error, skip note
   - Malformed JSON: Retry request, then fail

## Contract Testing

**Test Cases**:

1. **Successful Pagination**:
   - Request first page
   - Verify 200 response with notes array
   - Verify pagination metadata
   - Request subsequent pages until complete

2. **Empty Results**:
   - Request with updated_after in future
   - Verify 200 response with empty notes array
   - Verify pagination shows 0 total_count

3. **Authentication Failure**:
   - Request with invalid token
   - Verify 401 response with error message

4. **Rate Limiting**:
   - Make rapid consecutive requests
   - Verify 429 response eventually
   - Verify retry_after field present
   - Verify backoff and retry succeeds

5. **Large Content**:
   - Verify notes with multi-megabyte content are handled
   - Verify UTF-8 encoding preserved (emojis, non-Latin)

6. **Edge Cases**:
   - Page number beyond total_pages: verify empty notes array or error
   - per_page = 0 or negative: verify 400 error
   - updated_after with invalid format: verify 400 error

## Integration Points

**fellow_api.py Service**:
```python
async def fetch_notes(
    page: int = 1,
    per_page: int = 100,
    updated_after: Optional[datetime] = None
) -> dict:
    """Fetch notes from Fellow.app API.
    
    Args:
        page: Page number (1-indexed)
        per_page: Results per page (max 100)
        updated_after: Optional filter for incremental backup
        
    Returns:
        dict with 'notes' and 'pagination' keys
        
    Raises:
        APIAuthenticationError: Invalid credentials
        APIRateLimitError: Rate limit exceeded (includes retry_after)
        APIError: Other API errors
    """
```

**Error Exceptions**:
```python
class APIError(Exception):
    """Base API error."""
    pass

class APIAuthenticationError(APIError):
    """401 authentication error."""
    pass

class APIRateLimitError(APIError):
    """429 rate limit error."""
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after

class APIServerError(APIError):
    """5xx server error."""
    pass
```

## Compliance with Requirements

**Functional Requirements Coverage**:
- FR-001: ✅ Authentication with Bearer token
- FR-002: ✅ POST /api/v1/notes endpoint documented
- FR-003: ✅ Pagination support defined
- FR-004 through FR-009: ✅ All note fields in response
- FR-014: ✅ Rate limiting with exponential backoff
- FR-015: ✅ Request/response logging (implementation detail)
- FR-016: ✅ Error handling allows continuation

## API Version Assumptions

**Note**: This contract is based on inference from the feature specification and typical REST API patterns. Actual Fellow.app API may differ in:
- Exact endpoint path
- Request/response field names
- Pagination parameter names (offset/limit vs page/per_page)
- Rate limit values

**Validation Required**: Contract tests must be run against actual Fellow.app API or official documentation must be consulted to verify accuracy before implementation.

## Change Log

| Date | Version | Change |
|------|---------|--------|
| 2025-12-28 | 1.0 | Initial contract definition for notes-only backup |
