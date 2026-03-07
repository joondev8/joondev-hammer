# Copilot Instructions for Hammer

## Scope
- Apply these instructions to all code changes in this repository.

## Tech Stack
- Use Python 3.12-compatible code.
- Testing: pytest.

## Architecture
- Follow a modular structure with clear separation of concerns (e.g., routers, services, models).
- Use dependency injection for services and repositories.

## Code Style
- Make minimal, surgical changes focused on the request.
- Follow existing project naming and structure conventions.
- Prefer clear, explicit variable and function names.
- Avoid one-letter variable names.
- Do not add inline comments unless requested.
- Do not introduce new dependencies unless required by the task.

## API and Behavior
- Preserve existing API contracts unless the task explicitly asks for changes.
- For behavior changes, update related tests in `tests/`.
- Keep error handling explicit and consistent with existing endpoints.

## Testing
- Add or update pytest tests only for behavior touched by the change.
- Prefer targeted tests first (affected module), then broader tests as needed.
- Do not attempt to fix unrelated failing tests.

## Non-Goals
- Do not perform broad refactors unless requested.
- Do not rename files, symbols, or public interfaces without clear need.
- Do not commit changes unless explicitly asked.

## Personal Preferences
- Use boto3.Session() and assume IAM Role-based auth. Never prompt for access keys.
- When writing SQL for Terraform’s postgresql provider, provide queries that are safe for CI/CD (e.g., CREATE TABLE IF NOT EXISTS).
- For order events, use Amazon SQS with Dead Letter Queues (DLQ) for fault tolerance.
- Use context managers (with session.begin():) to ensure order operations are atomic.
