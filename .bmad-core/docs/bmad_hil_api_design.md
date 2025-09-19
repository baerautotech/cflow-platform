# BMAD Human-in-the-Loop (HIL) Approval System API Design

## Overview

This document defines the API endpoints and data structures for the BMAD Human-in-the-Loop approval system, including interactive sessions, document approvals, and workflow gates.

## Base URL

```
/api/bmad/hil/
```

## Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Interactive Session Management

### Start Interactive Session

**POST** `/api/bmad/hil/sessions`

Start a new interactive Q&A session between an agent and human.

**Request Body:**
```json
{
  "project_id": "uuid",
  "agent_type": "PM|Architect|PO",
  "document_type": "PRD|Architecture|Story",
  "initial_content": "string",
  "questions": [
    {
      "index": 0,
      "text": "What are the key user personas for this project?",
      "type": "text|choice|rating"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "status": "active",
  "current_question": {
    "index": 0,
    "text": "What are the key user personas for this project?",
    "type": "text"
  },
  "next_action": "awaiting_human_response"
}
```

### Submit Response

**POST** `/api/bmad/hil/sessions/{session_id}/respond`

Submit a human response to the current question.

**Request Body:**
```json
{
  "response": "string",
  "metadata": {
    "confidence": "high|medium|low",
    "additional_notes": "string"
  }
}
```

**Response:**
```json
{
  "success": true,
  "response_id": "uuid",
  "agent_feedback": "Thank you for that response. Based on your input...",
  "next_question": {
    "index": 1,
    "text": "What are the critical functional requirements?",
    "type": "text"
  },
  "session_status": "active|completed"
}
```

### Get Session Status

**GET** `/api/bmad/hil/sessions/{session_id}`

Get current status of an interactive session.

**Response:**
```json
{
  "success": true,
  "session": {
    "id": "uuid",
    "project_id": "uuid",
    "agent_type": "PM",
    "document_type": "PRD",
    "status": "active",
    "current_question_index": 2,
    "total_questions": 5,
    "responses": [
      {
        "question_index": 0,
        "question_text": "What are the key user personas?",
        "human_response": "Our primary users are...",
        "agent_feedback": "Excellent, that gives us a clear picture..."
      }
    ],
    "created_at": "2025-09-18T10:00:00Z",
    "updated_at": "2025-09-18T10:15:00Z"
  }
}
```

### Complete Session

**POST** `/api/bmad/hil/sessions/{session_id}/complete`

Complete an interactive session and generate the final document.

**Request Body:**
```json
{
  "final_approval": true,
  "notes": "string"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "status": "completed",
  "generated_document": {
    "id": "uuid",
    "type": "PRD",
    "content": "Generated document content...",
    "status": "draft"
  },
  "next_action": "document_approval_required"
}
```

## Document Approval Management

### Request Approval

**POST** `/api/bmad/hil/approvals`

Request human approval for a BMAD document.

**Request Body:**
```json
{
  "doc_id": "uuid",
  "approval_type": "prd_approval|arch_approval|story_approval",
  "approver": "user_id",
  "deadline": "2025-09-20T10:00:00Z",
  "message": "Please review and approve this PRD document"
}
```

**Response:**
```json
{
  "success": true,
  "approval_id": "uuid",
  "status": "pending",
  "notification_sent": true,
  "next_action": "awaiting_human_approval"
}
```

### Get Approval Status

**GET** `/api/bmad/hil/approvals/{approval_id}`

Get status of a document approval request.

**Response:**
```json
{
  "success": true,
  "approval": {
    "id": "uuid",
    "doc_id": "uuid",
    "approver": "user_id",
    "approval_type": "prd_approval",
    "status": "pending",
    "deadline": "2025-09-20T10:00:00Z",
    "created_at": "2025-09-18T10:00:00Z",
    "document": {
      "id": "uuid",
      "type": "PRD",
      "title": "Project PRD",
      "content": "Document content..."
    }
  }
}
```

### Confirm Approval

**POST** `/api/bmad/hil/approvals/{approval_id}/confirm`

Confirm or reject a document approval.

**Request Body:**
```json
{
  "approved": true,
  "feedback": "This looks good, approved with minor suggestions",
  "suggestions": [
    "Consider adding more detail to the user personas section"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "approval_id": "uuid",
  "status": "approved",
  "document_status": "approved",
  "workflow_gate_status": "passed",
  "next_action": "proceed_to_next_stage"
}
```

### List Pending Approvals

**GET** `/api/bmad/hil/approvals/pending`

Get all pending approval requests for the current user.

**Query Parameters:**
- `project_id` (optional): Filter by project
- `approval_type` (optional): Filter by approval type
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "success": true,
  "approvals": [
    {
      "id": "uuid",
      "doc_id": "uuid",
      "approval_type": "prd_approval",
      "status": "pending",
      "deadline": "2025-09-20T10:00:00Z",
      "document": {
        "id": "uuid",
        "type": "PRD",
        "title": "Project PRD"
      },
      "project": {
        "id": "uuid",
        "name": "My Project"
      }
    }
  ],
  "total_count": 5,
  "has_more": false
}
```

## Workflow Gate Management

### Get Workflow Status

**GET** `/api/bmad/hil/workflow/{project_id}/status`

Get current workflow status and gate information for a project.

**Response:**
```json
{
  "success": true,
  "project_id": "uuid",
  "workflow_status": {
    "current_step": "prd_creation",
    "current_gate": "prd_gate",
    "gates": [
      {
        "type": "prd_gate",
        "status": "pending",
        "required_approvals": ["prd_approval"],
        "completed_approvals": [],
        "blocking": true
      },
      {
        "type": "arch_gate",
        "status": "pending",
        "required_approvals": ["arch_approval"],
        "completed_approvals": [],
        "blocking": false
      }
    ],
    "next_action": "complete_prd_interactive_session",
    "available_actions": [
      "start_prd_interactive_session",
      "request_prd_approval"
    ]
  }
}
```

### Get Next Action

**GET** `/api/bmad/hil/workflow/{project_id}/next-action`

Get the next recommended action in the workflow.

**Response:**
```json
{
  "success": true,
  "next_action": {
    "action": "start_prd_interactive_session",
    "description": "Start interactive PRD creation session",
    "required": true,
    "blocking": false,
    "gate_status": "prd_gate_pending"
  },
  "alternative_actions": [
    {
      "action": "request_prd_approval",
      "description": "Request approval for existing PRD",
      "required": false,
      "blocking": true
    }
  ]
}
```

### Update Gate Status

**POST** `/api/bmad/hil/workflow/{project_id}/gates/{gate_type}`

Update the status of a workflow gate.

**Request Body:**
```json
{
  "status": "passed|failed|waived",
  "reason": "string",
  "approval_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "gate_type": "prd_gate",
  "status": "passed",
  "workflow_updated": true,
  "next_action": "start_architecture_creation"
}
```

## Notification Management

### Send Approval Notification

**POST** `/api/bmad/hil/notifications/send`

Send approval notification to a user.

**Request Body:**
```json
{
  "approval_id": "uuid",
  "recipient": "user_id",
  "notification_type": "approval_request|approval_reminder",
  "channel": "email|web|mobile"
}
```

**Response:**
```json
{
  "success": true,
  "notification_id": "uuid",
  "status": "sent",
  "delivery_status": "delivered"
}
```

### Get Notification Status

**GET** `/api/bmad/hil/notifications/{notification_id}`

Get status of a notification.

**Response:**
```json
{
  "success": true,
  "notification": {
    "id": "uuid",
    "approval_id": "uuid",
    "recipient": "user_id",
    "type": "approval_request",
    "status": "delivered",
    "sent_at": "2025-09-18T10:00:00Z",
    "delivered_at": "2025-09-18T10:01:00Z",
    "read_at": "2025-09-18T10:05:00Z"
  }
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "approval_type",
      "issue": "Must be one of: prd_approval, arch_approval, story_approval"
    }
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request data validation failed
- `AUTHENTICATION_ERROR`: Invalid or missing authentication
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `WORKFLOW_ERROR`: Workflow constraint violation
- `GATE_BLOCKED`: Workflow gate prevents action
- `SESSION_EXPIRED`: Interactive session has expired
- `APPROVAL_EXPIRED`: Approval deadline has passed

## Rate Limiting

- Interactive sessions: 10 per hour per user
- Approval requests: 50 per hour per user
- API calls: 1000 per hour per user

## WebSocket Events

For real-time updates, clients can subscribe to WebSocket events:

```javascript
const ws = new WebSocket('wss://api.example.com/bmad/hil/events');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'approval_request':
      // Show approval notification
      break;
    case 'session_question':
      // Show new question in interactive session
      break;
    case 'gate_status_changed':
      // Update workflow status
      break;
  }
};
```

## Client Integration Examples

### Interactive Session Flow

```javascript
// Start interactive session
const session = await fetch('/api/bmad/hil/sessions', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    project_id: 'project-uuid',
    agent_type: 'PM',
    document_type: 'PRD',
    questions: [...]
  })
});

// Submit responses
const response = await fetch(`/api/bmad/hil/sessions/${session.id}/respond`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    response: 'User response text',
    metadata: { confidence: 'high' }
  })
});

// Complete session
const completion = await fetch(`/api/bmad/hil/sessions/${session.id}/complete`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    final_approval: true,
    notes: 'Session completed successfully'
  })
});
```

### Approval Workflow

```javascript
// Request approval
const approval = await fetch('/api/bmad/hil/approvals', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    doc_id: 'document-uuid',
    approval_type: 'prd_approval',
    approver: 'user-id',
    deadline: '2025-09-20T10:00:00Z'
  })
});

// Confirm approval
const confirmation = await fetch(`/api/bmad/hil/approvals/${approval.id}/confirm`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    approved: true,
    feedback: 'Approved with minor suggestions'
  })
});
```

This API design provides a comprehensive foundation for implementing the BMAD Human-in-the-Loop approval system with interactive sessions, document approvals, and workflow gate management.
