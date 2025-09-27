#!/bin/bash

echo "🔍 COMPREHENSIVE GRAFANA DASHBOARD TROUBLESHOOTING"
echo "================================================="
echo ""

echo "1. Checking workflow status..."
echo "   Go to: https://github.com/baerautotech/cflow-platform/actions"
echo "   Look for: BMAD API Service Build and Deploy, Kubernetes Manifest Deployment"
echo ""

echo "2. Checking if ConfigMaps exist in cluster..."
kubectl get configmap -n monitoring | grep dashboard || echo "   ❌ No dashboard ConfigMaps found"
echo ""

echo "3. Checking Grafana pod status..."
kubectl get pods -n monitoring -l app=grafana
echo ""

echo "4. Checking Grafana deployment..."
kubectl get deployment grafana -n monitoring
echo ""

echo "5. Checking if Grafana has ConfigMap mounted..."
kubectl get deployment grafana -n monitoring -o yaml | grep -A 10 -B 10 dashboard || echo "   ❌ No dashboard ConfigMap mounted"
echo ""

echo "6. Checking Grafana logs for errors..."
kubectl logs -n monitoring deployment/grafana --tail=20 | grep -i error || echo "   ✅ No obvious errors in logs"
echo ""

echo "7. Checking Grafana logs for dashboard provisioning..."
kubectl logs -n monitoring deployment/grafana --tail=50 | grep -i "dashboard\|provisioning" || echo "   ❌ No dashboard provisioning messages"
echo ""

echo "8. Manual ConfigMap application..."
echo "   Applying Grafana dashboard provisioning..."
kubectl apply -f infrastructure/kubernetes/grafana-dashboard-provisioning.yaml
echo ""

echo "9. Restarting Grafana..."
kubectl rollout restart deployment/grafana -n monitoring
echo ""

echo "10. Waiting for Grafana to restart..."
kubectl rollout status deployment/grafana -n monitoring --timeout=300s
echo ""

echo "11. Final check - Grafana pod status..."
kubectl get pods -n monitoring -l app=grafana
echo ""

echo "✅ Troubleshooting complete!"
echo "🌐 Check Grafana: https://grafana.dev.cerebral.baerautotech.com"
echo "📊 Look for 'BMAD Monitoring' folder in Dashboards"
