# Lessons Learned

## Vercel: Changing the Production Branch

**Problem:** Needed to deploy from `dev` branch instead of `main` on Vercel. The branch setting is NOT under Settings → Git (which only has a "Connected Git Repository" section).

**Solution:** Go to **Settings → Environment** — the production branch can be configured there.

**Why we got it wrong:** Relied on outdated knowledge of the Vercel UI instead of checking the actual current interface. The setting used to be under Git settings but has since moved.
