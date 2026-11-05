# Which setup for which deployment

## Baseline for every deployment
- Realm, flows, clients, policies and required actions in Terraform.
- Passkeys enabled, RP ID = registrable domain, user verification required.
- One browser flow bound at realm level; 2FA skipped after a passkey; recovery codes offered.
- No forced password expiry, length 12 or more, brute force at 10 failures.
- Master realm for admins only, on its own hostname, security key required (or private network).
- Login, account (Single-Page) and email themes in one JAR, image pinned by tag.
- Login events kept for audit; a documented break-glass.

## By case

| Case | Primary sign-in | Fallback | External IdPs | Registration | Sessions |
|---|---|---|---|---|---|
| Internal team, homelab | Passkey (1Password or platform) | Security key or OTP, recovery codes | None | Closed, accounts in Terraform | Remember me 30 d, step-up on admin tools |
| Community of users | Passkey or an IdP they already have | Password + OTP, reset by email | The accounts they use (Microsoft, Discord, GitHub...) | Open, email verified or via IdP | Remember me 30 d |
| B2B multi-tenant | The customer's SSO | Passkey | One OIDC or SAML IdP per customer, through Organizations | Invitation | Short, set by the customer |
| Regulated or sensitive data | Hardware-bound key, AAGUID allow-list | Recovery codes, admin procedure | Per policy | Closed | Short, step-up everywhere |
| CLI or desktop app | System browser + PKCE (RFC 8252 loopback) | OAuth 2.0 device grant | Inherited | Inherited | Refresh tokens, DPoP where supported |

## Rules of thumb
- Add an external IdP only when users already have that account and it saves them one.
- Require hardware keys only when a password-manager compromise is in the threat model.
- Long sessions call for step-up on destructive actions.
- Security alert emails (new device, credential added) need an SMTP relay: a free tier of a
  transactional mail service with SPF and DKIM on the domain beats self-hosting on a residential IP.
