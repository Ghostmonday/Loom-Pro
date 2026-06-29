# Domains Inventory

**Owner:** Neural Draft LLC  
**Last updated:** _YYYY-MM-DD_  
**Purpose:** Single source of truth for every domain — registrar, expiry, lock status, DNS host.

Fill one row per domain. Update within 24 hours of any change.

---

## Summary

| Metric | Count |
|---|---|
| Total domains | |
| Active | |
| Locked / disputed | |
| Expiring in 30 days | |
| Backup / variation domains | |

---

## Primary domains

| Domain | Registrar | Expiry date | Status | DNS host | Nameservers | Auto-renew | Registrar lock | Notes |
|---|---|---|---|---|---|---|---|---|
| neuraldraft.net | Namecheap | | 🔴 Locked account / ⬜ Active / ⬜ Expired | | | ⬜ On / ⬜ Off | ⬜ On / ⬜ Off | Primary site — deploy `campaign/website/` |
| | | | | | | | | |
| | | | | | | | | |

**Status values:** `Active` · `Locked (account)` · `Locked (registrar)` · `Expired` · `Pending transfer` · `Redemption` · `Backup` · `Parked`

---

## Backup / variation domains

_Register here if primary recovery stalls (see NAMECHEAP-RECOVERY.md §6)._

| Domain | Registrar | Expiry date | Status | DNS host | Forwards to | Notes |
|---|---|---|---|---|---|---|
| | | | | | | e.g. temp landing during NC lock |
| | | | | | | |

---

## DNS record sheet (per domain)

_Copy this block for each production domain._

### `neuraldraft.net`

| Type | Host | Value | TTL | Proxy/CDN | Purpose |
|---|---|---|---|---|---|
| A | @ | | Auto | | Apex / origin |
| CNAME | www | | Auto | | WWW |
| TXT | @ | | Auto | | SPF / verification |
| MX | @ | | Auto | | Mail |
| | | | | | |

**Current nameservers (from `dig NS`):**
```
(paste output)
```

**WHOIS last checked:** _date_  
**WHOIS registrant email:**  
**WHOIS expiry:**  

---

## Registrar account map

| Registrar | Account email | Username | 2FA enabled | Account status | Support contacts used |
|---|---|---|---|---|---|
| Namecheap | | | ⬜ Yes / ⬜ No | 🔴 Locked / ⬜ OK | security@ / accountaccess@ / ticket # |
| Cloudflare | | | ⬜ Yes / ⬜ No | ⬜ OK | |
| | | | | | |

---

## Renewal calendar

| Domain | Expiry | Days until expiry | Auto-renew | Payment method (last4) | Action needed |
|---|---|---|---|---|---|
| neuraldraft.net | | | | | |
| | | | | | |

---

## Recovery / incident log

| Date | Domain | Event | Action taken | Outcome |
|---|---|---|---|---|
| | neuraldraft.net | Namecheap account locked | See NAMECHEAP-RECOVERY.md | Pending |
| | | | | |

---

## Quick commands (audit)

```bash
# Replace DOMAIN
DOMAIN=neuraldraft.net
whois $DOMAIN | grep -iE 'registrar|expir|status|name server'
dig NS $DOMAIN +short
dig A $DOMAIN +short
```

---

## Related docs

- [NAMECHEAP-RECOVERY.md](./NAMECHEAP-RECOVERY.md) — account unlock playbook
- `campaign/website/` — static site ready to deploy on unlock