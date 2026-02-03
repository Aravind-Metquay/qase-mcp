"""
Qase MCP Server - A Model Context Protocol server for Qase Test Management Platform

This MCP server provides tools for interacting with the Qase API for test case
generation and management.
"""

import os
import asyncio
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("qase")

# Configuration
QASE_API_BASE_URL = "https://api.qase.io/v1"
QASE_API_TOKEN = os.environ.get("QASE_API_TOKEN", "")

# Rate limit retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds


async def make_request(
    method: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
    retries: int = 0,
) -> dict[str, Any]:
    """Make an authenticated request to the Qase API with retry logic for rate limits."""
    if not QASE_API_TOKEN:
        return {"error": "QASE_API_TOKEN environment variable is not set"}

    url = f"{QASE_API_BASE_URL}{endpoint}"
    headers = {
        "Token": QASE_API_TOKEN,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=30.0,
            )

            # Handle rate limiting
            if response.status_code == 429:
                if retries < MAX_RETRIES:
                    retry_after = int(response.headers.get("Retry-After", RETRY_DELAY))
                    await asyncio.sleep(retry_after)
                    return await make_request(
                        method, endpoint, params, json_data, retries + 1
                    )
                return {"error": "Rate limit exceeded after maximum retries"}

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


# ============================================================================
# PROJECT TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_projects(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all projects in Qase.

    Args:
        limit: Maximum number of projects to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of projects with their codes, titles, and details
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", "/project", params=params)


@mcp.tool()
async def qase_get_project(project_code: str) -> dict[str, Any]:
    """
    Get details of a specific project.

    Args:
        project_code: The unique code of the project

    Returns:
        Project details including title, description, and settings
    """
    return await make_request("GET", f"/project/{project_code}")


@mcp.tool()
async def qase_create_project(
    title: str,
    code: str,
    description: str = "",
    access: str = "none",
) -> dict[str, Any]:
    """
    Create a new project in Qase.

    Args:
        title: Project title
        code: Unique project code (uppercase letters and numbers)
        description: Project description (optional)
        access: Access level - "none", "group", "all" (default: "none")

    Returns:
        Created project details
    """
    data = {
        "title": title,
        "code": code,
        "description": description,
        "access": access,
    }
    return await make_request("POST", "/project", json_data=data)


# ============================================================================
# TEST CASE TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_test_cases(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
    filters_priority: str | None = None,
    filters_type: str | None = None,
    filters_severity: str | None = None,
    filters_automation: str | None = None,
    filters_suite_id: int | None = None,
    filters_search: str | None = None,
) -> dict[str, Any]:
    """
    List all test cases in a project with optional filters.

    Args:
        project_code: The project code
        limit: Maximum number of test cases to return (default: 100)
        offset: Pagination offset (default: 0)
        filters_priority: Filter by priority (comma-separated, e.g., "high,low")
        filters_type: Filter by test type
        filters_severity: Filter by severity
        filters_automation: Filter by automation status
        filters_suite_id: Filter by suite ID
        filters_search: Search in test case title

    Returns:
        List of test cases matching the criteria
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if filters_priority:
        params["filters[priority]"] = filters_priority
    if filters_type:
        params["filters[type]"] = filters_type
    if filters_severity:
        params["filters[severity]"] = filters_severity
    if filters_automation:
        params["filters[automation]"] = filters_automation
    if filters_suite_id:
        params["filters[suite_id]"] = filters_suite_id
    if filters_search:
        params["filters[search]"] = filters_search

    return await make_request("GET", f"/case/{project_code}", params=params)


@mcp.tool()
async def qase_get_test_case(
    project_code: str,
    case_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific test case.

    Args:
        project_code: The project code
        case_id: The test case ID

    Returns:
        Test case details including title, steps, and metadata
    """
    return await make_request("GET", f"/case/{project_code}/{case_id}")


@mcp.tool()
async def qase_create_test_case(
    project_code: str,
    title: str,
    description: str = "",
    preconditions: str = "",
    postconditions: str = "",
    severity: int = 4,
    priority: int = 2,
    type_id: int = 1,
    behavior: int = 2,
    automation: str = "is-not-automated",
    suite_id: int | None = None,
    milestone_id: int | None = None,
    tags: list[str] | None = None,
    steps: list[dict[str, Any]] | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Create a new test case in a project.

    Args:
        project_code: The project code
        title: Test case title (required)
        description: Test case description
        preconditions: Preconditions for test execution
        postconditions: Postconditions after test execution
        severity: Severity level (1=blocker, 2=critical, 3=major, 4=normal, 5=minor, 6=trivial)
        priority: Priority level (1=high, 2=medium, 3=low)
        type_id: Test type ID
        behavior: Behavior type (1=undefined, 2=positive, 3=negative, 4=destructive)
        automation: Automation status ("is-not-automated", "to-be-automated", "automated")
        suite_id: Suite ID to place the test case in
        milestone_id: Milestone ID
        tags: List of tags
        steps: List of test steps, each with "action", "expected_result", "data", "position"
        custom_fields: List of custom field objects with "id" and "value"

    Returns:
        Created test case ID
    """
    data: dict[str, Any] = {
        "title": title,
        "description": description,
        "preconditions": preconditions,
        "postconditions": postconditions,
        "severity": severity,
        "priority": priority,
        "type": type_id,
        "behavior": behavior,
        "automation": automation,
    }

    if suite_id is not None:
        data["suite_id"] = suite_id
    if milestone_id is not None:
        data["milestone_id"] = milestone_id
    if tags:
        data["tags"] = tags
    if steps:
        data["steps"] = steps
    if custom_fields:
        data["custom_fields"] = custom_fields

    return await make_request("POST", f"/case/{project_code}", json_data=data)


@mcp.tool()
async def qase_create_bulk_test_cases(
    project_code: str,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create multiple test cases at once.

    Args:
        project_code: The project code
        cases: List of test case objects, each containing at minimum "title"
               and optionally: description, preconditions, postconditions,
               severity, priority, type, behavior, automation, suite_id,
               milestone_id, tags, steps, custom_fields

    Returns:
        List of created test case IDs
    """
    data = {"cases": cases}
    return await make_request("POST", f"/case/{project_code}/bulk", json_data=data)


@mcp.tool()
async def qase_update_test_case(
    project_code: str,
    case_id: int,
    title: str | None = None,
    description: str | None = None,
    preconditions: str | None = None,
    postconditions: str | None = None,
    severity: int | None = None,
    priority: int | None = None,
    type_id: int | None = None,
    behavior: int | None = None,
    automation: str | None = None,
    suite_id: int | None = None,
    milestone_id: int | None = None,
    tags: list[str] | None = None,
    steps: list[dict[str, Any]] | None = None,
    custom_fields: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Update an existing test case.

    Args:
        project_code: The project code
        case_id: The test case ID to update
        title: New test case title
        description: New description
        preconditions: New preconditions
        postconditions: New postconditions
        severity: New severity level (1-6)
        priority: New priority level (1-3)
        type_id: New test type ID
        behavior: New behavior type (1-4)
        automation: New automation status
        suite_id: New suite ID
        milestone_id: New milestone ID
        tags: New list of tags
        steps: New list of test steps
        custom_fields: New custom field values

    Returns:
        Updated test case ID
    """
    data: dict[str, Any] = {}

    if title is not None:
        data["title"] = title
    if description is not None:
        data["description"] = description
    if preconditions is not None:
        data["preconditions"] = preconditions
    if postconditions is not None:
        data["postconditions"] = postconditions
    if severity is not None:
        data["severity"] = severity
    if priority is not None:
        data["priority"] = priority
    if type_id is not None:
        data["type"] = type_id
    if behavior is not None:
        data["behavior"] = behavior
    if automation is not None:
        data["automation"] = automation
    if suite_id is not None:
        data["suite_id"] = suite_id
    if milestone_id is not None:
        data["milestone_id"] = milestone_id
    if tags is not None:
        data["tags"] = tags
    if steps is not None:
        data["steps"] = steps
    if custom_fields is not None:
        data["custom_fields"] = custom_fields

    return await make_request("PATCH", f"/case/{project_code}/{case_id}", json_data=data)


@mcp.tool()
async def qase_delete_test_case(
    project_code: str,
    case_id: int,
) -> dict[str, Any]:
    """
    Delete a test case from a project.

    Args:
        project_code: The project code
        case_id: The test case ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/case/{project_code}/{case_id}")


# ============================================================================
# TEST SUITE TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_suites(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> dict[str, Any]:
    """
    List all test suites in a project.

    Args:
        project_code: The project code
        limit: Maximum number of suites to return (default: 100)
        offset: Pagination offset (default: 0)
        search: Search filter for suite title

    Returns:
        List of test suites
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if search:
        params["filters[search]"] = search

    return await make_request("GET", f"/suite/{project_code}", params=params)


@mcp.tool()
async def qase_get_suite(
    project_code: str,
    suite_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific test suite.

    Args:
        project_code: The project code
        suite_id: The suite ID

    Returns:
        Suite details including title, description, and parent info
    """
    return await make_request("GET", f"/suite/{project_code}/{suite_id}")


@mcp.tool()
async def qase_create_suite(
    project_code: str,
    title: str,
    description: str = "",
    preconditions: str = "",
    parent_id: int | None = None,
) -> dict[str, Any]:
    """
    Create a new test suite in a project.

    Args:
        project_code: The project code
        title: Suite title (required)
        description: Suite description
        preconditions: Suite preconditions
        parent_id: Parent suite ID for nested suites

    Returns:
        Created suite ID
    """
    data: dict[str, Any] = {
        "title": title,
        "description": description,
        "preconditions": preconditions,
    }

    if parent_id is not None:
        data["parent_id"] = parent_id

    return await make_request("POST", f"/suite/{project_code}", json_data=data)


@mcp.tool()
async def qase_update_suite(
    project_code: str,
    suite_id: int,
    title: str | None = None,
    description: str | None = None,
    preconditions: str | None = None,
    parent_id: int | None = None,
) -> dict[str, Any]:
    """
    Update an existing test suite.

    Args:
        project_code: The project code
        suite_id: The suite ID to update
        title: New suite title
        description: New description
        preconditions: New preconditions
        parent_id: New parent suite ID

    Returns:
        Updated suite ID
    """
    data: dict[str, Any] = {}

    if title is not None:
        data["title"] = title
    if description is not None:
        data["description"] = description
    if preconditions is not None:
        data["preconditions"] = preconditions
    if parent_id is not None:
        data["parent_id"] = parent_id

    return await make_request("PATCH", f"/suite/{project_code}/{suite_id}", json_data=data)


@mcp.tool()
async def qase_delete_suite(
    project_code: str,
    suite_id: int,
) -> dict[str, Any]:
    """
    Delete a test suite from a project.

    Args:
        project_code: The project code
        suite_id: The suite ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/suite/{project_code}/{suite_id}")


# ============================================================================
# SHARED STEPS TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_shared_steps(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
    search: str | None = None,
) -> dict[str, Any]:
    """
    List all shared steps in a project.

    Args:
        project_code: The project code
        limit: Maximum number of shared steps to return (default: 100)
        offset: Pagination offset (default: 0)
        search: Search filter for shared step title

    Returns:
        List of shared steps
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if search:
        params["filters[search]"] = search

    return await make_request("GET", f"/shared_step/{project_code}", params=params)


@mcp.tool()
async def qase_get_shared_step(
    project_code: str,
    shared_step_hash: str,
) -> dict[str, Any]:
    """
    Get details of a specific shared step.

    Args:
        project_code: The project code
        shared_step_hash: The shared step hash identifier

    Returns:
        Shared step details
    """
    return await make_request("GET", f"/shared_step/{project_code}/{shared_step_hash}")


@mcp.tool()
async def qase_create_shared_step(
    project_code: str,
    title: str,
    action: str,
    expected_result: str = "",
    data: str = "",
) -> dict[str, Any]:
    """
    Create a new shared step in a project.

    Args:
        project_code: The project code
        title: Shared step title
        action: The action to perform
        expected_result: Expected result of the action
        data: Input data for the step

    Returns:
        Created shared step hash
    """
    step_data = {
        "title": title,
        "action": action,
        "expected_result": expected_result,
        "data": data,
    }
    return await make_request("POST", f"/shared_step/{project_code}", json_data=step_data)


@mcp.tool()
async def qase_update_shared_step(
    project_code: str,
    shared_step_hash: str,
    title: str | None = None,
    action: str | None = None,
    expected_result: str | None = None,
    data: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing shared step.

    Args:
        project_code: The project code
        shared_step_hash: The shared step hash to update
        title: New title
        action: New action
        expected_result: New expected result
        data: New input data

    Returns:
        Updated shared step hash
    """
    step_data: dict[str, Any] = {}

    if title is not None:
        step_data["title"] = title
    if action is not None:
        step_data["action"] = action
    if expected_result is not None:
        step_data["expected_result"] = expected_result
    if data is not None:
        step_data["data"] = data

    return await make_request(
        "PATCH", f"/shared_step/{project_code}/{shared_step_hash}", json_data=step_data
    )


@mcp.tool()
async def qase_delete_shared_step(
    project_code: str,
    shared_step_hash: str,
) -> dict[str, Any]:
    """
    Delete a shared step from a project.
    Note: This removes the shared step from all test cases using it.

    Args:
        project_code: The project code
        shared_step_hash: The shared step hash to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/shared_step/{project_code}/{shared_step_hash}")


# ============================================================================
# SHARED PARAMETERS TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_shared_parameters(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all shared parameters in a project.

    Args:
        project_code: The project code
        limit: Maximum number of parameters to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of shared parameters
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/shared_parameter/{project_code}", params=params)


@mcp.tool()
async def qase_get_shared_parameter(
    project_code: str,
    parameter_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific shared parameter.

    Args:
        project_code: The project code
        parameter_id: The shared parameter ID

    Returns:
        Shared parameter details
    """
    return await make_request("GET", f"/shared_parameter/{project_code}/{parameter_id}")


@mcp.tool()
async def qase_create_shared_parameter(
    project_code: str,
    title: str,
    values: list[str],
) -> dict[str, Any]:
    """
    Create a new shared parameter in a project.

    Args:
        project_code: The project code
        title: Parameter title
        values: List of parameter values

    Returns:
        Created shared parameter ID
    """
    data = {
        "title": title,
        "values": values,
    }
    return await make_request("POST", f"/shared_parameter/{project_code}", json_data=data)


@mcp.tool()
async def qase_update_shared_parameter(
    project_code: str,
    parameter_id: int,
    title: str | None = None,
    values: list[str] | None = None,
) -> dict[str, Any]:
    """
    Update an existing shared parameter.

    Args:
        project_code: The project code
        parameter_id: The parameter ID to update
        title: New title
        values: New list of values

    Returns:
        Updated shared parameter ID
    """
    data: dict[str, Any] = {}

    if title is not None:
        data["title"] = title
    if values is not None:
        data["values"] = values

    return await make_request(
        "PATCH", f"/shared_parameter/{project_code}/{parameter_id}", json_data=data
    )


@mcp.tool()
async def qase_delete_shared_parameter(
    project_code: str,
    parameter_id: int,
) -> dict[str, Any]:
    """
    Delete a shared parameter from a project.

    Args:
        project_code: The project code
        parameter_id: The parameter ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/shared_parameter/{project_code}/{parameter_id}")


# ============================================================================
# CUSTOM FIELDS TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_custom_fields(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all custom fields in a project.

    Args:
        project_code: The project code
        limit: Maximum number of custom fields to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of custom fields with their types and configurations
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/custom_field/{project_code}", params=params)


@mcp.tool()
async def qase_get_custom_field(
    project_code: str,
    field_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific custom field.

    Args:
        project_code: The project code
        field_id: The custom field ID

    Returns:
        Custom field details
    """
    return await make_request("GET", f"/custom_field/{project_code}/{field_id}")


@mcp.tool()
async def qase_create_custom_field(
    project_code: str,
    title: str,
    entity: int,
    field_type: int,
    placeholder: str = "",
    default_value: str = "",
    is_filterable: bool = False,
    is_visible: bool = True,
    is_required: bool = False,
    value: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Create a new custom field in a project.

    Args:
        project_code: The project code
        title: Field title
        entity: Entity type (0=case, 1=run, 2=defect)
        field_type: Field type (0=number, 1=string, 2=text, 3=selectbox, 4=checkbox, 5=radio, 6=multiselect, 7=url, 8=user, 9=datetime)
        placeholder: Placeholder text
        default_value: Default value
        is_filterable: Whether field is filterable
        is_visible: Whether field is visible
        is_required: Whether field is required
        value: For selectbox/radio/multiselect types, list of options with "title"

    Returns:
        Created custom field ID
    """
    data: dict[str, Any] = {
        "title": title,
        "entity": entity,
        "type": field_type,
        "placeholder": placeholder,
        "default_value": default_value,
        "is_filterable": is_filterable,
        "is_visible": is_visible,
        "is_required": is_required,
    }

    if value is not None:
        data["value"] = value

    return await make_request("POST", f"/custom_field/{project_code}", json_data=data)


@mcp.tool()
async def qase_update_custom_field(
    project_code: str,
    field_id: int,
    title: str | None = None,
    placeholder: str | None = None,
    default_value: str | None = None,
    is_filterable: bool | None = None,
    is_visible: bool | None = None,
    is_required: bool | None = None,
    value: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Update an existing custom field.

    Args:
        project_code: The project code
        field_id: The custom field ID to update
        title: New title
        placeholder: New placeholder
        default_value: New default value
        is_filterable: New filterable setting
        is_visible: New visibility setting
        is_required: New required setting
        value: New list of options (for selectbox/radio/multiselect)

    Returns:
        Updated custom field ID
    """
    data: dict[str, Any] = {}

    if title is not None:
        data["title"] = title
    if placeholder is not None:
        data["placeholder"] = placeholder
    if default_value is not None:
        data["default_value"] = default_value
    if is_filterable is not None:
        data["is_filterable"] = is_filterable
    if is_visible is not None:
        data["is_visible"] = is_visible
    if is_required is not None:
        data["is_required"] = is_required
    if value is not None:
        data["value"] = value

    return await make_request(
        "PATCH", f"/custom_field/{project_code}/{field_id}", json_data=data
    )


@mcp.tool()
async def qase_delete_custom_field(
    project_code: str,
    field_id: int,
) -> dict[str, Any]:
    """
    Delete a custom field from a project.

    Args:
        project_code: The project code
        field_id: The custom field ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/custom_field/{project_code}/{field_id}")


# ============================================================================
# SYSTEM FIELDS TOOLS
# ============================================================================


@mcp.tool()
async def qase_get_system_fields(project_code: str) -> dict[str, Any]:
    """
    Get all system-defined fields for a project.
    Returns fields like priority, severity, type, behavior, automation status.

    Args:
        project_code: The project code

    Returns:
        System fields with their possible values and configurations
    """
    return await make_request("GET", f"/system_field/{project_code}")


# ============================================================================
# TEST PLAN TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_test_plans(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all test plans in a project.

    Args:
        project_code: The project code
        limit: Maximum number of plans to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of test plans
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/plan/{project_code}", params=params)


@mcp.tool()
async def qase_get_test_plan(
    project_code: str,
    plan_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific test plan.

    Args:
        project_code: The project code
        plan_id: The test plan ID

    Returns:
        Test plan details including test cases and assignees
    """
    return await make_request("GET", f"/plan/{project_code}/{plan_id}")


@mcp.tool()
async def qase_create_test_plan(
    project_code: str,
    title: str,
    description: str = "",
    cases: list[int] | None = None,
) -> dict[str, Any]:
    """
    Create a new test plan in a project.

    Args:
        project_code: The project code
        title: Plan title
        description: Plan description
        cases: List of test case IDs to include in the plan

    Returns:
        Created test plan ID
    """
    data: dict[str, Any] = {
        "title": title,
        "description": description,
    }

    if cases:
        data["cases"] = cases

    return await make_request("POST", f"/plan/{project_code}", json_data=data)


@mcp.tool()
async def qase_update_test_plan(
    project_code: str,
    plan_id: int,
    title: str | None = None,
    description: str | None = None,
    cases: list[int] | None = None,
) -> dict[str, Any]:
    """
    Update an existing test plan.

    Args:
        project_code: The project code
        plan_id: The test plan ID to update
        title: New title
        description: New description
        cases: New list of test case IDs

    Returns:
        Updated test plan ID
    """
    data: dict[str, Any] = {}

    if title is not None:
        data["title"] = title
    if description is not None:
        data["description"] = description
    if cases is not None:
        data["cases"] = cases

    return await make_request("PATCH", f"/plan/{project_code}/{plan_id}", json_data=data)


@mcp.tool()
async def qase_delete_test_plan(
    project_code: str,
    plan_id: int,
) -> dict[str, Any]:
    """
    Delete a test plan from a project.

    Args:
        project_code: The project code
        plan_id: The test plan ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/plan/{project_code}/{plan_id}")


# ============================================================================
# TEST RUN TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_test_runs(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
    include: str | None = None,
) -> dict[str, Any]:
    """
    List all test runs in a project.

    Args:
        project_code: The project code
        limit: Maximum number of runs to return (default: 100)
        offset: Pagination offset (default: 0)
        include: Comma-separated list of additional entities to include (e.g., "cases")

    Returns:
        List of test runs
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if include:
        params["include"] = include

    return await make_request("GET", f"/run/{project_code}", params=params)


@mcp.tool()
async def qase_get_test_run(
    project_code: str,
    run_id: int,
    include: str | None = None,
) -> dict[str, Any]:
    """
    Get details of a specific test run.

    Args:
        project_code: The project code
        run_id: The test run ID
        include: Comma-separated list of additional entities to include

    Returns:
        Test run details
    """
    params: dict[str, Any] = {}
    if include:
        params["include"] = include

    return await make_request("GET", f"/run/{project_code}/{run_id}", params=params)


@mcp.tool()
async def qase_create_test_run(
    project_code: str,
    title: str,
    description: str = "",
    cases: list[int] | None = None,
    plan_id: int | None = None,
    environment_id: int | None = None,
    milestone_id: int | None = None,
    is_autotest: bool = False,
) -> dict[str, Any]:
    """
    Create a new test run in a project.

    Args:
        project_code: The project code
        title: Run title
        description: Run description
        cases: List of test case IDs to include
        plan_id: Test plan ID to run
        environment_id: Environment ID
        milestone_id: Milestone ID
        is_autotest: Whether this is an automated test run

    Returns:
        Created test run ID
    """
    data: dict[str, Any] = {
        "title": title,
        "description": description,
        "is_autotest": is_autotest,
    }

    if cases:
        data["cases"] = cases
    if plan_id is not None:
        data["plan_id"] = plan_id
    if environment_id is not None:
        data["environment_id"] = environment_id
    if milestone_id is not None:
        data["milestone_id"] = milestone_id

    return await make_request("POST", f"/run/{project_code}", json_data=data)


@mcp.tool()
async def qase_complete_test_run(
    project_code: str,
    run_id: int,
) -> dict[str, Any]:
    """
    Complete/close a test run.

    Args:
        project_code: The project code
        run_id: The test run ID to complete

    Returns:
        Completion confirmation
    """
    return await make_request("POST", f"/run/{project_code}/{run_id}/complete")


@mcp.tool()
async def qase_delete_test_run(
    project_code: str,
    run_id: int,
) -> dict[str, Any]:
    """
    Delete a test run from a project.

    Args:
        project_code: The project code
        run_id: The test run ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/run/{project_code}/{run_id}")


# ============================================================================
# TEST RESULT TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_test_results(
    project_code: str,
    run_id: int,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all test results in a test run.

    Args:
        project_code: The project code
        run_id: The test run ID
        limit: Maximum number of results to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of test results
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/result/{project_code}/{run_id}", params=params)


@mcp.tool()
async def qase_get_test_result(
    project_code: str,
    run_id: int,
    result_hash: str,
) -> dict[str, Any]:
    """
    Get details of a specific test result.

    Args:
        project_code: The project code
        run_id: The test run ID
        result_hash: The result hash identifier

    Returns:
        Test result details
    """
    return await make_request("GET", f"/result/{project_code}/{run_id}/{result_hash}")


@mcp.tool()
async def qase_create_test_result(
    project_code: str,
    run_id: int,
    case_id: int,
    status: str,
    time_ms: int | None = None,
    comment: str = "",
    defect: bool = False,
    member_id: int | None = None,
    steps: list[dict[str, Any]] | None = None,
    attachments: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a test result for a test case in a run.

    Args:
        project_code: The project code
        run_id: The test run ID
        case_id: The test case ID
        status: Result status ("passed", "failed", "blocked", "skipped", "invalid")
        time_ms: Execution time in milliseconds
        comment: Result comment
        defect: Whether the result has a defect
        member_id: Assignee member ID
        steps: List of step results with "position", "status", "comment"
        attachments: List of attachment hashes

    Returns:
        Created test result hash
    """
    data: dict[str, Any] = {
        "case_id": case_id,
        "status": status,
        "comment": comment,
        "defect": defect,
    }

    if time_ms is not None:
        data["time_ms"] = time_ms
    if member_id is not None:
        data["member_id"] = member_id
    if steps:
        data["steps"] = steps
    if attachments:
        data["attachments"] = attachments

    return await make_request("POST", f"/result/{project_code}/{run_id}", json_data=data)


@mcp.tool()
async def qase_create_bulk_test_results(
    project_code: str,
    run_id: int,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create multiple test results at once.

    Args:
        project_code: The project code
        run_id: The test run ID
        results: List of result objects, each with "case_id", "status", and optional
                 "time_ms", "comment", "defect", "member_id", "steps", "attachments"

    Returns:
        List of created result hashes
    """
    data = {"results": results}
    return await make_request("POST", f"/result/{project_code}/{run_id}/bulk", json_data=data)


# ============================================================================
# DEFECT TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_defects(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
    filters_status: str | None = None,
) -> dict[str, Any]:
    """
    List all defects in a project.

    Args:
        project_code: The project code
        limit: Maximum number of defects to return (default: 100)
        offset: Pagination offset (default: 0)
        filters_status: Filter by status ("open", "resolved", "in_progress")

    Returns:
        List of defects
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if filters_status:
        params["filters[status]"] = filters_status

    return await make_request("GET", f"/defect/{project_code}", params=params)


@mcp.tool()
async def qase_get_defect(
    project_code: str,
    defect_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific defect.

    Args:
        project_code: The project code
        defect_id: The defect ID

    Returns:
        Defect details
    """
    return await make_request("GET", f"/defect/{project_code}/{defect_id}")


@mcp.tool()
async def qase_create_defect(
    project_code: str,
    title: str,
    actual_result: str,
    severity: int = 4,
    member_id: int | None = None,
    milestone_id: int | None = None,
    attachments: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a new defect in a project.

    Args:
        project_code: The project code
        title: Defect title
        actual_result: Actual result/description of the defect
        severity: Severity level (1-6)
        member_id: Assigned member ID
        milestone_id: Milestone ID
        attachments: List of attachment hashes

    Returns:
        Created defect ID
    """
    data: dict[str, Any] = {
        "title": title,
        "actual_result": actual_result,
        "severity": severity,
    }

    if member_id is not None:
        data["member_id"] = member_id
    if milestone_id is not None:
        data["milestone_id"] = milestone_id
    if attachments:
        data["attachments"] = attachments

    return await make_request("POST", f"/defect/{project_code}", json_data=data)


@mcp.tool()
async def qase_resolve_defect(
    project_code: str,
    defect_id: int,
) -> dict[str, Any]:
    """
    Mark a defect as resolved.

    Args:
        project_code: The project code
        defect_id: The defect ID to resolve

    Returns:
        Resolution confirmation
    """
    return await make_request("PATCH", f"/defect/{project_code}/{defect_id}/resolve")


@mcp.tool()
async def qase_delete_defect(
    project_code: str,
    defect_id: int,
) -> dict[str, Any]:
    """
    Delete a defect from a project.

    Args:
        project_code: The project code
        defect_id: The defect ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/defect/{project_code}/{defect_id}")


# ============================================================================
# ENVIRONMENT TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_environments(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all environments in a project.

    Args:
        project_code: The project code
        limit: Maximum number of environments to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of environments
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/environment/{project_code}", params=params)


@mcp.tool()
async def qase_get_environment(
    project_code: str,
    environment_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific environment.

    Args:
        project_code: The project code
        environment_id: The environment ID

    Returns:
        Environment details
    """
    return await make_request("GET", f"/environment/{project_code}/{environment_id}")


@mcp.tool()
async def qase_create_environment(
    project_code: str,
    title: str,
    description: str = "",
    slug: str = "",
    host: str = "",
) -> dict[str, Any]:
    """
    Create a new environment in a project.

    Args:
        project_code: The project code
        title: Environment title
        description: Environment description
        slug: Environment slug/identifier
        host: Host URL for the environment

    Returns:
        Created environment ID
    """
    data = {
        "title": title,
        "description": description,
        "slug": slug,
        "host": host,
    }
    return await make_request("POST", f"/environment/{project_code}", json_data=data)


@mcp.tool()
async def qase_delete_environment(
    project_code: str,
    environment_id: int,
) -> dict[str, Any]:
    """
    Delete an environment from a project.

    Args:
        project_code: The project code
        environment_id: The environment ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/environment/{project_code}/{environment_id}")


# ============================================================================
# MILESTONE TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_milestones(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all milestones in a project.

    Args:
        project_code: The project code
        limit: Maximum number of milestones to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of milestones
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/milestone/{project_code}", params=params)


@mcp.tool()
async def qase_get_milestone(
    project_code: str,
    milestone_id: int,
) -> dict[str, Any]:
    """
    Get details of a specific milestone.

    Args:
        project_code: The project code
        milestone_id: The milestone ID

    Returns:
        Milestone details
    """
    return await make_request("GET", f"/milestone/{project_code}/{milestone_id}")


@mcp.tool()
async def qase_create_milestone(
    project_code: str,
    title: str,
    description: str = "",
    status: str = "active",
    due_date: str | None = None,
) -> dict[str, Any]:
    """
    Create a new milestone in a project.

    Args:
        project_code: The project code
        title: Milestone title
        description: Milestone description
        status: Status ("active", "completed")
        due_date: Due date in ISO format (YYYY-MM-DD)

    Returns:
        Created milestone ID
    """
    data: dict[str, Any] = {
        "title": title,
        "description": description,
        "status": status,
    }

    if due_date:
        data["due_date"] = due_date

    return await make_request("POST", f"/milestone/{project_code}", json_data=data)


@mcp.tool()
async def qase_delete_milestone(
    project_code: str,
    milestone_id: int,
) -> dict[str, Any]:
    """
    Delete a milestone from a project.

    Args:
        project_code: The project code
        milestone_id: The milestone ID to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/milestone/{project_code}/{milestone_id}")


# ============================================================================
# AUTHOR/USER TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_authors(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all authors in a project.

    Args:
        project_code: The project code
        limit: Maximum number of authors to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of authors
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/author/{project_code}", params=params)


@mcp.tool()
async def qase_list_users(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all users in the organization.

    Args:
        limit: Maximum number of users to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of users
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", "/user", params=params)


@mcp.tool()
async def qase_get_user(user_id: int) -> dict[str, Any]:
    """
    Get details of a specific user.

    Args:
        user_id: The user ID

    Returns:
        User details
    """
    return await make_request("GET", f"/user/{user_id}")


# ============================================================================
# SEARCH TOOLS
# ============================================================================


@mcp.tool()
async def qase_search(
    project_code: str,
    query: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search entities using Qase Query Language (QQL).

    Args:
        project_code: The project code
        query: QQL query string (e.g., "priority = high AND automation = automated")
        limit: Maximum number of results to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        Search results
    """
    params = {
        "query": query,
        "limit": limit,
        "offset": offset,
    }
    return await make_request("GET", f"/search/{project_code}", params=params)


# ============================================================================
# ATTACHMENT TOOLS
# ============================================================================


@mcp.tool()
async def qase_list_attachments(
    project_code: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all attachments in a project.

    Args:
        project_code: The project code
        limit: Maximum number of attachments to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of attachments
    """
    params = {"limit": limit, "offset": offset}
    return await make_request("GET", f"/attachment/{project_code}", params=params)


@mcp.tool()
async def qase_get_attachment(
    project_code: str,
    attachment_hash: str,
) -> dict[str, Any]:
    """
    Get details of a specific attachment.

    Args:
        project_code: The project code
        attachment_hash: The attachment hash identifier

    Returns:
        Attachment details including download URL
    """
    return await make_request("GET", f"/attachment/{project_code}/{attachment_hash}")


@mcp.tool()
async def qase_delete_attachment(
    project_code: str,
    attachment_hash: str,
) -> dict[str, Any]:
    """
    Delete an attachment from a project.

    Args:
        project_code: The project code
        attachment_hash: The attachment hash to delete

    Returns:
        Deletion confirmation
    """
    return await make_request("DELETE", f"/attachment/{project_code}/{attachment_hash}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Run the Qase MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
