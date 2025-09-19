# BMAD CLI Usage Guide for cflow Platform

**Date**: 2025-01-09  
**Status**: ✅ **READY FOR USE**  
**Target**: Developers using BMAD with cflow platform

## 🎯 **Quick Start**

### **1. Verify BMAD Integration**
```bash
cd /path/to/your/cflow-platform
python3 -m cflow_platform.cli.one_touch_installer --verify-bmad
```

### **2. Test BMAD Tools**
```bash
python3 -c "
import asyncio
from cflow_platform.core.direct_client import execute_mcp_tool

async def test_bmad():
    # Create a test PRD
    result = await execute_mcp_tool('bmad_prd_create', 
        project_name='Test Project',
        goals=['Test BMAD integration'],
        background='Testing BMAD CLI functionality'
    )
    print('✅ BMAD PRD Created:', result['success'])
    
    # List all documents
    docs = await execute_mcp_tool('bmad_doc_list')
    print(f'📄 Total Documents: {docs[\"count\"]}')

asyncio.run(test_bmad())
"
```

## 📋 **Complete BMAD CLI Reference**

### **Document Creation Commands**

#### **Create PRD (Product Requirements Document)**
```python
await execute_mcp_tool('bmad_prd_create', 
    project_name='Your Project Name',
    goals=['Goal 1', 'Goal 2', 'Goal 3'],
    background='Project background and context'
)
```

**Example:**
```python
await execute_mcp_tool('bmad_prd_create', 
    project_name='Task Management App',
    goals=[
        'User authentication and authorization',
        'Task creation and management',
        'Team collaboration features',
        'Real-time notifications'
    ],
    background='A modern task management application for development teams to collaborate and track project progress.'
)
```

#### **Create Architecture Document**
```python
await execute_mcp_tool('bmad_arch_create',
    project_name='Your Project Name',
    prd_id='<prd_document_id>',
    tech_stack=['Technology 1', 'Technology 2']
)
```

**Example:**
```python
await execute_mcp_tool('bmad_arch_create',
    project_name='Task Management App',
    prd_id='16026136-3af5-4d23-a7bb-74866edbb89e',
        tech_stack=['React Native + React Native Web', 'Python FastAPI', 'PostgreSQL', 'Redis', 'WebSocket']
)
```

#### **Create User Story Document**
```python
await execute_mcp_tool('bmad_story_create',
    project_name='Your Project Name',
    prd_id='<prd_document_id>',
    arch_id='<architecture_document_id>',
    user_stories=['Story 1', 'Story 2']
)
```

**Example:**
```python
await execute_mcp_tool('bmad_story_create',
    project_name='Task Management App',
    prd_id='16026136-3af5-4d23-a7bb-74866edbb89e',
    arch_id='3414f855-b3fd-41e6-9061-431e52b2a9c7',
    user_stories=[
        'As a user, I want to create an account so I can access the system',
        'As a user, I want to create tasks so I can track my work',
        'As a user, I want to assign tasks to team members so we can collaborate'
    ]
)
```

### **Document Management Commands**

#### **List All Documents**
```python
await execute_mcp_tool('bmad_doc_list')
```

#### **List Documents with Filters**
```python
await execute_mcp_tool('bmad_doc_list',
    project_id='<project_id>',  # Optional
    doc_type='PRD',             # Optional: 'PRD', 'ARCH', 'STORY'
    status='draft'              # Optional: 'draft', 'review', 'approved', 'archived'
)
```

#### **Approve Document**
```python
await execute_mcp_tool('bmad_doc_approve',
    doc_id='<document_id>',
    approver='your_name'
)
```

#### **Reject Document**
```python
await execute_mcp_tool('bmad_doc_reject',
    doc_id='<document_id>',
    reason='Reason for rejection',
    reviewer='your_name'
)
```

### **Document Update Commands**

#### **Update PRD**
```python
await execute_mcp_tool('bmad_prd_update',
    doc_id='<document_id>',
    updates={
        'content': 'Updated PRD content',
        'status': 'review'
    }
)
```

#### **Update Architecture**
```python
await execute_mcp_tool('bmad_arch_update',
    doc_id='<document_id>',
    updates={
        'content': 'Updated architecture content',
        'status': 'approved'
    }
)
```

#### **Update Story**
```python
await execute_mcp_tool('bmad_story_update',
    doc_id='<document_id>',
    updates={
        'content': 'Updated story content',
        'status': 'approved'
    }
)
```

### **Document Retrieval Commands**

#### **Get PRD**
```python
await execute_mcp_tool('bmad_prd_get',
    doc_id='<document_id>'
)
```

#### **Get Architecture**
```python
await execute_mcp_tool('bmad_arch_get',
    doc_id='<document_id>'
)
```

#### **Get Story**
```python
await execute_mcp_tool('bmad_story_get',
    doc_id='<document_id>'
)
```

## 🔄 **Complete Workflow Example**

### **Full BMAD Project Workflow**

```python
import asyncio
import json
from cflow_platform.core.direct_client import execute_mcp_tool

async def complete_bmad_workflow():
    """Complete BMAD workflow from PRD to approved stories."""
    
    # Step 1: Create PRD
    print("📝 Creating PRD...")
    prd_result = await execute_mcp_tool('bmad_prd_create', 
        project_name='E-commerce Platform',
        goals=[
            'User authentication and profiles',
            'Product catalog and search',
            'Shopping cart and checkout',
            'Order management and tracking',
            'Admin dashboard and analytics'
        ],
        background='A modern e-commerce platform for small to medium businesses to sell products online with comprehensive management tools.'
    )
    
    if not prd_result['success']:
        print(f"❌ PRD creation failed: {prd_result['error']}")
        return
    
    prd_id = prd_result['doc_id']
    print(f"✅ PRD created: {prd_id}")
    
    # Step 2: Create Architecture
    print("🏗️ Creating Architecture...")
    arch_result = await execute_mcp_tool('bmad_arch_create',
        project_name='E-commerce Platform',
        prd_id=prd_id,
        tech_stack=[
            'React Native + React Native Web (Cross-platform)',
            'Python FastAPI (Backend)',
            'PostgreSQL (Database)',
            'Redis (Caching)',
            'Stripe (Payments)',
            'MinIO S3 (File Storage)',
            'Docker (Containerization)'
        ]
    )
    
    if not arch_result['success']:
        print(f"❌ Architecture creation failed: {arch_result['error']}")
        return
    
    arch_id = arch_result['doc_id']
    print(f"✅ Architecture created: {arch_id}")
    
    # Step 3: Create User Stories
    print("📖 Creating User Stories...")
    story_result = await execute_mcp_tool('bmad_story_create',
        project_name='E-commerce Platform',
        prd_id=prd_id,
        arch_id=arch_id,
        user_stories=[
            'As a customer, I want to create an account so I can save my information',
            'As a customer, I want to browse products so I can find items to buy',
            'As a customer, I want to add items to cart so I can purchase multiple items',
            'As a customer, I want to checkout securely so I can complete my purchase',
            'As an admin, I want to manage products so I can update inventory',
            'As an admin, I want to view analytics so I can track business performance'
        ]
    )
    
    if not story_result['success']:
        print(f"❌ Story creation failed: {story_result['error']}")
        return
    
    story_id = story_result['doc_id']
    print(f"✅ Stories created: {story_id}")
    
    # Step 4: Approve Documents
    print("✅ Approving Documents...")
    
    # Approve PRD
    await execute_mcp_tool('bmad_doc_approve',
        doc_id=prd_id,
        approver='project_manager'
    )
    print(f"✅ PRD approved: {prd_id}")
    
    # Approve Architecture
    await execute_mcp_tool('bmad_doc_approve',
        doc_id=arch_id,
        approver='tech_lead'
    )
    print(f"✅ Architecture approved: {arch_id}")
    
    # Approve Stories
    await execute_mcp_tool('bmad_doc_approve',
        doc_id=story_id,
        approver='product_owner'
    )
    print(f"✅ Stories approved: {story_id}")
    
    # Step 5: List All Documents
    print("📋 Final Document Summary...")
    docs = await execute_mcp_tool('bmad_doc_list')
    
    print(f"\n📊 Project Summary:")
    print(f"Total Documents: {docs['count']}")
    print(f"PRD ID: {prd_id}")
    print(f"Architecture ID: {arch_id}")
    print(f"Stories ID: {story_id}")
    
    print("\n🎉 BMAD workflow completed successfully!")
    print("Ready for CAEF execution and development!")

# Run the complete workflow
asyncio.run(complete_bmad_workflow())
```

## 🛠️ **Integration with cflow Systems**

### **Task Management Integration**
```python
# After creating BMAD documents, create related tasks
await execute_mcp_tool('task_add',
    title='Implement User Authentication',
    description='Based on BMAD PRD and Architecture documents',
    priority='high'
)
```

### **Knowledge Graph Search**
```python
# Search for BMAD documents in Knowledge Graph
await execute_mcp_tool('memory_search',
    query='e-commerce platform authentication requirements'
)
```

### **CAEF Integration**
```python
# Start CAEF execution after BMAD approval
await execute_mcp_tool('caef_start',
    story_id='<bmad_story_document_id>',
    context_docs=['<prd_id>', '<arch_id>']
)
```

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. BMAD Handlers Not Available**
```bash
# Verify BMAD integration
python3 -m cflow_platform.cli.one_touch_installer --verify-bmad
```

#### **2. Supabase Connection Issues**
```bash
# Check Supabase connectivity
python3 -m cflow_platform.cli.memory_check
```

#### **3. Document Not Found**
```python
# List all documents to find correct IDs
docs = await execute_mcp_tool('bmad_doc_list')
for doc in docs['documents']:
    print(f"ID: {doc['id']}, Type: {doc['kind']}, Status: {doc['status']}")
```

### **Error Handling**
```python
try:
    result = await execute_mcp_tool('bmad_prd_create', 
        project_name='Test Project',
        goals=['Test goal'],
        background='Test background'
    )
    
    if result['success']:
        print(f"✅ Success: {result['message']}")
    else:
        print(f"❌ Error: {result['error']}")
        
except Exception as e:
    print(f"❌ Exception: {str(e)}")
```

## 📚 **Additional Resources**

- **BMAD Core Documentation**: `vendor/bmad/docs/user-guide.md`
- **Integration Status**: `docs/engineering/bmad_local_integration_status.md`
- **API Inventory**: `docs/architecture/bmad_api_inventory.md`
- **Integration Plan**: `docs/plans/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md`

## 🎉 **Ready to Use!**

BMAD CLI is fully functional and integrated with all cflow systems. You can:

- ✅ Create comprehensive project documentation
- ✅ Store documents in Supabase with full searchability
- ✅ Integrate with task management and CAEF workflows
- ✅ Use from CLI, IDE, or programmatically
- ✅ Build upon this foundation for web/mobile frontends

**Start building amazing projects with BMAD! 🚀**


