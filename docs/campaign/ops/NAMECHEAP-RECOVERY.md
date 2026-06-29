# Namecheap Account Recovery Playbook

**Goal:** Regain access to your Namecheap account and control of `neuraldraft.net` (and any other domains) as fast as possible.

**Reality check:** General support often replies within hours. **Risk Management / fraud locks** routinely take **3–14+ days**. Treat this as a multi-channel campaign, not a single ticket.

---

## 0. First 30 minutes — classify your lock

Before contacting support, figure out **which lock type** you have. The fix depends on it.

| Symptom / message | Lock type | First action |
|---|---|---|
| "Locked for 24 hours" after bad password/username | Brute-force lock | [Reset password](https://ap.www.namecheap.com/ResetPassword) or wait 24h |
| "Too many failed attempts" on trusted-device code | Device verification lock | Wait 15 min, request new code (max 5 resends/hour) |
| Failed 2FA (SMS/TOTP) 3× | 2FA lock | Wait 24h auto-unlock, or contact support |
| "Locked due to suspected fraud" / payment issue / suspicious activity | **Risk Management lock** | Email **security@namecheap.com** immediately |
| Services suspended + ToS violation notice | Permanent suspension | Email **legalandabuse@namecheap.com** — different path |
| Can't log in, no clear message, domains missing | Possible compromise | Reset password + **security@namecheap.com** + live chat |

**Official KB references:**
- [If my account is locked, how can I regain access?](https://www.namecheap.com/support/knowledgebase/article.aspx/10474/44/if-my-account-is-locked-how-can-i-regain-access/)
- [What should I do if my account is compromised?](https://www.namecheap.com/support/knowledgebase/article.aspx/10473/45/what-should-i-do-if-my-account-is-compromised/)
- [Identity and payment verification (Veriff)](https://www.namecheap.com/support/knowledgebase/article.aspx/10520/45/identity-and-payment-verification/)
- [Documents Namecheap may request](https://www.namecheap.com/support/knowledgebase/article.aspx/10465/45/why-we-can-request-the-documents-and-what-they-will-be/)

---

## 1. Contact channels — use all applicable paths same day

Do **not** rely on one channel. Risk cases get stuck in email queues.

### Channel A: Live Chat (fastest for non-risk locks)

- **URL:** https://www.namecheap.com/help-center/live-chat/
- **Best for:** Password reset failures, 2FA issues, "I can't log in" without fraud flag
- **Limitation:** Chat agents often **cannot unlock Risk Management cases**. They can create/escalate tickets and confirm ticket numbers.
- **Script opener:**
  > My account `[USERNAME]` is locked and I cannot access my domains. I am the legitimate owner. Please confirm lock reason and escalate to Risk Management if needed. Ticket/email reference: `[paste if any]`.

### Channel B: Support ticket (creates paper trail)

- **Submit:** https://support.namecheap.com/index.php?/Tickets/Submit
- **Best for:** Documented follow-ups, attaching non-sensitive proof, referencing prior emails
- **Note:** Namecheap states email replies within ~**2 hours** for general support — **not** Risk Management.

### Channel C: Direct department email (use the right inbox)

| Situation | Email |
|---|---|
| Account locked / can't log in | **accountaccess@namecheap.com** |
| Suspected fraud, chargeback, suspicious activity | **security@namecheap.com** |
| Suspended/locked services (abuse/legal) | **legalandabuse@namecheap.com** |
| Domain DNS, renewal, registration (domain-specific) | **domainsupport@namecheap.com** |
| Transfer in/out | **concierge@namecheap.com** |
| Billing / payment disputes | **billing@namecheap.com** |
| General fallback | **support@namecheap.com** |

**Full list:** [How can I request support via email?](https://www.namecheap.com/support/knowledgebase/article.aspx/227/5/how-can-i-request-support-via-email/)

### Escalation order (risk/fraud lock)

1. **security@namecheap.com** — primary for fraud/risk locks (per official KB)
2. **accountaccess@namecheap.com** — parallel copy if login blocked
3. **Live chat** — get ticket # and ask for Risk Management escalation
4. **domainsupport@namecheap.com** — if chat confirms domains are active but account panel locked
5. Day 7+ — reply-all with "follow-up #2" subject prefix; reference all prior ticket IDs

**Support PIN:** Only visible after login (24h validity). You won't have it while locked out — state that explicitly in every message.

---

## 2. Documents to prepare NOW (before they ask)

Namecheap uses **Veriff** for ID verification. They will **not** ask for ID via email attachment — **never send passport/ID attachments over email** (official policy).

### Have ready to submit via Veriff link (when emailed)

- Government photo ID: passport, driver's license, or national ID card
- Selfie matching the ID
- Smartphone with camera, good lighting
- **Veriff link expires in 7 days** — complete immediately; request resend via ticket if expired

### Have ready to cite in email (not as ID attachments)

| Proof type | What to gather |
|---|---|
| **Account identity** | Username, account email, full name on account, billing address |
| **Payment verification** | Card **last 4 digits**, expiration month/year, PayPal email used, screenshot of PayPal/ bank charge to Namecheap (amount + date) |
| **Domain ownership** | List of domains, registration dates if known, registrant email from WHOIS |
| **Domain proof** | Prior renewal receipts, order confirmation emails, EPP/auth code emails (if any) |
| **Address proof** (sometimes requested) | Utility bill or bank statement matching account address |
| **Business proof** (if applicable) | Articles of incorporation, EIN letter, business registration |

### Compromised account checklist (official KB)

If you suspect takeover:

1. Try [password reset](https://ap.www.namecheap.com/ResetPassword)
2. Secure the email account tied to Namecheap (change password, enable 2FA)
3. Check for unauthorized orders, EPP codes, missing domains
4. Contact support immediately
5. Expect temporary domain modification lock during investigation (services may stay up)

---

## 3. Escalation email template — copy, fill, send

**To:** security@namecheap.com  
**CC:** accountaccess@namecheap.com  
**Subject:** URGENT — Account locked — Identity verification ready — `[YOUR_USERNAME]` — Ticket `#[if any]`

```
Hello Namecheap Risk Management,

My Namecheap account is locked and I cannot access the control panel. I am the legitimate account holder and request expedited review and account restoration.

ACCOUNT DETAILS
- Username: [USERNAME]
- Account email: [EMAIL]
- Full name on account: [NAME]
- Support PIN: unavailable (cannot log in)

LOCK DETAILS
- First noticed locked: [DATE/TIME + TIMEZONE]
- Error message (if any): [paste exact text]
- Prior ticket/chat IDs: [list all]
- I have received / not received a Veriff verification link

DOMAINS AT RISK (business-critical)
- neuraldraft.net — [registered YYYY-MM-DD if known] — DNS/hosting needed for active business site
- [other domains]

VERIFICATION I CAN PROVIDE IMMEDIATELY
- Government ID via Veriff (passport/driver license) — ready now
- Payment method: [Visa/MC/PayPal] ending in [LAST4], exp [MM/YY]
- Recent Namecheap charge: $[AMOUNT] on [DATE] — receipt attached
- Billing address on file: [ADDRESS]

REQUEST
1. Confirm the specific reason for the lock
2. Send or re-send Veriff verification link if required
3. Restore account access and remove modification locks on my domains
4. Confirm neuraldraft.net status (active, expiration date, registrar lock state)

I understand verification protects customers. I am ready to complete Veriff immediately upon receipt. Please advise next steps within 24 hours.

Thank you,
[FULL NAME]
[PHONE]
[ALTERNATE EMAIL]
```

**After sending:** Save the sent email, enable read receipts if available, and log the timestamp in the follow-up table below.

---

## 4. Parallel work — claim `neuraldraft.net` DNS while waiting

You **cannot change nameservers or DNS records at Namecheap while the account is locked**. Do not wait idle — pre-stage everything so DNS flips in minutes once access returns.

### Step 1: Public audit (do today)

```bash
# WHOIS — registrar, expiry, status, registrant email
whois neuraldraft.net

# Current nameservers and DNS
dig NS neuraldraft.net +short
dig A neuraldraft.net +short
dig MX neuraldraft.net +short
dig TXT neuraldraft.net +short
```

Record results in `DOMAINS-INVENTORY.md`.

### Step 2: Archive evidence

- Screenshot WHOIS from https://lookup.icann.org/
- Save any Namecheap order/renewal emails for `neuraldraft.net`
- Export `campaign/website/` — site is ready to deploy (see `campaign/website/index.html` comment)

### Step 3: Pre-stage Cloudflare (or other DNS host)

1. Create free Cloudflare account (if you don't have one)
2. Add site `neuraldraft.net` → Cloudflare will show **two nameservers** (e.g. `ada.ns.cloudflare.com`)
3. Pre-configure DNS records you'll need:

| Type | Name | Value | Notes |
|---|---|---|---|
| A | `@` | `[YOUR_HOST_IP]` | Or CNAME to Pages/Netlify |
| CNAME | `www` | `neuraldraft.net` | Or target host |
| TXT | `@` | `[verify tokens]` | Email, search console, etc. |

4. **Do not change NS at registrar yet** — wait until Namecheap unlocks
5. Optional: Deploy static site to **Cloudflare Pages** or **Netlify** now on a `*.pages.dev` / `*.netlify.app` URL for testing

### Step 4: On unlock — DNS cutover (15-minute playbook)

1. Log in → Domain List → `neuraldraft.net` → Domain → Nameservers → Custom DNS
2. Enter Cloudflare nameservers → Save
3. In Cloudflare, confirm zone is "Active" (propagation: 5 min – 48 hrs, usually < 1 hr)
4. Enable SSL/TLS Full (strict) once origin is live
5. Deploy `campaign/website/` to your host
6. Verify: `curl -I https://neuraldraft.net`

### Step 5: If domain was transferred or compromised

- Check WHOIS for unexpected registrant change
- If domain missing from account: cite EPP/unauthorized transfer in email to **security@namecheap.com** + **domainsupport@namecheap.com**
- Enable registrar lock + 2FA immediately after recovery

---

## 5. Timeline expectations and follow-up cadence

| Day | Expected from Namecheap | Your actions |
|---|---|---|
| **Day 0** | Auto-reply; maybe Veriff link within 24–72h for risk cases | Send escalation email + open live chat + start DNS pre-staging |
| **Day 1** | General support may reply in hours; Risk may be silent | Follow up if no Veriff link or human reply in 24h. Re-open live chat with ticket IDs. Complete Veriff same day if link arrives. |
| **Day 3** | Risk review often in progress | Send follow-up #1 (see template below). Confirm domain still resolves. Register backup domain if not done. |
| **Day 7** | Many risk cases resolve by now — not guaranteed | Send follow-up #2. Ask for supervisor/escalated Risk review. Mention business impact + domains at risk. |
| **Day 14** | Long-tail cases | Follow-up #3. Consider **ICANN registrar complaint** path if domain held hostage with no response (last resort). Execute backup domain plan fully. |

### Follow-up email template (Day 3 / 7 / 14)

**Subject:** FOLLOW-UP #[N] — Account lock unresolved since [DATE] — `[USERNAME]`

```
Hello,

Follow-up #[N] on my locked account case.

- Original contact date: [DATE]
- Prior references: [ticket IDs, email subjects]
- Veriff status: [completed DATE / link not received / expired — need resend]
- Domains affected: neuraldraft.net (business site blocked from deployment)

I completed all requested verification steps on [DATE or "awaiting your link"].

Please provide:
1. Current case status and assigned department
2. Estimated resolution date
3. Confirmation that neuraldraft.net remains registered to me and is not scheduled for deletion

Thank you,
[NAME]
```

### Response time reality

| Channel | Official / typical |
|---|---|
| General email support | ~2 hours (per Namecheap KB) |
| Live chat | Minutes to connect; may not solve risk locks |
| Risk Management (security@) | **No SLA published** — commonly 3–14 days |
| Veriff processing | Often same day once submitted |

---

## 6. Backup plan — don't block the business on one registrar

If Day 3 passes with no progress, **stop waiting** and ship on a variation domain.

### Register elsewhere (same day)

Pick one registrar you control independently:

- **Cloudflare Registrar** (at-cost, needs Cloudflare account)
- **Porkbun**, **Google Domains/Squarespace**, **Gandi**, **Hover**

**Variation names to check:**

- `neuraldraft.io` / `neuraldraft.co` / `neuraldraft.dev`
- `getneuraldraft.com` / `neuraldraft.ai`
- `neural-draft.com` / `neuraldraftllc.com`

### Minimal launch config

1. Register variation → point DNS to Cloudflare Pages / Netlify / VPS
2. Deploy `campaign/website/` — update brand strings only if needed
3. Set up email forwarding (e.g. ImprovMX, ForwardEmail, or registrar forwarding)
4. Add redirect rule: variation → `neuraldraft.net` **later** when primary is recovered

### Forwarding after recovery

Once `neuraldraft.net` is back:

```
# Cloudflare bulk redirect or page rule
neuraldraft.net/* → https://[primary]/$1 (301)
# OR reverse if variation became primary during outage
```

Update `DOMAINS-INVENTORY.md` with both domains.

---

## 7. After recovery — lock it down (same session)

- [ ] Change Namecheap password (unique, 20+ chars)
- [ ] Enable 2FA (TOTP app, not SMS)
- [ ] Enable security notifications
- [ ] Verify registrant contact email is yours and secure
- [ ] Enable **Domain Lock** (registrar lock) on all domains
- [ ] Enable **Auto-Renew** + confirm payment method
- [ ] Remove stale API keys / connected apps
- [ ] Export list of domains to `DOMAINS-INVENTORY.md`
- [ ] Consider moving DNS to Cloudflare (nameservers) for resilience
- [ ] Save Support PIN workflow for future chats

---

## 8. Quick reference card

```
LOCKED (fraud/risk)     → security@namecheap.com + accountaccess@namecheap.com
LOCKED (login only)     → Live chat + accountaccess@namecheap.com
COMPROMISED             → Password reset + secure email + security@namecheap.com
DOMAIN DNS (unlocked)   → domainsupport@namecheap.com
VERIFF LINK EXPIRED     → Ticket resend request (7-day validity)
ID DOCUMENTS            → Veriff ONLY — never email attachments
SITE READY TO SHIP      → campaign/website/ → deploy on unlock or backup domain
```

---

## 9. Case log (fill in as you go)

| Date | Action | Channel | Reference # | Response |
|---|---|---|---|---|
| | Initial escalation sent | security@ | | |
| | Live chat | Chat | | |
| | Ticket opened | Ticket | | |
| | Veriff completed | Veriff | | |
| | Follow-up #1 (Day 3) | Email | | |
| | Follow-up #2 (Day 7) | Email | | |
| | Account restored | — | | |
| | neuraldraft.net DNS live | Cloudflare/NC | | |

---

*Last updated: 2026-06-15. Sources: Namecheap KB articles 10474, 10473, 10520, 10465, 227, 1125.*