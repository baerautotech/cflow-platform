#!/bin/bash

# Setup Vault Access for BMAD Development
# This script sets up port-forward to access the cerebral cluster vault

echo "🧙 BMAD-MASTER: Setting up Vault access..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if vault port-forward is already running
if pgrep -f "kubectl port-forward.*vault" > /dev/null; then
    echo "✅ Vault port-forward already running"
else
    echo "🚀 Starting vault port-forward..."
    kubectl port-forward -n cerebral-infrastructure svc/vault 8200:8200 &
    sleep 3
fi

# Test vault connection
echo "🔍 Testing vault connection..."
if curl -s http://localhost:8200/v1/sys/health > /dev/null; then
    echo "✅ Vault is accessible at http://localhost:8200"
    echo "🔑 Using token: root-token-12345"
    echo ""
    echo "🚀 Ready to test vault integration!"
    echo "Run: uv run python3 -c \"from cflow_platform.core.vault_integration import test_vault_integration; test_vault_integration()\""
else
    echo "❌ Vault connection failed. Check if port-forward is running."
    echo "Run: kubectl port-forward -n cerebral-infrastructure svc/vault 8200:8200"
fi

