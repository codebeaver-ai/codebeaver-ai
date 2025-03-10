Let's create comprehensive specifications for your CI tool's reporting formats. I'll design formats for JUnit XML, HTML, and JSON that accommodate your specific requirements.

## 1. JUnit XML Format Extension

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <properties>
    <property name="tool_version" value="1.0.0"/>
    <property name="timestamp" value="2025-03-10T12:00:00"/>
  </properties>

  <testsuite name="UserServiceTests" tests="5" failures="1" errors="0" skipped="0" time="3.45">
    <properties>
      <property name="file_path" value="src/services/__tests__/user-service.test.js"/>
      <property name="file_status" value="updated"/> <!-- Added/Updated/Unchanged -->
    </properties>

    <testcase name="should create user" classname="UserServiceTests" time="0.24">
      <properties>
        <property name="test_written_by" value="tool"/> <!-- Tool/Human -->
        <property name="test_status" value="added"/> <!-- Added/Updated/Unchanged -->
      </properties>
    </testcase>

    <testcase name="should handle duplicate users" classname="UserServiceTests" time="0.31">
      <failure message="Expected error to be thrown" type="AssertionError">
        Expected error to be thrown but function completed successfully.
        at Object.&lt;anonymous> (src/services/__tests__/user-service.test.js:48:12)
      </failure>
      <properties>
        <property name="test_written_by" value="human"/>
        <property name="test_status" value="unchanged"/>
        <property name="bug_refs" value="BUG-123"/> <!-- References to detected bugs -->
      </properties>
    </testcase>

    <!-- More test cases... -->
  </testsuite>

  <testsuite name="E2ETests" tests="2" failures="1" errors="0" skipped="0" time="28.75">
    <properties>
      <property name="type" value="e2e"/>
    </properties>

    <testcase name="User Registration Flow" classname="E2ETests.UserFlows" time="15.32">
      <properties>
        <property name="video_path" value="artifacts/e2e/user-registration.mp4"/>
        <property name="bug_refs" value="BUG-456"/>
      </properties>
      <failure message="Registration form submission failed" type="E2EFailure">
        <![CDATA[
        STEPS:
        1. Navigate to /register
        2. Fill in email: test@example.com
        3. Fill in password: Password123
        4. Click submit button

        FAILURE COMMENT:
        Form submission failed - API returned 422 unprocessable entity.
        See network logs for details.
        ]]>
      </failure>
    </testcase>

    <!-- More E2E test cases... -->
  </testsuite>

  <!-- Bug reports section (extension to standard JUnit) -->
  <bugs>
    <bug id="BUG-123" severity="medium">
      <description>
        <![CDATA[
        Duplicate user check is not working properly in the createUser function.
        The function doesn't throw an error when a duplicate email is provided.

        Potential fix: Add validation before database insertion.
        ]]>
      </description>
      <affected_files>
        <file path="src/services/user-service.js" lines="45-52"/>
        <file path="src/controllers/user-controller.js" lines="23-29"/>
      </affected_files>
      <log_path>artifacts/logs/bug-123.log</log_path>
    </bug>

    <bug id="BUG-456" severity="high">
      <description>
        <![CDATA[
        API validation error not being handled in the registration form.
        When server returns validation errors, the UI shows a generic error
        instead of field-specific validation messages.
        ]]>
      </description>
      <affected_files>
        <file path="src/components/RegistrationForm.js" lines="78-92"/>
        <file path="src/api/user-api.js" lines="34-40"/>
      </affected_files>
      <log_path>artifacts/logs/bug-456.log</log_path>
    </bug>
  </bugs>
</testsuites>
```

## 2. JSON Format Specification

```json
{
  "meta": {
    "tool_version": "1.0.0",
    "timestamp": "2025-03-10T12:00:00",
    "summary": {
      "total_tests": 7,
      "passed": 5,
      "failed": 2,
      "skipped": 0,
      "total_time": 32.2,
      "bugs_found": 2
    }
  },
  "test_suites": [
    {
      "name": "UserServiceTests",
      "type": "unit",
      "file_path": "src/services/__tests__/user-service.test.js",
      "file_status": "updated",
      "tests": 5,
      "failures": 1,
      "errors": 0,
      "skipped": 0,
      "time": 3.45,
      "test_cases": [
        {
          "name": "should create user",
          "classname": "UserServiceTests",
          "time": 0.24,
          "status": "passed",
          "test_written_by": "tool",
          "test_status": "added"
        },
        {
          "name": "should handle duplicate users",
          "classname": "UserServiceTests",
          "time": 0.31,
          "status": "failed",
          "test_written_by": "human",
          "test_status": "unchanged",
          "failure": {
            "message": "Expected error to be thrown",
            "type": "AssertionError",
            "details": "Expected error to be thrown but function completed successfully.\nat Object.<anonymous> (src/services/__tests__/user-service.test.js:48:12)"
          },
          "bug_refs": ["BUG-123"]
        }
      ]
    },
    {
      "name": "E2ETests",
      "type": "e2e",
      "tests": 2,
      "failures": 1,
      "errors": 0,
      "skipped": 0,
      "time": 28.75,
      "test_cases": [
        {
          "name": "User Registration Flow",
          "classname": "E2ETests.UserFlows",
          "time": 15.32,
          "status": "failed",
          "video_path": "artifacts/e2e/user-registration.mp4",
          "failure": {
            "message": "Registration form submission failed",
            "type": "E2EFailure",
            "steps": [
              "Navigate to /register",
              "Fill in email: test@example.com",
              "Fill in password: Password123",
              "Click submit button"
            ],
            "comment": "Form submission failed - API returned 422 unprocessable entity. See network logs for details."
          },
          "bug_refs": ["BUG-456"]
        },
        {
          "name": "User Login Flow",
          "classname": "E2ETests.UserFlows",
          "time": 13.43,
          "status": "passed",
          "video_path": "artifacts/e2e/user-login.mp4",
          "steps": [
            "Navigate to /login",
            "Fill in email: test@example.com",
            "Fill in password: Password123",
            "Click login button",
            "Assert redirect to dashboard"
          ]
        }
      ]
    }
  ],
  "bugs": [
    {
      "id": "BUG-123",
      "severity": "medium",
      "description": "Duplicate user check is not working properly in the createUser function. The function doesn't throw an error when a duplicate email is provided.\n\nPotential fix: Add validation before database insertion.",
      "affected_files": [
        {
          "path": "src/services/user-service.js",
          "lines": "45-52"
        },
        {
          "path": "src/controllers/user-controller.js",
          "lines": "23-29"
        }
      ],
      "log_path": "artifacts/logs/bug-123.log",
      "found_in": ["unit_tests"],
      "related_tests": [
        {
          "suite": "UserServiceTests",
          "test": "should handle duplicate users"
        }
      ]
    },
    {
      "id": "BUG-456",
      "severity": "high",
      "description": "API validation error not being handled in the registration form. When server returns validation errors, the UI shows a generic error instead of field-specific validation messages.",
      "affected_files": [
        {
          "path": "src/components/RegistrationForm.js",
          "lines": "78-92"
        },
        {
          "path": "src/api/user-api.js",
          "lines": "34-40"
        }
      ],
      "log_path": "artifacts/logs/bug-456.log",
      "found_in": ["e2e_tests"],
      "related_tests": [
        {
          "suite": "E2ETests",
          "test": "User Registration Flow"
        }
      ]
    }
  ]
}
```

## 3. HTML Report Structure

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Test Report - March 10, 2025</title>
    <style>
      :root {
        --primary: #3498db;
        --success: #2ecc71;
        --warning: #f39c12;
        --danger: #e74c3c;
        --light: #f8f9fa;
        --dark: #343a40;
      }

      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
          Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        margin: 0;
        padding: 0;
        background-color: #f5f5f5;
      }

      .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
      }

      header {
        background-color: var(--dark);
        color: white;
        padding: 1rem 2rem;
        margin-bottom: 2rem;
      }

      .summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
      }

      .summary-card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      }

      .tabs {
        display: flex;
        border-bottom: 1px solid #ddd;
        margin-bottom: 1rem;
      }

      .tab {
        padding: 0.75rem 1.5rem;
        cursor: pointer;
        border-bottom: 3px solid transparent;
      }

      .tab.active {
        border-bottom: 3px solid var(--primary);
        font-weight: bold;
      }

      .tab-content {
        display: none;
      }

      .tab-content.active {
        display: block;
      }

      .test-suite {
        background: white;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        overflow: hidden;
      }

      .test-suite-header {
        padding: 1rem;
        background: #f8f9fa;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
      }

      .test-suite-body {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
      }

      .test-suite.expanded .test-suite-body {
        max-height: 2000px;
      }

      .test-case {
        padding: 1rem;
        border-bottom: 1px solid #eee;
      }

      .test-case:last-child {
        border-bottom: none;
      }

      .test-case.failed {
        border-left: 4px solid var(--danger);
      }

      .test-case.passed {
        border-left: 4px solid var(--success);
      }

      .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
      }

      .badge-primary {
        background-color: var(--primary);
        color: white;
      }
      .badge-success {
        background-color: var(--success);
        color: white;
      }
      .badge-danger {
        background-color: var(--danger);
        color: white;
      }
      .badge-warning {
        background-color: var(--warning);
        color: white;
      }

      .bug-card {
        background: white;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        padding: 1.5rem;
        border-left: 4px solid var(--danger);
      }

      .failure-details {
        background: #f8f9fa;
        border-radius: 4px;
        padding: 1rem;
        margin-top: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
      }

      .video-preview {
        max-width: 100%;
        border-radius: 4px;
        margin-top: 1rem;
        border: 1px solid #ddd;
      }

      .steps-list {
        background: #f8f9fa;
        border-radius: 4px;
        padding: 1rem;
        margin-top: 1rem;
      }

      .steps-list ol {
        margin: 0;
        padding-left: 1.5rem;
      }

      .file-badge {
        display: inline-block;
        background: #eee;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
      }
    </style>
  </head>
  <body>
    <header>
      <h1>Test Report</h1>
      <div>March 10, 2025 - 12:00:00 PM</div>
    </header>

    <div class="container">
      <!-- Summary Section -->
      <section class="summary">
        <div class="summary-card">
          <h3>Total Tests</h3>
          <div style="font-size: 2rem; font-weight: bold;">7</div>
        </div>

        <div class="summary-card">
          <h3>Passed</h3>
          <div
            style="font-size: 2rem; font-weight: bold; color: var(--success);"
          >
            5
          </div>
        </div>

        <div class="summary-card">
          <h3>Failed</h3>
          <div
            style="font-size: 2rem; font-weight: bold; color: var(--danger);"
          >
            2
          </div>
        </div>

        <div class="summary-card">
          <h3>Bugs Found</h3>
          <div
            style="font-size: 2rem; font-weight: bold; color: var(--warning);"
          >
            2
          </div>
        </div>

        <div class="summary-card">
          <h3>Total Duration</h3>
          <div style="font-size: 2rem; font-weight: bold;">32.2s</div>
        </div>
      </section>

      <!-- Tabs Navigation -->
      <div class="tabs">
        <div class="tab active" data-tab="all-tests">All Tests</div>
        <div class="tab" data-tab="unit-tests">Unit Tests</div>
        <div class="tab" data-tab="e2e-tests">E2E Tests</div>
        <div class="tab" data-tab="bugs">Bugs (2)</div>
      </div>

      <!-- All Tests Tab -->
      <div class="tab-content active" id="all-tests">
        <!-- Unit Test Suite Example -->
        <div class="test-suite expanded">
          <div class="test-suite-header">
            <div>
              <span class="badge badge-primary">Unit</span>
              <strong>UserServiceTests</strong>
              <span class="badge badge-warning">File Updated</span>
            </div>
            <div>
              <span class="badge badge-success">4 Passed</span>
              <span class="badge badge-danger">1 Failed</span>
              <span>3.45s</span>
            </div>
          </div>

          <div class="test-suite-body">
            <!-- Passed Test Case -->
            <div class="test-case passed">
              <div style="display: flex; justify-content: space-between;">
                <div>
                  <strong>should create user</strong>
                  <span class="badge badge-success">Passed</span>
                  <span class="badge badge-primary">Tool-written</span>
                  <span class="badge badge-warning">Added</span>
                </div>
                <div>0.24s</div>
              </div>
            </div>

            <!-- Failed Test Case -->
            <div class="test-case failed">
              <div style="display: flex; justify-content: space-between;">
                <div>
                  <strong>should handle duplicate users</strong>
                  <span class="badge badge-danger">Failed</span>
                  <span class="badge badge-primary">Human-written</span>
                </div>
                <div>0.31s</div>
              </div>

              <div class="failure-details">
                AssertionError: Expected error to be thrown but function
                completed successfully. at Object.&lt;anonymous>
                (src/services/__tests__/user-service.test.js:48:12)
              </div>

              <div style="margin-top: 1rem;">
                <strong>Related bugs:</strong> <a href="#bug-123">BUG-123</a>
              </div>
            </div>
          </div>
        </div>

        <!-- E2E Test Suite Example -->
        <div class="test-suite">
          <div class="test-suite-header">
            <div>
              <span class="badge badge-primary">E2E</span>
              <strong>E2ETests</strong>
            </div>
            <div>
              <span class="badge badge-success">1 Passed</span>
              <span class="badge badge-danger">1 Failed</span>
              <span>28.75s</span>
            </div>
          </div>

          <div class="test-suite-body">
            <!-- Failed E2E Test Case -->
            <div class="test-case failed">
              <div style="display: flex; justify-content: space-between;">
                <div>
                  <strong>User Registration Flow</strong>
                  <span class="badge badge-danger">Failed</span>
                </div>
                <div>15.32s</div>
              </div>

              <div style="margin-top: 1rem;">
                <video class="video-preview" controls>
                  <source
                    src="artifacts/e2e/user-registration.mp4"
                    type="video/mp4"
                  />
                  Your browser does not support the video tag.
                </video>
              </div>

              <div class="steps-list">
                <strong>Steps:</strong>
                <ol>
                  <li>Navigate to /register</li>
                  <li>Fill in email: test@example.com</li>
                  <li>Fill in password: Password123</li>
                  <li>Click submit button</li>
                </ol>
              </div>

              <div class="failure-details">
                <strong>Failure Comment:</strong>
                Form submission failed - API returned 422 unprocessable entity.
                See network logs for details.
              </div>

              <div style="margin-top: 1rem;">
                <strong>Related bugs:</strong> <a href="#bug-456">BUG-456</a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Unit Tests Tab -->
      <div class="tab-content" id="unit-tests">
        <!-- Content similar to all-tests but filtered -->
      </div>

      <!-- E2E Tests Tab -->
      <div class="tab-content" id="e2e-tests">
        <!-- Content similar to all-tests but filtered -->
      </div>

      <!-- Bugs Tab -->
      <div class="tab-content" id="bugs">
        <!-- Bug Card Example -->
        <div class="bug-card" id="bug-123">
          <div
            style="display: flex; justify-content: space-between; align-items: flex-start;"
          >
            <h3>BUG-123</h3>
            <span class="badge badge-warning">Medium</span>
          </div>

          <p>
            Duplicate user check is not working properly in the createUser
            function. The function doesn't throw an error when a duplicate email
            is provided.
          </p>

          <p>
            <strong>Potential fix:</strong> Add validation before database
            insertion.
          </p>

          <div>
            <strong>Affected files:</strong>
            <div style="margin-top: 0.5rem;">
              <span class="file-badge">src/services/user-service.js:45-52</span>
              <span class="file-badge"
                >src/controllers/user-controller.js:23-29</span
              >
            </div>
          </div>

          <div style="margin-top: 1rem;">
            <strong>Found in:</strong> Unit Tests
          </div>

          <div style="margin-top: 0.5rem;">
            <strong>Related tests:</strong>
            <ul>
              <li>UserServiceTests > should handle duplicate users</li>
            </ul>
          </div>

          <div style="margin-top: 1rem;">
            <a href="artifacts/logs/bug-123.log">View Detailed Log</a>
          </div>
        </div>

        <!-- Another Bug Card Example -->
        <div class="bug-card" id="bug-456">
          <div
            style="display: flex; justify-content: space-between; align-items: flex-start;"
          >
            <h3>BUG-456</h3>
            <span class="badge badge-danger">High</span>
          </div>

          <p>
            API validation error not being handled in the registration form.
            When server returns validation errors, the UI shows a generic error
            instead of field-specific validation messages.
          </p>

          <div>
            <strong>Affected files:</strong>
            <div style="margin-top: 0.5rem;">
              <span class="file-badge"
                >src/components/RegistrationForm.js:78-92</span
              >
              <span class="file-badge">src/api/user-api.js:34-40</span>
            </div>
          </div>

          <div style="margin-top: 1rem;">
            <strong>Found in:</strong> E2E Tests
          </div>

          <div style="margin-top: 0.5rem;">
            <strong>Related tests:</strong>
            <ul>
              <li>E2ETests > User Registration Flow</li>
            </ul>
          </div>

          <div style="margin-top: 1rem;">
            <a href="artifacts/logs/bug-456.log">View Detailed Log</a>
          </div>
        </div>
      </div>
    </div>

    <script>
      // Tab switching
      document.querySelectorAll(".tab").forEach((tab) => {
        tab.addEventListener("click", () => {
          // Deactivate all tabs
          document.querySelectorAll(".tab").forEach((t) => {
            t.classList.remove("active");
          });

          // Deactivate all tab contents
          document.querySelectorAll(".tab-content").forEach((content) => {
            content.classList.remove("active");
          });

          // Activate clicked tab
          tab.classList.add("active");

          // Activate corresponding content
          const tabId = tab.getAttribute("data-tab");
          document.getElementById(tabId).classList.add("active");
        });
      });

      // Test suite expansion toggle
      document.querySelectorAll(".test-suite-header").forEach((header) => {
        header.addEventListener("click", () => {
          const suite = header.parentElement;
          suite.classList.toggle("expanded");
        });
      });
    </script>
  </body>
</html>
```

## Report Format Implementation Guide

Now that we've defined the three report formats, here's my recommendation for implementing them:

### 1. Primary Output Implementation

1. **Base Format**: Generate the JUnit XML format first, as it's the most widely compatible format.

   - Extend the standard JUnit XML with custom properties for your special requirements
   - This ensures compatibility with existing CI systems while supporting your features

2. **Storage**: Save the report files with consistent naming conventions:

   - `test-report-{timestamp}.xml` - JUnit XML report
   - `test-report-{timestamp}.json` - JSON report
   - `test-report-{timestamp}.html` - HTML report

3. **Artifacts Management**:
   - Store videos, screenshots, and logs in an organized folder structure
   - Reference them with relative paths in the reports
   - Example structure:
     ```
     /artifacts/
       /e2e/
         user-registration.mp4
         user-login.mp4
       /logs/
         bug-123.log
         bug-456.log
     ```

### 2. Key Features to Implement

1. **For Unit Tests**:

   - Track which tests were generated by the tool vs. written by humans
   - Track file and test modification status (added/updated/unchanged)
   - Link bugs to specific test failures

2. **For E2E Tests**:

   - Structured representation of test steps
   - Failure comments for better debugging context
   - Video linking and embedding in HTML reports
   - Steps visualization

3. **For Bug Tracking**:
   - Unique bug IDs for reference
   - Severity classification
   - Detailed descriptions
   - Affected files with line numbers
   - Links to relevant tests that discovered the bug

### 3. Report Generation Pipeline

I recommend implementing the report generation as follows:

1. Collect test results during execution
2. Generate the JUnit XML as the primary data structure
3. Transform the XML to JSON for easier programmatic handling
4. Generate the HTML report from the JSON data
5. Store all formats and artifacts in a consistent location

This approach gives you the best of all worlds - compatibility, machine readability, and human-friendly visualization.

Would you like me to elaborate on any specific part of these formats or implementation recommendations?
