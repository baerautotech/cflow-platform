# BMAD API Reference

## Base URL
```
http://bmad-api-production.cerebral-production.svc.cluster.local:8000
```

## Authentication
All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

## Core Endpoints

### Health & Status
- `GET /bmad/health` - Comprehensive health status
- `GET /bmad/tools` - List all available BMAD tools

### Task Management
- `GET /bmad/tasks` - List tasks with filtering
- `GET /bmad/tasks/{task_id}` - Get specific task
- `POST /bmad/tasks/{task_id}/status` - Update task status
- `GET /bmad/task-management/stats` - Task statistics

### YAML Templates
- `GET /bmad/templates` - List available templates
- `POST /bmad/templates/{template_id}/create-task` - Create task from template

### Workflow Execution
- `POST /bmad/workflows/execute` - Execute BMAD workflow
- `POST /bmad/projects/detect-type` - Detect project type

### Expansion Packs
- `GET /bmad/expansion-packs` - List expansion packs
- `GET /bmad/expansion-packs/{pack_name}` - Get pack details
- `POST /bmad/expansion-packs/{pack_name}/install` - Install pack
- `POST /bmad/expansion-packs/{pack_name}/enable` - Enable pack
- `DELETE /bmad/expansion-packs/{pack_name}` - Uninstall pack

### Analytics
- `GET /bmad/analytics/metrics` - Real-time metrics
- `GET /bmad/analytics/report` - Comprehensive report
- `GET /bmad/analytics/users/{user_id}` - User analytics
- `GET /bmad/analytics/workflows/{workflow_name}` - Workflow analytics

## Response Format
```json
{
  "status": "success|error",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": { ... },
  "message": "Optional message"
}
```

## Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting
- Default: 100 requests/minute per user
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`