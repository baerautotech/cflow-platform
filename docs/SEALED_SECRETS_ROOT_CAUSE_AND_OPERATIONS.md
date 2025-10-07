# Sealed Secrets Confusion Root Cause Analysis & Operations Playbook

This document mirrors the authoritative guide in `cerebral-deployment/docs/SEALED_SECRETS_ROOT_CAUSE_AND_OPERATIONS.md` and ensures cflow-platform agents receive identical instructions. Refer to the original for full context; the highlights below are tailored for BMAD agents working within this repository and the GitHub Actions + webhook deployment path. Inventory snapshots live under `docs/SEALED_SECRETS_INVENTORY.md|json` in the cerebral repository.

---

## 1. Key Takeaways

- **Sealed Secrets is the only supported secret backend.** Vault and External Secrets Operator are retired.
- **Inventory lives in `cerebral-deployment/sealed-secrets/backups/`.** Always check there first.
- **kubeseal CLI is mandatory** for creating or updating secrets. Install on the workstation or use the cluster binaries.
- **Helper scripts exist:** `sealed-secrets/controller-artifacts/restore_and_reseal.sh` (for resealing) and `scripts/secrets/list-sealed-secrets.sh` (inventory).

---

## 2. Common Pitfalls Identified

| Issue | Impact | Fix |
| --- | --- | --- |
| Legacy Vault docs | Agents revert to deprecated flows | Treat any Vault reference as obsolete; follow Sealed Secrets quick reference |
| Lack of quick instructions in `cflow-platform` | Agents assume secrets missing | Use Section 3 below and the TL;DR guide |
| Unknown inventory | Duplicate resealing or missing manifests | Run `scripts/secrets/list-sealed-secrets.sh` from `cerebral-deployment` repo |
| Cert/key rotation confusion | Agents think controller lost keys | Use reseal script with old key + new cert |

---

## 3. Quick Operations

```bash
# List secrets (run from cerebral-deployment)
./scripts/secrets/list-sealed-secrets.sh

# Create plaintext secret (example)
kubectl create secret generic my-secret \
  --namespace cerebral-development \
  --from-literal=username=admin \
  --from-literal=password='S3cur3!' \
  --dry-run=client -o yaml > my-secret.yaml

# Seal with controller cert
kubeseal --fetch-cert --controller-namespace kube-system --controller-name sealed-secrets > sealed-secrets-cert.pem
kubeseal --cert sealed-secrets-cert.pem \
  --namespace cerebral-development \
  --name my-secret \
  --format yaml < my-secret.yaml > my-secret.sealed.yaml

# Move sealed manifest into repo
mv my-secret.sealed.yaml ../cerebral-deployment/sealed-secrets/backups/cerebral-development/

# Commit from cerebral-deployment repo and apply
git add sealed-secrets/backups/cerebral-development/my-secret.sealed.yaml
git commit -m "Add sealed secret for my-secret"
kubectl apply -f sealed-secrets/backups/cerebral-development/my-secret.sealed.yaml
```

---

## 4. Where to Go for More Detail

- `cerebral-deployment/docs/SEALED_SECRETS_ARCHITECTURE.md` – full architecture & troubleshooting.
- `cerebral-deployment/docs/SEALED_SECRETS_ROOT_CAUSE_AND_OPERATIONS.md` – root cause analysis, remediation plan, and inventory snapshot.
- `cerebral-deployment/docs/SEALED_SECRETS_QUICK_REFERENCE.md` – TL;DR guide.

Ensure cflow-platform agents keep these references aligned; updates should land in both repositories.


