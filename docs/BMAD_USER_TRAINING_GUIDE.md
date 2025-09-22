# BMAD User Training Guide

**Document Version**: 1.0  
**Date**: 2025-01-17  
**Audience**: Developers, Product Managers, Architects

## 🎯 **Training Overview**

This guide provides comprehensive training on the new BMAD-Cerebral integration capabilities. BMAD (Business Method and Design) is an AI-powered project planning and execution system that bridges natural language planning with knowledge management and task orchestration.

## 📚 **Learning Objectives**

By the end of this training, you will be able to:

1. **Understand BMAD concepts** and how they integrate with Cerebral
2. **Use the BMAD CLI** for local development and testing
3. **Create project documentation** using brownfield workflows
4. **Manage expansion packs** for specialized domain support
5. **Execute BMAD workflows** through the API
6. **Monitor system performance** and troubleshoot issues

## 🏗️ **BMAD Architecture Overview**

### **Core Components**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   BMAD API      │    │   Cerebral       │    │   Database      │
│   Service       │◄──►│   Platform       │◄──►│   Schema        │
│                 │    │                  │    │                 │
│ • HTTP API      │    │ • Tool Registry  │    │ • Documents     │
│ • Brownfield    │    │ • CLI Interface  │    │ • Tasks         │
│ • Expansion     │    │ • Database Int.  │    │ • Activities    │
│ • Workflows     │    │ • RAG/KG Sync    │    │ • Projects      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Key Concepts**

- **Greenfield Projects**: New projects built from scratch
- **Brownfield Projects**: Enhancement of existing projects
- **Expansion Packs**: Specialized domain capabilities (game dev, creative writing, etc.)
- **Workflows**: Automated processes for PRD, Architecture, and Story creation
- **RAG Integration**: Retrieval-Augmented Generation for intelligent document search

## 🚀 **Getting Started**

### **Prerequisites**

1. **Access to Cerebral Platform**
2. **BMAD CLI installed** (see setup instructions below)
3. **Basic understanding of project planning concepts**
4. **Familiarity with command-line interfaces**

### **Setup BMAD CLI**

```bash
# Navigate to your project directory
cd /path/to/your/project

# Run the setup script
python scripts/setup_bmad_cli.py

# Verify installation
./bmad local-tool-registry
```

## 🛠️ **Module 1: BMAD CLI Basics**

### **Available Commands**

The BMAD CLI provides 11 commands for local development and testing:

```bash
./bmad health                           # Check API service health
./bmad list-tools                       # List available BMAD tools
./bmad detect-project-type              # Detect greenfield vs brownfield
./bmad document-project                 # Document existing projects
./bmad create-brownfield-prd            # Create brownfield PRDs
./bmad list-expansion-packs             # List expansion packs
./bmad install-pack                     # Install expansion packs
./bmad stats                            # Get service statistics
./bmad local-tool-registry              # Show local tool registry
```

### **Exercise 1: CLI Exploration**

```bash
# Check if BMAD CLI is working
./bmad local-tool-registry

# Expected output: 278 total tools, 230 BMAD tools
```

**Expected Output:**
```
🔧 Local BMAD Tool Registry:
Total tools: 278
BMAD tools: 230
Registry version: 1.0.0

📋 BMAD Tools by Category:
  prd: 3 tools
  arch: 3 tools
  story: 3 tools
  brownfield: 4 tools
  expansion: 31 tools
  ...
```

## 🏗️ **Module 2: Project Type Detection**

### **Understanding Project Types**

BMAD automatically detects whether your project is:
- **Greenfield**: New project built from scratch
- **Brownfield**: Enhancement of existing project

### **Exercise 2: Project Type Detection**

```bash
# Detect project type for a new project
./bmad detect-project-type --project-size small

# Detect project type for an existing project
./bmad detect-project-type --has-existing-code --has-tests --project-size large
```

**Expected Output:**
```
🔍 Detecting project type...
📊 Project Type: BROWNFIELD
🎯 Confidence: 85.0%
🔄 Recommended Workflow: bmad_brownfield_workflow
📋 Analysis:
  • has_existing_code: true
  • has_documentation: true
  • has_tests: true
  • project_size: large
```

## 📝 **Module 3: Brownfield Project Enhancement**

### **Brownfield Workflow Overview**

Brownfield workflows help enhance existing projects by:
1. **Documenting existing systems**
2. **Creating enhancement-focused PRDs**
3. **Designing integration-focused architectures**
4. **Generating safe enhancement stories**

### **Exercise 3: Document Existing Project**

```bash
# Document an existing project
./bmad document-project /path/to/your/project \
  --focus-areas 'backend,api,database' \
  --output-format single_document
```

**Expected Output:**
```
📝 Documenting project: /path/to/your/project
✅ Project documentation completed
```

### **Exercise 4: Create Brownfield PRD**

```bash
# Create PRD for project enhancement
./bmad create-brownfield-prd 'My Enhancement Project' \
  --enhancement-scope '{"features": ["new-api", "ui-update"]}' \
  --existing-analysis '{"current_tech": "react", "database": "postgresql"}'
```

**Expected Output:**
```
📋 Creating brownfield PRD for: My Enhancement Project
✅ Brownfield PRD created successfully
```

## 🎮 **Module 4: Expansion Packs**

### **Available Expansion Packs**

BMAD includes 10 expansion packs for specialized domains:

- **bmad-creative-writing**: 10 agents, 7 workflows
- **bmad-godot-game-dev**: 10 agents, 2 workflows
- **bmad-2d-unity-game-dev**: 4 agents, 2 workflows
- **bmad-technical-research**: 2 agents, 1 workflow
- **bmad-infrastructure-devops**: 1 agent, 0 workflows

### **Exercise 5: Expansion Pack Management**

```bash
# List available expansion packs
./bmad list-expansion-packs

# Install creative writing pack
./bmad install-pack bmad-creative-writing

# Enable pack for project
./bmad enable-pack bmad-creative-writing --project-id 'your-project-id'
```

**Expected Output:**
```
📦 Available Expansion Packs (10 total):
  • Creative Writing
    ID: bmad-creative-writing
    Version: 1.0.0
    Category: creative
    Agents: 10
    Workflows: 7

📦 Installing expansion pack: bmad-creative-writing (version: latest)
✅ Expansion pack installed successfully
```

## 🔧 **Module 5: API Integration**

### **BMAD API Endpoints**

The BMAD API provides 20+ endpoints for programmatic access:

**Core Endpoints:**
- `GET /bmad/health` - Service health check
- `GET /bmad/tools` - List available tools
- `POST /bmad/tools/{tool_name}/execute` - Execute BMAD workflows

**Brownfield Endpoints:**
- `POST /bmad/project-type/detect` - Detect project type
- `POST /bmad/brownfield/document-project` - Document existing project
- `POST /bmad/brownfield/prd-create` - Create brownfield PRD

**Expansion Pack Endpoints:**
- `GET /bmad/expansion-packs/list` - List available packs
- `POST /bmad/expansion-packs/install` - Install expansion pack
- `POST /bmad/expansion-packs/enable` - Enable pack for project

### **Exercise 6: API Testing**

```bash
# Start BMAD API service locally
python -m bmad_api_service.main &

# Test health endpoint
./bmad health

# Get service statistics
./bmad stats
```

**Expected Output:**
```
✅ BMAD API service is healthy
Tools count: 81
Vendor BMAD status: True

📊 BMAD API Service Statistics:
Tools count: 81
Performance Stats:
  • uptime: 43.00477886199951
  • total_executions: 0
  • success_rate: 0.0
  • system_stats: {'cpu_usage': 9.4, 'memory_usage': 42.0}
```

## 📊 **Module 6: Monitoring and Troubleshooting**

### **Health Monitoring**

BMAD provides comprehensive monitoring through:
- **Health endpoints** for service status
- **Metrics endpoints** for performance data
- **Statistics endpoints** for usage analytics

### **Exercise 7: Monitoring Setup**

```bash
# Set up monitoring (requires Kubernetes cluster access)
./scripts/setup-bmad-monitoring.sh setup

# Verify monitoring
./scripts/setup-bmad-monitoring.sh verify
```

### **Troubleshooting Common Issues**

**Issue 1: CLI Command Not Found**
```bash
# Solution: Make sure CLI is executable
chmod +x ./bmad
```

**Issue 2: API Service Not Responding**
```bash
# Solution: Check if service is running
./bmad health
# If failed, start the service
python -m bmad_api_service.main
```

**Issue 3: Authentication Errors**
```bash
# Solution: Check API key configuration
export BMAD_API_KEY="your-api-key"
./bmad health
```

## 🎯 **Module 7: Best Practices**

### **Project Planning Best Practices**

1. **Start with Project Type Detection**
   - Always run project type detection first
   - Use the recommended workflow for your project type

2. **Document Existing Projects Thoroughly**
   - Use focused documentation for large projects
   - Include all relevant focus areas

3. **Leverage Expansion Packs**
   - Install relevant expansion packs for your domain
   - Enable packs only for projects that need them

4. **Monitor System Performance**
   - Set up monitoring for production deployments
   - Watch for error rates and response times

### **Security Best Practices**

1. **Use Proper Authentication**
   - Always use API keys for production
   - Rotate keys regularly

2. **Follow Kyverno Policies**
   - Use SHA256 image digests
   - Enable security contexts

3. **Monitor Access Patterns**
   - Watch for unusual API usage
   - Set up alerting for security events

## 📈 **Module 8: Advanced Usage**

### **Custom Workflow Development**

1. **Create Custom Templates**
   - Extend existing BMAD templates
   - Add domain-specific requirements

2. **Build Custom Expansion Packs**
   - Create specialized agent teams
   - Define custom workflows

3. **Integrate with External Systems**
   - Use BMAD API for CI/CD integration
   - Connect to project management tools

### **Performance Optimization**

1. **Optimize Workflow Execution**
   - Use appropriate timeouts
   - Monitor resource usage

2. **Scale API Service**
   - Deploy multiple replicas
   - Use load balancing

3. **Optimize Database Queries**
   - Use proper indexing
   - Monitor query performance

## 🧪 **Module 9: Hands-on Exercises**

### **Exercise 9.1: Complete Greenfield Project**

```bash
# 1. Detect project type
./bmad detect-project-type --project-size medium

# 2. Create PRD
./bmad create-greenfield-prd 'My New Project'

# 3. Create Architecture
./bmad create-architecture 'My New Project'

# 4. Generate Stories
./bmad create-stories 'My New Project'
```

### **Exercise 9.2: Complete Brownfield Enhancement**

```bash
# 1. Detect project type
./bmad detect-project-type --has-existing-code --has-tests --project-size large

# 2. Document existing project
./bmad document-project /path/to/project --focus-areas 'api,ui'

# 3. Create enhancement PRD
./bmad create-brownfield-prd 'Enhancement Project'

# 4. Create integration architecture
./bmad create-brownfield-arch 'Enhancement Project'
```

### **Exercise 9.3: Expansion Pack Workflow**

```bash
# 1. List available packs
./bmad list-expansion-packs

# 2. Install relevant pack
./bmad install-pack bmad-creative-writing

# 3. Enable pack for project
./bmad enable-pack bmad-creative-writing --project-id 'project-id'

# 4. Use pack-specific tools
./bmad execute bmad_creative_writing_create_character --args '{"name": "Hero"}'
```

## 📋 **Module 10: Assessment and Certification**

### **Knowledge Check Questions**

1. **What is the difference between greenfield and brownfield projects?**
2. **How do you detect the project type using BMAD CLI?**
3. **What are expansion packs and how do you use them?**
4. **How do you monitor BMAD API service health?**
5. **What are the key security considerations for BMAD deployment?**

### **Practical Assessment**

Complete the following tasks:

1. **Setup BMAD CLI** and verify installation
2. **Detect project type** for a sample project
3. **Document an existing project** using brownfield workflows
4. **Install and enable** an expansion pack
5. **Monitor API service** performance and health

### **Certification Criteria**

To be certified in BMAD usage, you must:

- ✅ Successfully complete all hands-on exercises
- ✅ Demonstrate understanding of BMAD concepts
- ✅ Show proficiency with CLI commands
- ✅ Understand monitoring and troubleshooting
- ✅ Apply best practices in project planning

## 📚 **Additional Resources**

### **Documentation**

- [BMAD-Cerebral Integration Complete](./BMAD_CEREBRAL_INTEGRATION_COMPLETE.md)
- [Database Schema Design](./architecture/bmad_database_schema.md)
- [API Reference](./architecture/bmad_api_inventory.md)
- [Deployment Guide](./WEBMCP_DEPLOYMENT_GUIDE.md)

### **Support Channels**

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and references
- **Community Forum**: Ask questions and share experiences
- **Training Sessions**: Regular training and Q&A sessions

### **Version Information**

- **BMAD CLI**: Version 1.0.0
- **API Service**: Version 1.0.0
- **Tool Registry**: 278 tools, 230 BMAD tools
- **Expansion Packs**: 10 packs available

---

## 🎉 **Congratulations!**

You have completed the BMAD User Training Guide. You now have the knowledge and skills to effectively use the BMAD-Cerebral integration for AI-powered project planning and execution.

**Next Steps:**
1. Practice with your own projects
2. Explore advanced features
3. Share feedback and suggestions
4. Help train other team members

**Remember**: BMAD is designed to make project planning more intelligent and efficient. Use it to enhance your existing workflows and discover new possibilities in AI-assisted development.

---

*For questions or support, please refer to the additional resources or contact the development team.*
