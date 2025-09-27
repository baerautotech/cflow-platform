#!/bin/bash

echo "🔧 MANUAL GRAFANA DASHBOARD DEPLOYMENT"
echo "======================================"
echo ""

echo "1. Applying Grafana dashboard provisioning ConfigMap..."
kubectl apply -f infrastructure/kubernetes/grafana-dashboard-provisioning.yaml

echo ""
echo "2. Checking if ConfigMap was created..."
kubectl get configmap grafana-dashboard-provisioning -n monitoring

echo ""
echo "3. Restarting Grafana deployment..."
kubectl rollout restart deployment/grafana -n monitoring

echo ""
echo "4. Waiting for Grafana to restart..."
kubectl rollout status deployment/grafana -n monitoring --timeout=300s

echo ""
echo "5. Checking Grafana pod status..."
kubectl get pods -n monitoring -l app=grafana

echo ""
echo "6. Checking ConfigMap content..."
kubectl describe configmap grafana-dashboard-provisioning -n monitoring

echo ""
echo "✅ Manual deployment complete!"
echo "🌐 Check Grafana: https://grafana.dev.cerebral.baerautotech.com"
echo "📊 Look for 'BMAD Monitoring' folder in Dashboards"
