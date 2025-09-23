# BMAD Enhanced Capabilities User Guide

## Overview

This guide covers all the enhanced capabilities of the BMAD (Business Method Architecture Design) system, including Supabase integration, YAML templates, performance optimization, advanced analytics, and comprehensive monitoring.

## 🚀 **New Capabilities Overview**

### **1. Supabase Task Integration**
- **Direct Supabase Integration**: All task operations now use Supabase as the single source of truth
- **Real-time Synchronization**: Tasks are synchronized in real-time across all clients
- **Enhanced Task Management**: Comprehensive CRUD operations for BMAD tasks
- **Task Tracking**: Automatic task creation and status tracking for workflows

### **2. YAML Template System**
- **Template Management**: Create and manage YAML-based task templates
- **Dynamic Task Creation**: Generate tasks from templates with parameter substitution
- **Conditional Logic**: Support for conditional task creation based on parameters
- **Template Versioning**: Version control for task templates

### **3. Performance Optimization**
- **Intelligent Caching**: Automatic caching of frequently accessed data
- **Rate Limiting**: Built-in rate limiting to prevent system overload
- **Circuit Breaker**: Automatic failover protection for external services
- **Connection Pooling**: Optimized database connection management

### **4. Advanced Analytics**
- **Real-time Metrics**: Live performance and usage metrics
- **User Analytics**: Track user behavior and activity patterns
- **Workflow Analytics**: Monitor workflow execution and success rates
- **Business Intelligence**: Comprehensive reporting and insights

### **5. Enhanced Monitoring**
- **Comprehensive Dashboards**: 18-panel Grafana dashboard
- **Advanced Alerting**: 20+ alert rules covering all system aspects
- **Health Monitoring**: Real-time health checks for all components
- **Performance Tracking**: Detailed performance metrics and trends

## 📋 **API Endpoints Reference**

### **Core BMAD Endpoints**

#### **Health & Status**
```http
GET /bmad/health
```
Returns comprehensive health status including:
- Service availability
- Supabase connection status
- Provider router status
- Performance metrics
- Analytics status
- Task management status

#### **Tool Registry**
```http
GET /bmad/tools
```
Returns all available BMAD tools and their capabilities.

### **Task Management Endpoints**

#### **List Tasks**
```http
GET /bmad/tasks?project_id={id}&tenant_id={id}&status={status}&workflow_type={type}
```
Parameters:
- `project_id` (optional): Filter by project
- `tenant_id` (optional): Filter by tenant
- `status` (optional): Filter by status (pending, in_progress, completed, cancelled)
- `workflow_type` (optional): Filter by workflow type (PRD, ARCH, STORY)

#### **Get Task**
```http
GET /bmad/tasks/{task_id}
```
Returns detailed information about a specific task.

#### **Update Task Status**
```http
POST /bmad/tasks/{task_id}/status
```
Body:
```json
{
  "status": "in_progress",
  "metadata": {
    "updated_by": "user_id",
    "notes": "Task started"
  }
}
```

#### **Get Task Statistics**
```http
GET /bmad/task-management/stats
```
Returns comprehensive task management statistics.

### **YAML Template Endpoints**

#### **List Templates**
```http
GET /bmad/templates
```
Returns all available BMAD task templates.

#### **Create Task from Template**
```http
POST /bmad/templates/{template_id}/create-task
```
Body:
```json
{
  "project_id": "project_123",
  "tenant_id": "tenant_456",
  "parameters": {
    "title": "Custom Task Title",
    "description": "Custom task description",
    "priority": "high"
  }
}
```

### **Workflow Endpoints**

#### **Execute Workflow**
```http
POST /bmad/workflows/execute
```
Body:
```json
{
  "workflow_path": "prd/greenfield-prd.yaml",
  "arguments": {
    "project_name": "My Project",
    "description": "Project description"
  },
  "user_context": {
    "user_id": "user_123",
    "project_id": "project_456",
    "tenant_id": "tenant_789"
  }
}
```

#### **Project Type Detection**
```http
POST /bmad/projects/detect-type
```
Body:
```json
{
  "project_path": "/path/to/project",
  "project_name": "My Project"
}
```

### **Expansion Pack Endpoints**

#### **List Expansion Packs**
```http
GET /bmad/expansion-packs
```
Returns all available expansion packs.

#### **Get Expansion Pack Details**
```http
GET /bmad/expansion-packs/{pack_name}
```
Returns detailed information about a specific expansion pack.

#### **Install Expansion Pack**
```http
POST /bmad/expansion-packs/{pack_name}/install
```

#### **Enable Expansion Pack**
```http
POST /bmad/expansion-packs/{pack_name}/enable
```

#### **Uninstall Expansion Pack**
```http
DELETE /bmad/expansion-packs/{pack_name}
```

### **Analytics Endpoints**

#### **Get Real-time Metrics**
```http
GET /bmad/analytics/metrics
```
Returns real-time performance metrics.

#### **Get Comprehensive Report**
```http
GET /bmad/analytics/report
```
Returns comprehensive analytics report.

#### **Get User Analytics**
```http
GET /bmad/analytics/users/{user_id}
```
Returns analytics for a specific user.

#### **Get Workflow Analytics**
```http
GET /bmad/analytics/workflows/{workflow_name}
```
Returns analytics for a specific workflow.

## 🛠️ **Usage Examples**

### **Creating a Task from Template**

1. **List available templates:**
   ```bash
   curl -X GET "http://bmad-api/bmad/templates"
   ```

2. **Create a task from a template:**
   ```bash
   curl -X POST "http://bmad-api/bmad/templates/prd-template/create-task" \
     -H "Content-Type: application/json" \
     -d '{
       "project_id": "my-project-123",
       "tenant_id": "my-tenant-456",
       "parameters": {
         "title": "Product Requirements Document",
         "description": "Create PRD for new feature",
         "priority": "high"
       }
     }'
   ```

### **Executing a Workflow**

```bash
curl -X POST "http://bmad-api/bmad/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_path": "prd/greenfield-prd.yaml",
    "arguments": {
      "project_name": "E-commerce Platform",
      "description": "Modern e-commerce platform with AI recommendations"
    },
    "user_context": {
      "user_id": "user_123",
      "project_id": "ecommerce-project",
      "tenant_id": "company_abc"
    }
  }'
```

### **Monitoring Task Progress**

1. **Get task details:**
   ```bash
   curl -X GET "http://bmad-api/bmad/tasks/task_123"
   ```

2. **Update task status:**
   ```bash
   curl -X POST "http://bmad-api/bmad/tasks/task_123/status" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "in_progress",
       "metadata": {
         "updated_by": "user_123",
         "notes": "Started working on task"
       }
     }'
   ```

3. **Get task statistics:**
   ```bash
   curl -X GET "http://bmad-api/bmad/task-management/stats"
   ```

## 📊 **Monitoring & Analytics**

### **Health Monitoring**

Check the overall health of the BMAD system:
```bash
curl -X GET "http://bmad-api/bmad/health"
```

Response includes:
- Service status
- Supabase connection status
- Provider router status
- Performance metrics
- Analytics status
- Task management status

### **Real-time Metrics**

Get real-time performance metrics:
```bash
curl -X GET "http://bmad-api/bmad/analytics/metrics"
```

### **Comprehensive Reports**

Get detailed analytics reports:
```bash
curl -X GET "http://bmad-api/bmad/analytics/report"
```

## 🔧 **Configuration**

### **Environment Variables**

#### **Supabase Configuration**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

#### **Provider Configuration**
```bash
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
```

#### **Performance Configuration**
```bash
BMAD_CACHE_TTL=600
BMAD_RATE_LIMIT_MAX_CALLS=100
BMAD_RATE_LIMIT_PERIOD=60
BMAD_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
BMAD_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30
```

### **Production Mode**

Enable production mode to disable mock functionality:
```bash
BMAD_PRODUCTION_MODE=true
BMAD_ALLOW_MOCK_MODE=false
```

## 🚨 **Error Handling**

### **Common Error Responses**

#### **400 Bad Request**
```json
{
  "detail": "Invalid request parameters",
  "status_code": 400
}
```

#### **404 Not Found**
```json
{
  "detail": "Resource not found",
  "status_code": 404
}
```

#### **429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "status_code": 429
}
```

#### **503 Service Unavailable**
```json
{
  "detail": "Service temporarily unavailable (circuit breaker open)",
  "status_code": 503
}
```

### **Error Handling Best Practices**

1. **Check HTTP status codes** before processing responses
2. **Implement retry logic** for transient errors (429, 503)
3. **Handle rate limiting** with exponential backoff
4. **Monitor circuit breaker status** for service availability
5. **Log errors** for debugging and monitoring

## 📚 **Best Practices**

### **Task Management**
1. **Use appropriate task priorities** (low, medium, high)
2. **Update task status regularly** to maintain accurate tracking
3. **Include meaningful metadata** when updating tasks
4. **Monitor task statistics** for system health

### **Workflow Execution**
1. **Provide complete user context** for proper task creation
2. **Use descriptive workflow arguments** for better tracking
3. **Monitor workflow execution** through task status updates
4. **Handle workflow failures** gracefully

### **Template Usage**
1. **Use existing templates** when possible
2. **Provide all required parameters** for template instantiation
3. **Customize templates** for specific project needs
4. **Version control templates** for consistency

### **Performance Optimization**
1. **Monitor cache hit rates** for optimization opportunities
2. **Respect rate limits** to avoid service degradation
3. **Handle circuit breaker states** appropriately
4. **Use connection pooling** for database operations

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Supabase Connection Issues**
- Verify `SUPABASE_URL` and API keys are correct
- Check network connectivity to Supabase
- Monitor Supabase service status

#### **Provider Router Issues**
- Verify provider API keys are valid
- Check provider service status
- Monitor provider response times

#### **Task Creation Failures**
- Verify project_id and tenant_id are valid
- Check Supabase permissions
- Monitor task creation metrics

#### **Template Issues**
- Verify template_id exists
- Check template parameter requirements
- Validate template JSON format

### **Debugging Commands**

```bash
# Check service health
curl -X GET "http://bmad-api/bmad/health"

# Check task statistics
curl -X GET "http://bmad-api/bmad/task-management/stats"

# Check analytics metrics
curl -X GET "http://bmad-api/bmad/analytics/metrics"

# Check available templates
curl -X GET "http://bmad-api/bmad/templates"
```

## 📞 **Support**

For technical support:
1. Check the troubleshooting section above
2. Review API documentation and examples
3. Monitor system health and metrics
4. Contact the development team with specific error details

## 🔄 **Migration Guide**

### **From Local Task Manager to Supabase**

If migrating from the old local task manager:

1. **Export existing tasks** (if any)
2. **Update API calls** to use new Supabase endpoints
3. **Configure Supabase credentials**
4. **Test task operations** with new endpoints
5. **Update monitoring** to use new metrics

### **API Changes**

- Task operations now use Supabase as backend
- New template-based task creation endpoints
- Enhanced health check with comprehensive status
- New analytics and monitoring endpoints
- Improved error handling and status codes
