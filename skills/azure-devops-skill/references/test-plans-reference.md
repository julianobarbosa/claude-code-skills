# Test Plans API Reference

Comprehensive reference for Azure DevOps Test Plans REST API operations.

## Table of Contents

- [Test Plan Hierarchy](#test-plan-hierarchy)
- [Test Case Management](#test-case-management)
- [Test Runs and Results](#test-runs-and-results)
- [Test Configurations](#test-configurations)
- [Test Points](#test-points)

---

## Test Plan Hierarchy

### Structure

```
Test Plan
    └── Test Suite (Root)
        ├── Test Suite (Static)
        │   └── Test Cases
        ├── Test Suite (Requirements-based)
        │   └── Test Cases (auto-linked)
        └── Test Suite (Query-based)
            └── Test Cases (dynamic)
```

### Test Suite Types

| Type | ID | Description |
|------|----|-----------|
| Static | `staticTestSuite` | Manual hierarchy of test cases |
| Requirements-based | `requirementTestSuite` | Linked to a requirement work item |
| Query-based | `dynamicTestSuite` | Test cases from WIQL query |

### Test Plan States

| State | Description |
|-------|-------------|
| `active` | Currently active plan |
| `inactive` | Archived/completed plan |

---

## Test Case Management

### Test Case Fields

| Field | Reference Name | Description |
|-------|----------------|-------------|
| ID | `System.Id` | Unique identifier |
| Title | `System.Title` | Test case name |
| State | `System.State` | Design/Ready/Closed |
| Priority | `Microsoft.VSTS.Common.Priority` | Priority (1-4) |
| Steps | `Microsoft.VSTS.TCM.Steps` | Test steps XML |
| Expected Result | (in steps) | Expected outcomes |
| Automated | `Microsoft.VSTS.TCM.AutomationStatus` | Automation status |
| Automation Test | `Microsoft.VSTS.TCM.AutomatedTestName` | Automated test name |
| Test Suite | - | Parent suite(s) |
| Area Path | `System.AreaPath` | Area classification |
| Iteration Path | `System.IterationPath` | Iteration |
| Parameters | - | Shared parameters |
| Local Data Source | `Microsoft.VSTS.TCM.LocalDataSource` | Data-driven source |

### Test Steps Format

```
1. Step action|Expected result
2. Another step|Another expected result
3. Validate data|Data is correct
```

### Test Steps XML Structure

```xml
<steps id="0" last="3">
  <step id="1" type="ActionStep">
    <parameterizedString isFormatted="true">
      &lt;P&gt;Navigate to login page&lt;/P&gt;
    </parameterizedString>
    <parameterizedString isFormatted="true">
      &lt;P&gt;Login page is displayed&lt;/P&gt;
    </parameterizedString>
  </step>
  <step id="2" type="ActionStep">
    <parameterizedString isFormatted="true">
      &lt;P&gt;Enter username @username&lt;/P&gt;
    </parameterizedString>
    <parameterizedString isFormatted="true">
      &lt;P&gt;Username field populated&lt;/P&gt;
    </parameterizedString>
  </step>
</steps>
```

### Test Case States

| State | Description |
|-------|-------------|
| `Design` | Being designed |
| `Ready` | Ready for execution |
| `Closed` | Completed/obsolete |

### Automation Status

| Status | Description |
|--------|-------------|
| `Not Automated` | Manual test |
| `Planned` | Automation planned |
| `Automated` | Has associated automated test |

---

## Test Runs and Results

### Test Run States

| State | Description |
|-------|-------------|
| `Unspecified` | Not specified |
| `NotStarted` | Not yet started |
| `InProgress` | Currently running |
| `Completed` | Finished |
| `Aborted` | Was aborted |
| `Waiting` | Waiting for resources |
| `NeedsInvestigation` | Requires investigation |

### Test Run Types

| Type | Description |
|------|-------------|
| `Manual` | Manual test execution |
| `Automated` | Automated test run |
| `NoConfigRun` | Run without configuration |

### Test Outcome Values

| Outcome | ID | Description |
|---------|----|-----------|
| None | `0` | No outcome |
| Passed | `2` | Test passed |
| Failed | `3` | Test failed |
| Inconclusive | `4` | No clear result |
| Timeout | `5` | Timed out |
| Aborted | `6` | Was aborted |
| Blocked | `7` | Could not execute |
| NotExecuted | `8` | Not run |
| Warning | `9` | Passed with warnings |
| Error | `10` | Error during execution |
| NotApplicable | `11` | Not applicable |
| Paused | `12` | Execution paused |
| InProgress | `13` | Currently running |
| NotImpacted | `14` | Not impacted by changes |

### Test Result Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | Int | Result ID |
| `testCaseTitle` | String | Test case name |
| `outcome` | String | Pass/Fail/etc. |
| `state` | String | Result state |
| `durationInMs` | Long | Execution time |
| `errorMessage` | String | Error if failed |
| `stackTrace` | String | Stack trace |
| `comment` | String | Tester comments |
| `runBy` | Identity | Who ran the test |
| `completedDate` | DateTime | Completion time |
| `configuration` | Object | Test configuration |
| `build` | Object | Associated build |
| `release` | Object | Associated release |

---

## Test Configurations

### Configuration Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | Int | Configuration ID |
| `name` | String | Configuration name |
| `description` | String | Description |
| `isDefault` | Boolean | Default configuration |
| `state` | String | Active/Inactive |
| `values` | Array | Variable values |

### Configuration Variables

```json
{
  "name": "Windows 11 Chrome",
  "description": "Test on Windows 11 with Chrome browser",
  "values": [
    {"name": "Operating System", "value": "Windows 11"},
    {"name": "Browser", "value": "Chrome"},
    {"name": "Browser Version", "value": "Latest"}
  ]
}
```

---

## Test Points

### Test Point Concept

A Test Point is the combination of:

- Test Case
- Test Configuration
- Test Suite

### Test Point Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | Int | Point ID |
| `testCase` | Object | Test case reference |
| `configuration` | Object | Configuration |
| `suite` | Object | Test suite |
| `assignedTo` | Identity | Assigned tester |
| `outcome` | String | Last outcome |
| `state` | String | Point state |
| `lastRunBuildNumber` | String | Last run build |
| `lastResultState` | String | Last result state |
| `lastTestRun` | Object | Last run reference |
| `lastResultDetails` | Object | Last result |

### Test Point Assignment

```json
{
  "id": 123,
  "testCase": {"id": 456},
  "configuration": {"id": 1},
  "assignedTo": {
    "displayName": "Test User",
    "uniqueName": "user@domain.com"
  }
}
```

---

## MCP Tool Usage Examples

### List Test Plans

```python
# Using mcp__ado__testplan_list_test_plans
params = {
    "project": "MyProject",
    "filterActivePlans": True,
    "includePlanDetails": True
}
```

### Create Test Plan

```python
# Using mcp__ado__testplan_create_test_plan
params = {
    "project": "MyProject",
    "name": "Q1 2024 Release Testing",
    "iteration": "MyProject\\Release 1.0",
    "areaPath": "MyProject\\Team A",
    "description": "Test plan for Q1 2024 release",
    "startDate": "2024-01-01",
    "endDate": "2024-03-31"
}
```

### Create Test Suite

```python
# Using mcp__ado__testplan_create_test_suite
params = {
    "project": "MyProject",
    "planId": 123,
    "parentSuiteId": 456,  # Root suite ID if top-level
    "name": "Login Feature Tests"
}
```

### Create Test Case

```python
# Using mcp__ado__testplan_create_test_case
params = {
    "project": "MyProject",
    "title": "Verify successful login with valid credentials",
    "priority": 1,
    "areaPath": "MyProject\\Team A",
    "iterationPath": "MyProject\\Sprint 1",
    "steps": """1. Navigate to login page|Login page is displayed
2. Enter valid username in the username field|Username is entered
3. Enter valid password in the password field|Password is masked and entered
4. Click the Login button|User is redirected to dashboard
5. Verify user name is displayed|User's name appears in header""",
    "testsWorkItemId": 789  # Optional: link to user story/requirement
}
```

### Update Test Case Steps

```python
# Using mcp__ado__testplan_update_test_case_steps
params = {
    "id": 12345,
    "steps": """1. Navigate to login page|Login page is displayed
2. Enter valid username|Username field populated
3. Enter valid password|Password field shows masked characters
4. Click Login button|System processes credentials
5. Verify dashboard loads|Dashboard is displayed with user info"""
}
```

### Add Test Cases to Suite

```python
# Using mcp__ado__testplan_add_test_cases_to_suite
params = {
    "project": "MyProject",
    "planId": 123,
    "suiteId": 456,
    "testCaseIds": ["12345", "12346", "12347"]
}
```

### List Test Cases in Suite

```python
# Using mcp__ado__testplan_list_test_cases
params = {
    "project": "MyProject",
    "planid": 123,
    "suiteid": 456
}
```

### Get Test Results from Build

```python
# Using mcp__ado__testplan_show_test_results_from_build_id
params = {
    "project": "MyProject",
    "buildid": 78901
}
```

---

## Test Plan Best Practices

### 1. Structure Test Plans by Release/Sprint

```
Release 2.0 Test Plan
├── Sprint 1 Tests
│   ├── Feature A Tests
│   └── Feature B Tests
├── Sprint 2 Tests
│   └── Feature C Tests
├── Regression Tests
└── Performance Tests
```

### 2. Use Requirements-Based Suites

Link test suites to user stories for traceability:

```
User Story: As a user, I want to login...
└── Requirements Suite
    ├── TC: Valid login
    ├── TC: Invalid password
    ├── TC: Account locked
    └── TC: Forgot password
```

### 3. Parameterize Test Cases

Use shared parameters for data-driven testing:

```
@username = testuser1, testuser2, admin
@password = valid123, Valid456, Admin789
```

### 4. Configure Multiple Configurations

Test across environments:

| Config | OS | Browser |
|--------|-------|---------|
| Config 1 | Windows 11 | Chrome |
| Config 2 | Windows 11 | Firefox |
| Config 3 | macOS | Safari |
| Config 4 | Ubuntu | Chrome |

### 5. Link to Automation

```json
{
  "automationStatus": "Automated",
  "automatedTestName": "MyTests.LoginTests.ValidLoginTest",
  "automatedTestStorage": "MyTests.dll",
  "automatedTestType": "Unit Test"
}
```
