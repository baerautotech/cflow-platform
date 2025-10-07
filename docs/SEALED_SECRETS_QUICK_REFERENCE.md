# Sealed Secrets Quick Reference (cflow-platform)

Sync with `cerebral-deployment/docs/SEALED_SECRETS_QUICK_REFERENCE.md` to stay current. GitHub Actions and webhook deployments consume the same instructions.

---

## Commands

```bash
# Inventory (run from cerebral-deployment repo)
./scripts/secrets/list-sealed-secrets.sh

# Compliance monitor
kubectl get configmap sealed-secrets-compliance-monitor -n kube-system \
  -o jsonpath='{.data.monitor\.sh}' | bash
```

## Create / Update Secret

```bash
kubectl create secret generic my-secret \
  --namespace cerebral-development \
  --from-literal=username=admin \
  --from-literal=password='S3cur3!' \
  --dry-run=client -o yaml > my-secret.yaml

kubeseal --fetch-cert --controller-name sealed-secrets \
  --controller-namespace kube-system > sealed-secrets-cert.pem

kubeseal --cert sealed-secrets-cert.pem \
  --namespace cerebral-development \
  --name my-secret \
  --format yaml < my-secret.yaml > my-secret.sealed.yaml

mv my-secret.sealed.yaml ../cerebral-deployment/sealed-secrets/backups/cerebral-development/

git -C ../cerebral-deployment add sealed-secrets/backups/cerebral-development/my-secret.sealed.yaml
git -C ../cerebral-deployment commit -m "Add sealed secret for my-secret"
kubectl apply -f ../cerebral-deployment/sealed-secrets/backups/cerebral-development/my-secret.sealed.yaml
```

## Rotation

```bash
../cerebral-deployment/sealed-secrets/controller-artifacts/restore_and_reseal.sh \
  -k ../cerebral-deployment/sealed-secrets/controller-artifacts/<old-key>.pem \
  -c ../cerebral-deployment/sealed-secrets/controller-artifacts/<new-cert>.pem
```

## Troubleshooting

- `kubectl get pods -n kube-system -l name=sealed-secrets`
- `kubectl logs -n kube-system -l name=sealed-secrets`
- Reapply sealed manifest if Secret missing.

Keep this file aligned with the canonical doc.


