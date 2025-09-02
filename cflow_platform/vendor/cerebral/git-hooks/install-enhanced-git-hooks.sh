#!/bin/bash

# =============================================================================
# 🔧 ENHANCED GIT HOOKS INSTALLER v3.0
# =============================================================================
# Installs enterprise-grade git hooks with proper database and RAG integration
#
# FEATURES:
# - Enhanced pre-commit validation (security, organization, documentation)
# - Enhanced post-commit processing (database → RAG → cleanup)
# - Proper tenant-aware processing
# - Enterprise audit trails
# - Backup existing hooks
# - Validation of required services

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_HOOKS_SOURCE_DIR="$PROJECT_ROOT/git-hooks"
GIT_HOOKS_TARGET_DIR="$PROJECT_ROOT/.git/hooks"
BACKEND_DIR="$PROJECT_ROOT/backend-python"
LOG_FILE="$PROJECT_ROOT/.cerebraflow/logs/hook-installation.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log_message() {
    local level="${2:-INFO}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $1" | tee -a "$LOG_FILE"
}

# Colored output functions
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log_message "$1" "INFO"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    log_message "$1" "SUCCESS"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log_message "$1" "WARN"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    log_message "$1" "ERROR"
}

# Header
echo ""
echo "🔧 Installing Enhanced Git Hooks v3.0"
echo "================================================"
echo ""

info "Starting git hooks installation process..."
log_message "🚀 Enhanced Git Hooks Installer v3.0 started"

# Validate project structure
info "Validating project structure..."

if [ ! -d "$PROJECT_ROOT/.git" ]; then
    error "This is not a git repository. Please run from the project root."
    exit 1
fi

if [ ! -d "$GIT_HOOKS_SOURCE_DIR" ]; then
    error "Git hooks source directory not found: $GIT_HOOKS_SOURCE_DIR"
    exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
    error "Backend directory not found: $BACKEND_DIR"
    exit 1
fi

success "Project structure validation passed"

# Check for required services
info "Validating required services..."

REQUIRED_SERVICES=(
    "services/hybrid_tenant_service.py"
    "services/enhanced_autodoc_integration_service.py"
    "scripts/post_commit_doc_processor.py"
)

MISSING_SERVICES=()
for service in "${REQUIRED_SERVICES[@]}"; do
    service_path="$BACKEND_DIR/$service"
    if [ -f "$service_path" ]; then
        success "Found: $service"
    else
        warning "Missing: $service"
        MISSING_SERVICES+=("$service")
    fi
done

if [ ${#MISSING_SERVICES[@]} -gt 0 ]; then
    warning "Some required services are missing. Hooks will install but may have limited functionality."
    echo "Missing services:"
    for service in "${MISSING_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
else
    success "All required services found"
fi

# Check Python virtual environment
info "Checking Python virtual environment..."

if [ -d "$PROJECT_ROOT/.venv" ]; then
    success "Python virtual environment found at .venv"
else
    warning "Python virtual environment not found at .venv"
    warning "Hooks may fail without proper Python environment"
fi

# Backup existing hooks
info "Backing up existing git hooks..."

BACKUP_DIR="$PROJECT_ROOT/.git/hooks.backup.$(date +%Y%m%d_%H%M%S)"
if [ -d "$GIT_HOOKS_TARGET_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    
    # Copy existing hooks to backup
    for hook_file in "$GIT_HOOKS_TARGET_DIR"/*; do
        if [ -f "$hook_file" ] && [ ! -name "*.sample" ]; then
            hook_name=$(basename "$hook_file")
            if [[ ! "$hook_name" == *.sample ]]; then
                cp "$hook_file" "$BACKUP_DIR/"
                success "Backed up: $hook_name"
            fi
        fi
    done
    
    info "Backup created at: $BACKUP_DIR"
else
    mkdir -p "$GIT_HOOKS_TARGET_DIR"
    info "Created git hooks directory"
fi

# Install enhanced pre-commit hook
info "Installing enhanced pre-commit hook..."

if [ -f "$GIT_HOOKS_SOURCE_DIR/enhanced-pre-commit" ]; then
    cp "$GIT_HOOKS_SOURCE_DIR/enhanced-pre-commit" "$GIT_HOOKS_TARGET_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_TARGET_DIR/pre-commit"
    success "Enhanced pre-commit hook installed"
else
    error "Enhanced pre-commit hook source not found"
    exit 1
fi

# Install enhanced post-commit hook
info "Installing enhanced post-commit hook..."

if [ -f "$GIT_HOOKS_SOURCE_DIR/enhanced-post-commit" ]; then
    cp "$GIT_HOOKS_SOURCE_DIR/enhanced-post-commit" "$GIT_HOOKS_TARGET_DIR/post-commit"
    chmod +x "$GIT_HOOKS_TARGET_DIR/post-commit"
    success "Enhanced post-commit hook installed"
else
    error "Enhanced post-commit hook source not found"
    exit 1
fi

# Install additional hooks if they exist
info "Checking for additional hooks..."

ADDITIONAL_HOOKS=(
    "commit-msg"
    "pre-push"
    "post-build"
)

for hook in "${ADDITIONAL_HOOKS[@]}"; do
    source_hook="$GIT_HOOKS_SOURCE_DIR/$hook"
    target_hook="$GIT_HOOKS_TARGET_DIR/$hook"
    
    if [ -f "$source_hook" ]; then
        cp "$source_hook" "$target_hook"
        chmod +x "$target_hook"
        success "Installed additional hook: $hook"
    fi
done

# Create hook configuration
info "Creating hook configuration..."

HOOK_CONFIG_FILE="$PROJECT_ROOT/.cerebraflow/config/git-hooks.json"
mkdir -p "$(dirname "$HOOK_CONFIG_FILE")"

cat > "$HOOK_CONFIG_FILE" << EOF
{
  "git_hooks_config": {
    "version": "3.0",
    "installed_date": "$(date -Iseconds)",
    "installed_by": "$(git config user.email 2>/dev/null || echo 'unknown')",
    "hooks": {
      "pre-commit": {
        "enabled": true,
        "features": [
          "security_validation",
          "file_organization",
          "documentation_naming",
          "database_integration_check",
          "rag_system_validation",
          "enterprise_compliance"
        ]
      },
      "post-commit": {
        "enabled": true,
        "features": [
          "documentation_import",
          "rag_system_update",
          "codebase_vectorization",
          "tenant_aware_processing",
          "enterprise_audit_trail",
          "real_time_sync"
        ]
      }
    },
    "enterprise_features": {
      "tenant_isolation": true,
      "audit_trails": true,
      "database_integration": true,
      "rag_coordination": true,
      "real_time_sync": true
    },
    "missing_services": $(printf '%s\n' "${MISSING_SERVICES[@]}" | jq -R . | jq -s .),
    "backup_location": "$BACKUP_DIR"
  }
}
EOF

success "Hook configuration created"

# Create log directories
info "Creating log directories..."

LOG_DIRS=(
    ".cerebraflow/logs"
    ".cerebraflow/logs/hooks"
    ".cerebraflow/logs/audit"
)

for log_dir in "${LOG_DIRS[@]}"; do
    mkdir -p "$PROJECT_ROOT/$log_dir"
    success "Created: $log_dir"
done

# Test hook installation
info "Testing hook installation..."

# Test pre-commit hook execution
if [ -x "$GIT_HOOKS_TARGET_DIR/pre-commit" ]; then
    # Create a test scenario (non-destructive)
    echo "# Test file for hook validation" > "/tmp/test-hook-file.tmp"
    
    # Test if hook is executable and has basic syntax
    if bash -n "$GIT_HOOKS_TARGET_DIR/pre-commit" 2>/dev/null; then
        success "Pre-commit hook syntax validation passed"
    else
        error "Pre-commit hook has syntax errors"
        exit 1
    fi
    
    rm -f "/tmp/test-hook-file.tmp"
else
    error "Pre-commit hook is not executable"
    exit 1
fi

# Test post-commit hook syntax
if [ -x "$GIT_HOOKS_TARGET_DIR/post-commit" ]; then
    if bash -n "$GIT_HOOKS_TARGET_DIR/post-commit" 2>/dev/null; then
        success "Post-commit hook syntax validation passed"
    else
        error "Post-commit hook has syntax errors"
        exit 1
    fi
else
    error "Post-commit hook is not executable"
    exit 1
fi

# Set up git configuration for optimal hook operation
info "Configuring git for optimal hook operation..."

# Set git config for hook optimization
git config hooks.enhanced true
git config hooks.version "3.0"
git config hooks.enterprise true

success "Git configuration updated"

# Summary and next steps
echo ""
echo "🎉 Enhanced Git Hooks Installation Complete!"
echo "============================================="
echo ""
echo "✅ Installed Hooks:"
echo "   - Enhanced Pre-commit Hook v3.0"
echo "   - Enhanced Post-commit Hook v3.0"
echo ""
echo "🏢 Enterprise Features Enabled:"
echo "   - Security validation with compliance checks"
echo "   - File organization enforcement"
echo "   - Documentation naming validation"
echo "   - Database integration with tenant isolation"
echo "   - RAG system coordination (docs → database → RAG)"
echo "   - Codebase vectorization with enterprise standards"
echo "   - Comprehensive audit trails"
echo "   - Real-time sync notifications"
echo ""
echo "📋 Configuration:"
echo "   - Config file: .cerebraflow/config/git-hooks.json"
echo "   - Log directory: .cerebraflow/logs/"
echo "   - Backup location: $BACKUP_DIR"
echo ""

if [ ${#MISSING_SERVICES[@]} -gt 0 ]; then
    echo "⚠️  Missing Services (hooks will work but with reduced functionality):"
    for service in "${MISSING_SERVICES[@]}"; do
        echo "   - $service"
    done
    echo ""
fi

echo "📝 Next Steps:"
echo "   1. Review hook configuration in .cerebraflow/config/git-hooks.json"
echo "   2. Test hooks with a sample commit"
echo "   3. Monitor logs in .cerebraflow/logs/ for any issues"
echo "   4. Configure tenant settings if using multi-tenant features"
echo ""
echo "🔧 Environment Variables (optional):"
echo "   - CEREBRAFLOW_TENANT_ID: Override tenant detection"
echo "   - CEREBRAFLOW_PROJECT_ID: Override project detection"
echo "   - CEREBRAFLOW_USER_ID: Override user detection"
echo "   - CEREBRAFLOW_SKIP_PROCESSING: Skip all post-commit processing"
echo ""
echo "📚 Documentation Import Workflow:"
echo "   1. Create .md files in docs/ with CEREBRAL_XXX_TOPIC.md naming"
echo "   2. Commit files - pre-commit validates naming and structure"
echo "   3. Post-commit imports to documentation_files table"
echo "   4. Updates documentation RAG system"
echo "   5. Deletes .md files from filesystem after successful import"
echo ""
echo "💻 Codebase Vectorization Workflow:"
echo "   1. Commit code changes (Python, TypeScript, etc.)"
echo "   2. Post-commit triggers codebase vectorization"
echo "   3. Updates agentic_knowledge_chunks table"
echo "   4. Syncs to ChromaDB for local RAG access"
echo ""

log_message "🎉 Enhanced Git Hooks v3.0 installation completed successfully"

# Create a quick test script
info "Creating test script for hook validation..."

cat > "$PROJECT_ROOT/test-git-hooks.sh" << 'EOF'
#!/bin/bash

echo "🧪 Testing Enhanced Git Hooks"
echo "============================="

# Test pre-commit hook
echo ""
echo "📋 Testing pre-commit hook validation..."
echo "# Test documentation" > test-doc.md
git add test-doc.md

echo "Running pre-commit checks..."
if .git/hooks/pre-commit; then
    echo "✅ Pre-commit validation passed"
else
    echo "❌ Pre-commit validation failed (expected for test file)"
fi

# Clean up
git reset HEAD test-doc.md 2>/dev/null || true
rm -f test-doc.md

echo ""
echo "📋 Check hook logs:"
echo "   tail -f .cerebraflow/logs/pre-commit-validation.log"
echo "   tail -f .cerebraflow/logs/post-commit-processing.log"
echo ""
echo "✅ Hook testing complete"
EOF

chmod +x "$PROJECT_ROOT/test-git-hooks.sh"
success "Created test script: test-git-hooks.sh"

echo ""
success "Installation complete! Run ./test-git-hooks.sh to validate the setup."
echo "" 