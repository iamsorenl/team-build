# Contracts

Interfaces between slices. Only a contract's owner changes it, and every change gets logged in DECISIONS.md.

## Example: GET /api/tasks
- Owner: name
- Used by: names
- Request: `GET /api/tasks`
- Success (200):
```json
{ "items": [{ "id": "task-1", "title": "Demo task", "assignee": null, "status": "todo" }] }
```
- Empty (200): `{ "items": [] }`
- Error (400): `{ "error": { "code": "INVALID_QUERY", "message": "..." } }`
