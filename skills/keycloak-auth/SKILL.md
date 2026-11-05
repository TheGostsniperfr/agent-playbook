---
name: keycloak-auth
description: "Set up or upgrade a Keycloak (26.x) deployment to state-of-the-art sign-in: passkeys first (1Password, platform, YubiKey), password plus second factor as fallback, recovery codes, realm-wide flow with RBAC, long sessions with step-up, a hardened master realm, and a branded Keycloakify login and account theme with light and dark mode. Terraform (keycloak/keycloak provider) for every realm setting. Use when deploying a new Keycloak, auditing an existing realm, adding passkeys or MFA, building or fixing a Keycloakify theme, or when asked how a login flow should work."
compatibility: "Keycloak 26.4 or later (passkeys supported). Terraform provider keycloak/keycloak 5.8.0 or later. Keycloakify 11 for themes. Docker and Playwright for the local test."
metadata:
  version: "0.1.0"
  author: "Brian Perret"
---

# Keycloak sign-in, state of the art

Target: a login that takes one touch and is phishing-resistant, with fallbacks that never lock
anyone out, every setting in Terraform, and a theme that looks like the product on every page
(login, account, emails). First built for Arffornia (Keycloak 26.5, 2026-11).

## 1. Decide (ask only what the code cannot answer)
Pick the column of [references/playbook.md](references/playbook.md): internal team, community
of users, B2B multi-tenant, regulated, CLI. It sets the primary method, the fallback, external
identity providers, registration and session lengths. Ask the owner one question when the
audience is unclear: "who signs in here, and do they already have an account elsewhere?"

## 2. Audit an existing realm
Read the realm, flows, clients and theme. Check at least:
- WebAuthn policies: an RP ID left at an example value breaks every registration.
- Which flow each client uses: per-client overrides leave other clients on the built-in flow,
  often without the RBAC check.
- Dead executions (Kerberos, IdP redirector with no IdP), forced password expiry, short
  passwords, `max_login_failures` far above 10.
- Theme name in the JAR vs `login_theme` in the realm; image pinned by tag, not `latest`;
  which theme types exist (login, account, email).

## 3. Implement, one PR per concern
Terraform shapes, ids and config keys verified against the Keycloak 26.5 source are in
[references/terraform.md](references/terraform.md). Order that never locks anyone out:
1. Theme release with the conditional UI fix (section 5) **before** passkeys are enabled.
2. Provider ≥ 5.8.0; WebAuthn passwordless policy with `passwordless_passkeys_enabled`, RP ID
   = registrable domain, user verification `required`; WebAuthn 2FA policy for security keys.
3. New browser flow next to the old one, bound to one low-risk client. Users register their
   passkey, security key and recovery codes in the account console. Test all three paths.
4. Bind the new flow at realm level (`keycloak_authentication_bindings`), delete the old one.
5. Master realm: password plus a mandatory security key (Terraform keeps using direct grant).
6. Remember-me sessions (14 d idle, 30 d max), NIST password policy, brute force at 10.
7. Step-up for sensitive clients: `max_age` on the client side, or ACR to LoA mapping.

## 4. Test before handing over
Run the real thing locally: [references/local-test.md](references/local-test.md) (Keycloak in
Docker with the theme JAR, the Terraform applied to it, Playwright with a CDP virtual
authenticator). Prove: first-login enrolment of a new account, passkey-only login with no OTP
page, password plus OTP, recovery code, master realm key prompt. A screenshot per step.

## 5. Theme (Keycloakify)
Stack, gotchas and the patterns that work: [references/keycloakify-theme.md](references/keycloakify-theme.md).
The ones that cost hours:
- The shadcn login extension and `@keycloakify/login-ui-storybook` ship the same 39 story files:
  their copies corrupt each other in `node_modules/.cache/keycloakify`. Keep one.
- The conditional (autofill) passkey request must only submit a picked passkey. Submitting its
  error reloads the page and restarts the request: an endless reload loop as soon as a browser
  rejects the silent request.
- `early-color-scheme.js` only runs from `public/keycloak-theme/<themeType>/`.
- The account console must match the server's Keycloak version (`2605xx` for 26.5), and its
  `allowObjectInHTMLChildren: true` breaks type-checking of the login components.
- Ship only the JAR for your Keycloak major in the image: both JARs declare the same theme.

## 6. Document
Next to the Keycloak manifests, a README with: how a user signs in, the rollout order, the
break-glass (`kc.sh bootstrap-admin user` in the pod), and what is not done yet.

## Rules
- Every realm, flow, policy and client setting is Terraform. A UI change is a break-glass,
  followed by a revert and an apply.
- Never put a realm's admin password, client secrets or tfvars values in a skill, doc or log.
- A flow change ships with its local test evidence in the PR body.
- Passkeys and the theme fix go out in the order of section 3, never in one apply.
