# Grafana Dashboard Troubleshooting Guide

## Problem: No Dashboards Visible in Grafana

### **Root Cause**
The ConfigMaps we created contain dashboard JSON, but they're not automatically imported into Grafana. ConfigMaps are just data storage - they don't create dashboards in Grafana's UI.

### **Solutions**

## **Solution 1: Automatic Dashboard Provisioning (Recommended)**

Run the setup script to enable automatic dashboard provisioning:

```bash
./scripts/setup-grafana-dashboards.sh setup
```

This will:
- Create dashboard provisioning ConfigMaps in the `monitoring` namespace
- Restart Grafana to apply the provisioning
- Set up automatic dashboard discovery

## **Solution 2: Manual Import**

If automatic provisioning doesn't work, manually import the dashboards:

```bash
./scripts/import-grafana-dashboards.sh extract
```

Then:
1. Go to `https://grafana.dev.cerebral.baerautotech.com`
2. Login as admin/developer
3. Navigate to **Dashboards > Import**
4. Copy the JSON from `bmad-enhanced-dashboard.json`
5. Paste into "Import via panel json" text area
6. Click **Load** then **Import**

## **Solution 3: Check Existing Dashboards**

The issue might be that dashboards exist but are in a different folder or have different permissions:

1. **Check Dashboard Folders:**
   - Look for "BMAD Monitoring" folder
   - Check "General" folder
   - Search for "BMAD" in dashboard search

2. **Check User Permissions:**
   - Ensure admin/developer users have dashboard read permissions
   - Check if dashboards are in a restricted folder

3. **Check Data Sources:**
   - Verify Prometheus data source is configured
   - Ensure it's scraping BMAD API metrics
   - Check if metrics are actually being collected

## **Troubleshooting Commands**

```bash
# Check if Grafana is running
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana

# Check Grafana logs
kubectl logs -n monitoring deployment/grafana

# Check ConfigMaps
kubectl get configmap -n monitoring | grep dashboard

# Check if BMAD API is running
kubectl get pods -n cerebral-production -l app=bmad-api-production

# Check ServiceMonitor
kubectl get servicemonitor -n cerebral-production

# Check Prometheus targets
kubectl port-forward -n monitoring service/prometheus-operated 9090:9090
# Then visit http://localhost:9090/targets
```

## **Common Issues**

### **1. Dashboards Exist But No Data**
- **Cause**: Prometheus not scraping BMAD API metrics
- **Fix**: Verify ServiceMonitor is applied and BMAD API is running

### **2. Dashboards Not Appearing**
- **Cause**: Dashboard provisioning not configured
- **Fix**: Run the setup script or manually import

### **3. Permission Denied**
- **Cause**: User doesn't have dashboard read permissions
- **Fix**: Check Grafana user roles and folder permissions

### **4. Wrong Namespace**
- **Cause**: ConfigMaps in wrong namespace
- **Fix**: Move ConfigMaps to `monitoring` namespace

## **Verification Steps**

1. **Check Grafana Access:**
   ```bash
   curl -f https://grafana.dev.cerebral.baerautotech.com/api/health
   ```

2. **Check Dashboard Provisioning:**
   ```bash
   kubectl get configmap -n monitoring | grep dashboard
   ```

3. **Check BMAD API Metrics:**
   ```bash
   kubectl port-forward -n cerebral-production service/bmad-api-metrics 8080:8001
   curl http://localhost:8080/bmad/metrics
   ```

4. **Check Prometheus Targets:**
   - Access Prometheus UI
   - Go to Status > Targets
   - Look for `bmad-api-production` target

## **Expected Result**

After successful setup, you should see:
- **BMAD Monitoring** folder in Grafana
- **BMAD API Enhanced Production Dashboard** with 18 panels
- Real-time metrics showing BMAD API status
- All panels displaying data (not "No data")

## **Next Steps**

If dashboards still don't appear:
1. Check Grafana logs for errors
2. Verify Prometheus is scraping metrics
3. Ensure BMAD API is running and healthy
4. Contact the development team with specific error details
