---
title: 'Google Cloud Storage Static Page Push Support'
slug: 'gcs-static-page-push'
created: '2026-02-17'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.14', 'Flask', 'google-cloud-storage']
files_to_modify: ['esb/services/static_page_service.py', 'tests/test_services/test_static_page_service.py', 'requirements.txt', '.env.example', 'docs/administrators.md', 'README.md']
code_patterns: ['lazy cloud SDK imports inside push functions', 'RuntimeError for all push failures', 'log_mutation on success', 'bucket/key target parsing with index.html default']
test_patterns: ['mock cloud client via patch', 'TestPushS3-style class with 5 cases: happy path, client error, no credentials, empty bucket, default key']
---

# Tech-Spec: Google Cloud Storage Static Page Push Support

**Created:** 2026-02-17

## Overview

### Problem Statement

The static status page can only be pushed to a local directory or AWS S3. Users hosting on Google Cloud have no native push option.

### Solution

Add `gcs` as a third `STATIC_PAGE_PUSH_METHOD` value, using the `google-cloud-storage` Python library with Google's default credential chain, following the same implementation patterns established by the existing S3 push method.

### Scope

**In Scope:**
- New `_push_gcs()` function in `static_page_service.py` (lazy import, same error handling pattern as S3)
- `gcs` case in the `push()` dispatcher
- `google-cloud-storage` added to `requirements.txt`
- Full test coverage matching the S3 test structure
- README and Administrator Guide documentation updates
- `.env.example` updates

**Out of Scope:**
- No CLI commands, admin UI changes, or notification flow changes
- No multi-destination support
- No other cloud providers (Azure Blob, etc.)

## Context for Development

### Codebase Patterns

- Service layer pattern: all business logic in `esb/services/`, views never query models directly
- Lazy imports for optional cloud dependencies (boto3 imported inside `_push_s3()`, not at module level)
- `RuntimeError` raised for all configuration/credential/upload errors, propagated to worker for retry with backoff
- `log_mutation()` audit logging on successful push (called in `push()` after dispatch)
- Target format: `bucket-name/optional/key/path` — split on first `/`, default key is `index.html`
- Tests mock cloud clients via `unittest.mock.patch`, use `app.config[]` to set push method/target

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `esb/services/static_page_service.py` | Core service — `push()` dispatcher, `_push_s3()` as pattern template |
| `tests/test_services/test_static_page_service.py` | Test file — `TestPushS3` class as pattern template |
| `esb/config.py` | Config class with `STATIC_PAGE_PUSH_METHOD` and `STATIC_PAGE_PUSH_TARGET` |
| `.env.example` | Environment variable documentation |
| `docs/administrators.md` | Admin guide with Static Status Page Setup section and env var reference table |
| `README.md` | Project README with features list and tech stack |
| `requirements.txt` | Python dependencies |

### Technical Decisions

- Use `google-cloud-storage` library with default credential chain (`GOOGLE_APPLICATION_CREDENTIALS` env var, GCE instance metadata, Workload Identity, etc.) — mirrors boto3's approach for S3
- Target format follows same convention as S3: `bucket-name/optional/key/path`
- Push method config value: `gcs`
- Lazy import of `google.cloud.storage` inside `_push_gcs()` with clear `RuntimeError` if not installed
- Error mapping: `google.auth.exceptions.DefaultCredentialsError` → `RuntimeError` (mirrors `NoCredentialsError`), `google.api_core.exceptions.GoogleAPIError` → `RuntimeError` (mirrors `ClientError`)
- Upload via `blob.upload_from_string(html_content, content_type='text/html; charset=utf-8')` with `cache_control='no-cache, no-store, must-revalidate'`

## Implementation Plan

### Tasks

- [ ] Task 1: Add `google-cloud-storage` to `requirements.txt`
  - File: `requirements.txt`
  - Action: Add `google-cloud-storage>=2.18.0` after the `boto3` line
  - Notes: Follows same pattern as boto3 — pinned to minimum version with `>=`

- [ ] Task 2: Add `_push_gcs()` function to static page service
  - File: `esb/services/static_page_service.py`
  - Action: Add a new `_push_gcs(html_content: str, target: str) -> None` function after `_push_s3()`, mirroring its structure:
    1. Lazy import `google.cloud.storage` inside the function, catching `ImportError` with a clear `RuntimeError` message: `'google-cloud-storage is required for GCS push method. Install it with: pip install google-cloud-storage'`
    2. Parse `target` using the same `split('/', 1)` logic as `_push_s3()`: first part = bucket name, remainder = object name (blob key), default to `index.html` if no path component
    3. Validate bucket name is not empty — raise `RuntimeError(f'Invalid GCS target {target!r}: bucket name is empty')`
    4. Create client: `client = storage.Client()`
    5. Get bucket and blob: `bucket_obj = client.bucket(bucket)`, `blob = bucket_obj.blob(key)`
    6. Set `blob.cache_control = 'no-cache, no-store, must-revalidate'`
    7. Upload: `blob.upload_from_string(html_content, content_type='text/html; charset=utf-8')`
    8. Log success: `logger.info('Static page uploaded to gs://%s/%s', bucket, key)`
    9. Catch `google.auth.exceptions.DefaultCredentialsError` → `RuntimeError('Google Cloud credentials not configured for GCS push')`
    10. Catch `google.api_core.exceptions.GoogleAPIError` → `RuntimeError(f'GCS upload failed: {e}')`

- [ ] Task 3: Add `gcs` case to `push()` dispatcher
  - File: `esb/services/static_page_service.py`
  - Action: Add `elif method == 'gcs': _push_gcs(html_content, target)` between the `s3` elif and the `else` clause in the `push()` function (line 52)

- [ ] Task 4: Add `TestPushGCS` test class
  - File: `tests/test_services/test_static_page_service.py`
  - Action: Add a new `TestPushGCS` class after `TestPushS3`, with 5 test methods mirroring the S3 tests:
    1. `test_calls_gcs_upload_from_string` — Set config `STATIC_PAGE_PUSH_METHOD='gcs'`, `STATIC_PAGE_PUSH_TARGET='my-bucket/status/index.html'`. Mock `google.cloud.storage.Client`. Assert `Client()` called, `client.bucket('my-bucket')` called, `bucket.blob('status/index.html')` called, `blob.upload_from_string` called with `('<html>test</html>', content_type='text/html; charset=utf-8')`, and `blob.cache_control` set to `'no-cache, no-store, must-revalidate'`
    2. `test_handles_google_api_error` — Mock `blob.upload_from_string` to raise `google.api_core.exceptions.GoogleAPIError('Forbidden')`. Assert `RuntimeError` raised matching `'GCS upload failed'`
    3. `test_handles_default_credentials_error` — Mock `storage.Client` to raise `google.auth.exceptions.DefaultCredentialsError('msg')`. Assert `RuntimeError` raised matching `'Google Cloud credentials not configured'`
    4. `test_empty_bucket_raises_runtime_error` — Set target to `'/key/path'`. Assert `RuntimeError` raised matching `'bucket name is empty'`
    5. `test_default_key_when_no_path` — Set target to `'my-bucket'`. Mock client. Assert `bucket.blob` called with `'index.html'`
  - Notes: Import `google.cloud.storage`, `google.auth.exceptions`, and `google.api_core.exceptions` inside test methods (same lazy pattern as boto3 tests). Use `patch.object` on the `storage` module's `Client` class.

- [ ] Task 5: Update `.env.example`
  - File: `.env.example`
  - Action: Update the comment on `STATIC_PAGE_PUSH_METHOD` line from `'local' (copy to local path) or 's3' (upload to S3 bucket via boto3)` to `'local' (copy to local path), 's3' (upload to S3 bucket via boto3), or 'gcs' (upload to Google Cloud Storage bucket)`

- [ ] Task 6: Update Administrator Guide
  - File: `docs/administrators.md`
  - Action: Three changes:
    1. **Static Status Page Setup section** (line ~204): Add a `gcs` bullet to the Configuration list: `**\`gcs\`** — Uploads the static page to a Google Cloud Storage bucket specified by \`STATIC_PAGE_PUSH_TARGET\`. Uses Google's default credential chain (\`GOOGLE_APPLICATION_CREDENTIALS\` environment variable, GCE instance metadata, or Workload Identity).`
    2. **Environment Variable Reference table** (line ~82): Update `STATIC_PAGE_PUSH_METHOD` description to include `gcs`. Add two new rows after the AWS credential rows for `GOOGLE_APPLICATION_CREDENTIALS`: `Path to Google Cloud service account JSON key file. Only needed if \`STATIC_PAGE_PUSH_METHOD=gcs\` and not using instance metadata or Workload Identity.`
    3. **Runtime Dependencies list** (line ~135): Add `**google-cloud-storage** — Google Cloud Storage client for static page push (when using \`gcs\` method)` after the boto3 entry
    4. **Troubleshooting > Static page not updating** (line ~303): Add `For \`gcs\` method: verify Google Cloud credentials and bucket permissions`

- [ ] Task 7: Update README
  - File: `README.md`
  - Action: Two changes:
    1. **Features list** (line ~16): Change `pushes to local directory or S3` to `pushes to local directory, S3, or Google Cloud Storage`
    2. **Tech Stack list** (line ~50): Add `**google-cloud-storage** — GCS static page publishing` after the boto3 entry

### Acceptance Criteria

- [ ] AC 1: Given `STATIC_PAGE_PUSH_METHOD=gcs` and `STATIC_PAGE_PUSH_TARGET=my-bucket/status/index.html`, when `push()` is called with HTML content, then `google.cloud.storage.Client` is instantiated, `bucket('my-bucket')` is called, `blob('status/index.html')` is created, `blob.cache_control` is set to `'no-cache, no-store, must-revalidate'`, and `blob.upload_from_string()` is called with the HTML content and `content_type='text/html; charset=utf-8'`
- [ ] AC 2: Given `STATIC_PAGE_PUSH_METHOD=gcs` and `STATIC_PAGE_PUSH_TARGET=my-bucket`, when `push()` is called, then the blob key defaults to `index.html`
- [ ] AC 3: Given `STATIC_PAGE_PUSH_METHOD=gcs` and `STATIC_PAGE_PUSH_TARGET=/key/path` (empty bucket), when `push()` is called, then `RuntimeError` is raised with message containing `'bucket name is empty'`
- [ ] AC 4: Given `STATIC_PAGE_PUSH_METHOD=gcs` and Google Cloud credentials are not configured, when `push()` is called, then `RuntimeError` is raised with message containing `'Google Cloud credentials not configured'`
- [ ] AC 5: Given `STATIC_PAGE_PUSH_METHOD=gcs` and the GCS API returns an error, when `push()` is called, then `RuntimeError` is raised with message containing `'GCS upload failed'`
- [ ] AC 6: Given `google-cloud-storage` is not installed, when `_push_gcs()` is called, then `RuntimeError` is raised with message containing `'google-cloud-storage is required'`
- [ ] AC 7: Given a successful GCS push, when `push()` completes, then `log_mutation('static_page.pushed', 'system', {'method': 'gcs', 'target': ...})` is called (existing behavior in `push()` — no change needed, just verify it works for `gcs`)
- [ ] AC 8: Given the README, when a user reads the Features section, then it lists Google Cloud Storage as a static page destination
- [ ] AC 9: Given the Administrator Guide, when a user reads the Static Status Page Setup section, then `gcs` is documented as a push method with credential configuration instructions
- [ ] AC 10: Given `.env.example`, when a user reads the static page config comments, then `gcs` is listed as a valid method option

## Additional Context

### Dependencies

- `google-cloud-storage>=2.18.0` Python package (added to `requirements.txt`)
- No database migrations required
- No new environment variables required beyond the existing `STATIC_PAGE_PUSH_METHOD` and `STATIC_PAGE_PUSH_TARGET` (GCS credentials use Google's standard `GOOGLE_APPLICATION_CREDENTIALS` env var, which is not an app config — it's consumed by the SDK directly)

### Testing Strategy

- **Unit tests:** 5 new tests in `TestPushGCS` class covering happy path, credential error, API error, empty bucket validation, and default key behavior
- **Existing tests:** No changes to existing tests — `TestPushErrors.test_unknown_method_raises_runtime_error` still passes since `gcs` is now a known method
- **Manual verification:** Set `STATIC_PAGE_PUSH_METHOD=gcs` and `STATIC_PAGE_PUSH_TARGET=test-bucket/index.html` with valid credentials, trigger a status change, verify the HTML appears in the GCS bucket
- **Lint:** Run `make lint` to verify no ruff violations

### Notes

- The `google-cloud-storage` library pulls in `google-auth`, `google-api-core`, and `google-cloud-core` as transitive dependencies. These provide the credential chain and exception classes used in error handling.
- The `push()` function's existing `log_mutation` and `logger.info` calls fire after the dispatcher returns, so no changes needed there — they already capture `method` and `target` dynamically.
- AC 7 is technically already covered by the existing `TestPushMutationLogging` test pattern, but verifying it works for `gcs` is good practice.
