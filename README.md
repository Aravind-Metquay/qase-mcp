# Qase MCP Server

## Description

Qase MCP Server is a Model Context Protocol (MCP) server that exposes Qase Test Management APIs as tools for LLM clients. It helps generate, manage, and query test cases, suites, runs, and other Qase resources directly from MCP-enabled apps.

## Installation & Setup

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

> If you prefer `uv`, you can run: `uv sync`

### 2) Configure your Qase token

Set the API token in your environment:

```bash
export QASE_API_TOKEN="your_qase_api_token"
```

### 3) Configure Claude Desktop

1. Open Claude Desktop settings → **Developer** → **Edit Config**.
2. Add a new MCP server entry:

```json
{
  "mcpServers": {
    "qase": {
      "command": "C:\\Python312\\python.exe",
      "args": ["D:\\GitHub\\qase-mcp\\main.py"],
      "cwd": "D:\\GitHub\\qase-mcp",
      "env": {
        "QASE_API_TOKEN": "your_qase_api_token"
      }
    }
  }
}
```

3. Save and restart Claude Desktop.

### 4) Configure other MCP clients

Most MCP clients support the same `command`, `args`, and `env` format. Point the client to this repo and use:

```json
{
  "command": "python",
  "args": ["main.py"],
  "env": {
    "QASE_API_TOKEN": "your_qase_api_token"
  }
}
```

### 5) Run locally (optional)

```bash
python main.py
```

## Capabilities (Quick View)

- List, create, update, and delete test cases and suites
- Create and complete test runs and results
- Manage shared steps, parameters, defects, and milestones
- Search across Qase entities using QQL

---

# Qase API Documentation for Test Case Generation & MCP Server Development

## Overview

Qase provides REST APIs (v1 and v2) for interacting with their test management platform. This documentation focuses on endpoints relevant for test case generation and management.

## Authentication

**Method:** API Token-based authentication

**Header:**
```
Token: YOUR_API_TOKEN
```

**Creating API Token:**
1. Click your user profile picture
2. Navigate to "API Tokens"
3. Click "Create a new API token"
4. Copy the token (shown only once)

**Important:** API tokens inherit the permissions of the user who creates them.

## Rate Limits

- **Standard:** 600 API requests per minute
- **Enterprise:** Custom limits available
- **Exceeded:** HTTP 429 with `Retry-After` header (60-second timeout)

## Base URLs

- **API v1:** `https://api.qase.io/v1`
- **API v2:** `https://api.qase.io/v2`

---

## API v1 Endpoints

### Test Cases

#### 1. Get All Test Cases
- **Method:** GET
- **Endpoint:** `/case/{code}`
- **Description:** Retrieve all test cases in a project
- **Parameters:**
  - `limit`: Pagination limit
  - `offset`: Pagination offset
  - `filters[priority]`: Filter by priority (e.g., high, low)
  - `filters[type]`: Filter by test type
  - `filters[severity]`: Filter by severity
  - `filters[automation]`: Filter by automation status

**Example:**
```bash
curl "https://api.qase.io/v1/case/{code}?limit=10&offset=0&filters[priority]=high,low" \
  -H "Token: api_token" \
  -H "Content-type: application/json"
```

**Response:**
```json
{
  "status": true,
  "result": {
    "total": 250,
    "filtered": 250,
    "count": 1,
    "entities": [
      {
        "id": 5,
        "position": 1,
        "title": "Test case",
        "description": "Description for case",
        "preconditions": "",
        "postconditions": "",
        "severity": 4,
        "priority": 2,
        "type": 1,
        "behavior": 2,
        "automation": "is-not-automated",
        "status": "actual",
        "milestone_id": null,
        "suite_id": 1,
        "tags": [],
        "links": [],
        "revision": 1,
        "custom_fields": [],
        "attachments": [],
        "steps": [],
        "created": "2018-05-02T20:32:23.000000Z",
        "updated": "2019-07-21T13:24:08.000000Z"
      }
    ]
  }
}
```

#### 2. Get Specific Test Case
- **Method:** GET
- **Endpoint:** `/case/{code}/{id}`
- **Description:** Retrieve a specific test case by ID

#### 3. Create Test Case
- **Method:** POST
- **Endpoint:** `/case/{code}`
- **Description:** Create a new test case in a project

**Payload Fields:**
- `title` (required): Test case title
- `description`: Test case description
- `preconditions`: Preconditions for test execution
- `postconditions`: Postconditions after test execution
- `severity`: Severity level (1-4)
- `priority`: Priority level (1-4)
- `type`: Test type ID
- `behavior`: Behavior type ID
- `automation`: Automation status
- `suite_id`: Suite ID to place the test case
- `milestone_id`: Milestone ID
- `tags`: Array of tags
- `custom_fields`: Array of custom field objects
- `steps`: Array of test step objects
  - `action`: Step action (required if shared_step_id not provided)
  - `expected_result`: Expected result
  - `data`: Input data
  - `position`: Step position
  - `attachments`: Array of attachment IDs
- `attachments`: Array of attachment IDs

**Test Case Step Structure:**
```json
{
  "position": 1,
  "action": "simple action",
  "expected_result": "expected result",
  "data": "input data",
  "attachments": [],
  "shared": false
}
```

#### 4. Create Test Cases in Bulk
- **Method:** POST
- **Endpoint:** `/case/{code}/bulk`
- **Description:** Create multiple test cases at once

#### 5. Update Test Case
- **Method:** PATCH
- **Endpoint:** `/case/{code}/{id}`
- **Description:** Update an existing test case

#### 6. Delete Test Case
- **Method:** DELETE
- **Endpoint:** `/case/{code}/{id}`
- **Description:** Delete a test case from repository

#### 7. Attach External Issues to Test Cases
- **Method:** POST
- **Endpoint:** `/case/{code}/external-issue/attach`
- **Description:** Link external issues (e.g., Jira) to test cases

#### 8. Detach External Issues from Test Cases
- **Method:** POST
- **Endpoint:** `/case/{code}/external-issue/detach`
- **Description:** Remove external issue links from test cases

---

### Test Suites

#### 1. Get All Test Suites
- **Method:** GET
- **Endpoint:** `/suite/{code}`
- **Parameters:** `limit`, `offset`, `filters[search]`

#### 2. Get Specific Test Suite
- **Method:** GET
- **Endpoint:** `/suite/{code}/{id}`

#### 3. Create Test Suite
- **Method:** POST
- **Endpoint:** `/suite/{code}`
- **Payload:**
  - `title`: Suite title (required)
  - `parent_id`: Parent suite ID
  - `description`: Suite description
  - `preconditions`: Suite preconditions

#### 4. Update Test Suite
- **Method:** PATCH
- **Endpoint:** `/suite/{code}/{id}`

#### 5. Delete Test Suite
- **Method:** DELETE
- **Endpoint:** `/suite/{code}/{id}`

---

### Shared Steps

#### 1. Get All Shared Steps
- **Method:** GET
- **Endpoint:** `/shared_step/{code}`

#### 2. Get Specific Shared Step
- **Method:** GET
- **Endpoint:** `/shared_step/{code}/{hash}`

#### 3. Create Shared Step
- **Method:** POST
- **Endpoint:** `/shared_step/{code}`

#### 4. Update Shared Step
- **Method:** PATCH
- **Endpoint:** `/shared_step/{code}/{hash}`

#### 5. Delete Shared Step
- **Method:** DELETE
- **Endpoint:** `/shared_step/{code}/{hash}`
- **Note:** Removes from all test cases using it

---

### Shared Parameters

#### 1. Get All Shared Parameters
- **Method:** GET
- **Endpoint:** `/shared_parameter/{code}`

#### 2. Get Specific Shared Parameter
- **Method:** GET
- **Endpoint:** `/shared_parameter/{code}/{id}`

#### 3. Create Shared Parameter
- **Method:** POST
- **Endpoint:** `/shared_parameter/{code}`

#### 4. Update Shared Parameter
- **Method:** PATCH
- **Endpoint:** `/shared_parameter/{code}/{id}`

#### 5. Delete Shared Parameter
- **Method:** DELETE
- **Endpoint:** `/shared_parameter/{code}/{id}`

---

### Test Plans

#### 1. Get All Test Plans
- **Method:** GET
- **Endpoint:** `/plan/{code}`

#### 2. Get Specific Test Plan
- **Method:** GET
- **Endpoint:** `/plan/{code}/{id}`
- **Returns:** Detailed information including test cases and assignees

#### 3. Create Test Plan
- **Method:** POST
- **Endpoint:** `/plan/{code}`
- **Payload:**
  - `title`: Plan title
  - `description`: Plan description
  - `cases`: Array of case IDs

#### 4. Update Test Plan
- **Method:** PATCH
- **Endpoint:** `/plan/{code}/{id}`

#### 5. Delete Test Plan
- **Method:** DELETE
- **Endpoint:** `/plan/{code}/{id}`

---

### Test Runs

#### 1. Get All Test Runs
- **Method:** GET
- **Endpoint:** `/run/{code}`

#### 2. Get Specific Test Run
- **Method:** GET
- **Endpoint:** `/run/{code}/{id}`

#### 3. Create Test Run
- **Method:** POST
- **Endpoint:** `/run/{code}`
- **Payload:**
  - `title`: Run title
  - `description`: Run description
  - `cases`: Array of case IDs
  - `environment_id`: Environment ID
  - `milestone_id`: Milestone ID

#### 4. Update Test Run
- **Method:** PATCH
- **Endpoint:** `/run/{code}/{id}`

#### 5. Delete Test Run
- **Method:** DELETE
- **Endpoint:** `/run/{code}/{id}`

#### 6. Complete Test Run
- **Method:** POST
- **Endpoint:** `/run/{code}/{id}/complete`

#### 7. Update Run Publicity
- **Method:** PATCH
- **Endpoint:** `/run/{code}/{id}/public`

#### 8. Update External Issues for Runs
- **Method:** POST
- **Endpoint:** `/run/{code}/external-issue`

---

### Test Results

#### 1. Get All Test Run Results
- **Method:** GET
- **Endpoint:** `/result/{code}/{run_id}`

#### 2. Get Specific Test Run Result
- **Method:** GET
- **Endpoint:** `/result/{code}/{run_id}/{hash}`

#### 3. Create Test Run Result
- **Method:** POST
- **Endpoint:** `/result/{code}/{run_id}`
- **Payload:**
  - `case_id`: Test case ID
  - `status`: Result status (passed, failed, blocked, skipped, invalid)
  - `time`: Execution time in milliseconds
  - `comment`: Comment
  - `defect`: Boolean - whether result has defect
  - `member_id`: Assignee ID
  - `steps`: Array of step results
  - `attachments`: Array of attachment hashes

#### 4. Bulk Create Test Run Results
- **Method:** POST
- **Endpoint:** `/result/{code}/{run_id}/bulk`

#### 5. Update Test Run Result
- **Method:** PATCH
- **Endpoint:** `/result/{code}/{run_id}/{hash}`

#### 6. Delete Test Run Result
- **Method:** DELETE
- **Endpoint:** `/result/{code}/{run_id}/{hash}`

---

### Attachments

#### 1. Get All Attachments
- **Method:** GET
- **Endpoint:** `/attachment/{code}`

#### 2. Upload Attachment
- **Method:** POST
- **Endpoint:** `/attachment/{code}`
- **Content-Type:** multipart/form-data

#### 3. Get Attachment by Hash
- **Method:** GET
- **Endpoint:** `/attachment/{code}/{hash}`

#### 4. Delete Attachment
- **Method:** DELETE
- **Endpoint:** `/attachment/{code}/{hash}`

---

### Custom Fields

#### 1. Get All Custom Fields
- **Method:** GET
- **Endpoint:** `/custom_field/{code}`

#### 2. Get Custom Field
- **Method:** GET
- **Endpoint:** `/custom_field/{code}/{id}`

#### 3. Create Custom Field
- **Method:** POST
- **Endpoint:** `/custom_field/{code}`
- **Field Types:** number, string, text, selectbox, checkbox

#### 4. Update Custom Field
- **Method:** PATCH
- **Endpoint:** `/custom_field/{code}/{id}`

#### 5. Delete Custom Field
- **Method:** DELETE
- **Endpoint:** `/custom_field/{code}/{id}`

---

### System Fields

#### 1. Get All System Fields
- **Method:** GET
- **Endpoint:** `/system_field/{code}`
- **Description:** Retrieve system-defined fields (priority, severity, type, behavior, automation, status)

---

### Projects

#### 1. Get All Projects
- **Method:** GET
- **Endpoint:** `/project`

#### 2. Create Project
- **Method:** POST
- **Endpoint:** `/project`
- **Payload:**
  - `title`: Project title
  - `code`: Project code (unique)
  - `description`: Project description
  - `access`: Access level

#### 3. Get Project by Code
- **Method:** GET
- **Endpoint:** `/project/{code}`

#### 4. Delete Project
- **Method:** DELETE
- **Endpoint:** `/project/{code}`

#### 5. Grant Access to Project
- **Method:** POST
- **Endpoint:** `/project/{code}/access`

#### 6. Revoke Access from Project
- **Method:** DELETE
- **Endpoint:** `/project/{code}/access`

---

### Defects

#### 1. Get All Defects
- **Method:** GET
- **Endpoint:** `/defect/{code}`

#### 2. Create Defect
- **Method:** POST
- **Endpoint:** `/defect/{code}`

#### 3. Get Specific Defect
- **Method:** GET
- **Endpoint:** `/defect/{code}/{id}`

#### 4. Update Defect
- **Method:** PATCH
- **Endpoint:** `/defect/{code}/{id}`

#### 5. Delete Defect
- **Method:** DELETE
- **Endpoint:** `/defect/{code}/{id}`

#### 6. Resolve Defect
- **Method:** PATCH
- **Endpoint:** `/defect/{code}/{id}/resolve`

#### 7. Update Defect Status
- **Method:** PATCH
- **Endpoint:** `/defect/{code}/{id}/status`

---

### Environments

#### 1. Get All Environments
- **Method:** GET
- **Endpoint:** `/environment/{code}`

#### 2. Create Environment
- **Method:** POST
- **Endpoint:** `/environment/{code}`

#### 3. Get Specific Environment
- **Method:** GET
- **Endpoint:** `/environment/{code}/{id}`

#### 4. Update Environment
- **Method:** PATCH
- **Endpoint:** `/environment/{code}/{id}`

#### 5. Delete Environment
- **Method:** DELETE
- **Endpoint:** `/environment/{code}/{id}`

---

### Milestones

#### 1. Get All Milestones
- **Method:** GET
- **Endpoint:** `/milestone/{code}`

#### 2. Create Milestone
- **Method:** POST
- **Endpoint:** `/milestone/{code}`

#### 3. Get Specific Milestone
- **Method:** GET
- **Endpoint:** `/milestone/{code}/{id}`

#### 4. Update Milestone
- **Method:** PATCH
- **Endpoint:** `/milestone/{code}/{id}`

#### 5. Delete Milestone
- **Method:** DELETE
- **Endpoint:** `/milestone/{code}/{id}`

---

### Configurations

#### 1. Get All Configuration Groups
- **Method:** GET
- **Endpoint:** `/configuration/{code}`

#### 2. Create Configuration
- **Method:** POST
- **Endpoint:** `/configuration/{code}`

#### 3. Create Configuration Group
- **Method:** POST
- **Endpoint:** `/configuration/{code}/group`

---

### Search

#### 1. Search by QQL (Qase Query Language)
- **Method:** GET
- **Endpoint:** `/search/{code}`
- **Description:** Search entities using Qase Query Language

---

### Authors

#### 1. Get All Authors
- **Method:** GET
- **Endpoint:** `/author/{code}`

#### 2. Get Specific Author
- **Method:** GET
- **Endpoint:** `/author/{code}/{id}`

---

### Users

#### 1. Get All Users
- **Method:** GET
- **Endpoint:** `/user`

#### 2. Get Specific User
- **Method:** GET
- **Endpoint:** `/user/{id}`

---

## API v2 Information

Qase has introduced API v2, which is available at `https://api.qase.io/v2`

**Available Clients:**
- Python: `qase-api-v2-client`
- JavaScript/TypeScript: `qase-api-v2-client`
- PHP: Qase TestOps API V2 client
- Java, Go: Can be generated using OpenAPI Generator

**Key Endpoints (Beta):**
- Results API for creating test run results
- Enhanced performance and structure
- OpenAPI-generated clients available

**Installation Examples:**

Python:
```bash
pip install qase-api-v2-client
```

JavaScript/Node.js:
```bash
npm install qase-api-v2-client
# or
yarn add qase-api-v2-client
```

---

## Webhooks

Qase also supports webhooks for real-time notifications:

### Test Case Webhook Events

1. **case.created** - Triggered when a test case is created
2. **case.cloned** - Triggered when a test case is cloned
3. **case.updated** - Triggered when a test case is updated
4. **case.deleted** - Triggered when a test case is deleted

**Webhook Payload Example:**
```json
{
  "event_name": "case.created",
  "timestamp": 1650530190,
  "payload": {
    "id": 1610,
    "title": "Example test case",
    "description": "Description test case",
    "preconditions": "something",
    "postconditions": "something",
    "priority": {
      "id": 2,
      "title": "Medium",
      "icon": "genderless",
      "color": "medium"
    },
    "severity": {
      "id": 4,
      "title": "Normal",
      "icon": "genderless",
      "color": "normal"
    },
    "behavior": {
      "id": 2,
      "title": "Positive"
    },
    "type": {
      "id": 8,
      "title": "Functional"
    },
    "automation": {
      "id": 1,
      "title": "To be automated"
    },
    "status": {
      "id": 0,
      "title": "Actual"
    },
    "suite_id": 12,
    "milestone_id": null,
    "steps": [
      {
        "position": 1,
        "action": "simple action",
        "expected_result": "expected result",
        "data": "input data",
        "attachments": [],
        "shared": false
      }
    ],
    "attachments": [],
    "custom_fields": [
      {
        "id": 174,
        "title": "Test Number",
        "type": "number",
        "value": "1"
      }
    ]
  },
  "team_member_id": 40,
  "project_code": "ID"
}
```

---

## MCP Server Development Recommendations

### Essential Tools for Test Case Generation

1. **Core Test Case Operations:**
   - `qase_create_test_case` - Create single test case
   - `qase_create_bulk_test_cases` - Create multiple test cases
   - `qase_get_test_case` - Retrieve test case details
   - `qase_update_test_case` - Update existing test case
   - `qase_delete_test_case` - Delete test case
   - `qase_list_test_cases` - List/search test cases

2. **Suite Management:**
   - `qase_create_suite` - Organize test cases into suites
   - `qase_list_suites` - Browse suite structure
   - `qase_get_suite` - Get suite details

3. **Shared Components:**
   - `qase_create_shared_step` - Create reusable test steps
   - `qase_list_shared_steps` - Browse shared steps
   - `qase_create_shared_parameter` - Create reusable parameters

4. **Custom Fields:**
   - `qase_list_custom_fields` - Get available custom fields
   - `qase_create_custom_field` - Define new custom fields

5. **System Configuration:**
   - `qase_get_system_fields` - Get priority, severity, type options
   - `qase_list_projects` - Get available projects

### Suggested Tool Structure

```python
# Example MCP tool definition
{
  "name": "qase_create_test_case",
  "description": "Create a new test case in Qase",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_code": {"type": "string"},
      "title": {"type": "string"},
      "description": {"type": "string"},
      "suite_id": {"type": "integer"},
      "steps": {"type": "array"},
      "priority": {"type": "integer"},
      "severity": {"type": "integer"}
    },
    "required": ["project_code", "title"]
  }
}
```

### Key Considerations

1. **Error Handling:** Implement retry logic for rate limits (429 responses)
2. **Batch Operations:** Use bulk endpoints when creating multiple test cases
3. **Validation:** Validate project codes and IDs before API calls
4. **Caching:** Cache system fields, custom fields to reduce API calls
5. **Webhooks:** Consider implementing webhook listeners for real-time updates

---

## Additional Resources

- **API Reference:** https://developers.qase.io/reference
- **API v2 Documentation:** https://developers.qase.io/v2.0/docs
- **Postman Collection:** https://www.postman.com/qaseio?tab=collections
- **GitHub Clients:**
  - JavaScript: https://github.com/qase-tms/qase-javascript
  - Python: https://pypi.org/project/qase-api-v2-client/
  - PHP: https://github.com/qase-tms/qase-api-v2-client
  - .NET: https://github.com/qase-tms/qase-net-api

---

## Notes for MCP Development

- All endpoints require authentication via API token
- Use `{code}` as the project code parameter in URLs
- IDs are integers; hashes are strings
- Rate limiting applies across all endpoints
- Consider implementing connection pooling for efficiency
- v2 API is recommended for new implementations (better performance)
- Webhook support available for event-driven architectures
