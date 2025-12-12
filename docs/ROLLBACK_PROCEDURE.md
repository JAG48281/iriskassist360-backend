# Production Rollback Procedure

If production errors are observed after a deployment, follow these steps immediately to restore service availability.

## 1. Railway Rollback (Immediate)

1.  Log in to the [Railway Dashboard](https://railway.app/).
2.  Navigate to the `iriskassist360_backend` project.
3.  Go to the **Deployments** tab.
4.  Find the last **successful** deployment (green checkmark).
5.  Click the **three dots** (...) menu and select **Rollback**.

This will immediately redeploy the previous stable image.

## 2. Repository Revert (Codebase)

Once service is restored via Railway UI, revert the problematic changes in the codebase to ensure the `main` branch is stable.

### Automated Script (if available)
```bash
./scripts/rollback.sh <BAD_COMMIT_HASH>
```

### Manual Steps
Open your terminal in the backend repository:

```bash
# 1. Switch to main branch
git checkout main

# 2. Revert the specific commit (create a new commit that undoes changes)
# Replace <commit-hash> with the ID of the bad deployment commit
git revert <commit-hash> -m 1

# 3. Push the reversion to trigger a clean deployment
git push
```

## 3. Fix and Redeploy

1.  Pull the latest `main` (which now includes the revert) to your local machine.
2.  Create a new branch for the fix.
3.  Debug locally using `uvicorn` and `pytest`.
4.  Once fixed, push a new commit.
