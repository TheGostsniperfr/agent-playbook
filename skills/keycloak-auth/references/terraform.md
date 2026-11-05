# Terraform: realm, flows, master realm

Provider `keycloak/keycloak` **5.8.0 or later** (`passwordless_passkeys_enabled` arrived in
5.8.0; tested with 5.10.0 against Keycloak 26.5.5). Upgrade only this provider: `terraform init
-upgrade` also bumps every unpinned provider in the lock file.

## Ids verified in the Keycloak 26.5 source

| What | Id | Config keys |
|---|---|---|
| Username + password form (offers passkeys when enabled) | `auth-username-password-form` | |
| Skip a subflow when a credential type was used | `conditional-credential` | `credentials` (comma list), `included` (`"true"`/`"false"`) |
| Skip a subflow when the user has none of its credentials | `conditional-user-configured` | |
| Step-up condition | `conditional-level-of-authentication` | `loa-condition-level`, `loa-max-age` |
| Passkey credential type | `webauthn-passwordless` | |
| OTP form / security key 2FA / recovery code | `auth-otp-form` / `webauthn-authenticator` / `auth-recovery-authn-code-form` | |
| Required actions | `webauthn-register-passwordless`, `webauthn-register`, `CONFIGURE_RECOVERY_AUTHN_CODES`, `CONFIGURE_TOTP` | |
| Realm attribute for ACR to LoA | `acr.loa.map` | |

Features `PASSKEYS`, `RECOVERY_CODES`, `STEP_UP_AUTHENTICATION` and `WEB_AUTHN` are on by
default in 26.5. The realm switch is the policy attribute below.

## Realm: WebAuthn policies, sessions, passwords

```hcl
resource "keycloak_realm" "this" {
  # ...
  sso_session_idle_timeout             = "10h"
  sso_session_max_lifespan             = "24h"
  sso_session_idle_timeout_remember_me = "336h" # 14 days, fine once logins are passkeys
  sso_session_max_lifespan_remember_me = "720h" # 30 days
  remember_me                          = true

  # NIST SP 800-63B: length over composition, no periodic expiry.
  password_policy = "length(12) and notUsername and notEmail and passwordHistory(3)"

  security_defenses {
    brute_force_detection {
      max_login_failures = 10
      # ...
    }
  }

  # RP ID = the registrable domain (example.com, not auth.example.com): passkeys survive a
  # hostname change. Changing the RP ID later invalidates every registered passkey.
  web_authn_passwordless_policy {
    relying_party_entity_name         = "Example ID"
    relying_party_id                  = "example.com"
    signature_algorithms              = ["ES256", "RS256"]
    user_verification_requirement     = "required"
    require_resident_key              = "Yes" # discoverable_credential = "required" on Keycloak 26.7+
    attestation_conveyance_preference = "none"
    avoid_same_authenticator_register = true
    passwordless_passkeys_enabled     = true
  }

  web_authn_policy { # security key as a second factor
    relying_party_entity_name         = "Example ID"
    relying_party_id                  = "example.com"
    signature_algorithms              = ["ES256", "RS256"]
    user_verification_requirement     = "preferred"
    attestation_conveyance_preference = "none"
    avoid_same_authenticator_register = true
  }
}

resource "keycloak_required_action" "passkey" {
  realm_id       = local.realm_id
  alias          = "webauthn-register-passwordless"
  name           = "Webauthn Register Passwordless"
  enabled        = true
  default_action = true
}
# Same shape for webauthn-register (default_action = false) and CONFIGURE_RECOVERY_AUTHN_CODES.
```

Restricting to hardware keys (regulated case): `acceptable_aaguids` on the policy, and
`authenticator_attachment = "cross-platform"`.

## Browser flow: passkey first (tested)

Shape: cookie | (username-password form, then 2FA unless a passkey was used), then RBAC.

```hcl
# BROWSER FLOW v5: PASSKEY FIRST
# Docs: https://www.keycloak.org/docs/latest/server_admin/index.html#passkeys_server_administration_guide
#
# The username/password form also offers the passkey (conditional UI and a "Sign in with
# Passkey" button) once passwordless_passkeys_enabled is set on the realm. A passkey already
# proves possession and user verification, so the second factor is skipped after one. The
# password path keeps a mandatory second factor: OTP, security key or a recovery code.
# =============================================================================

resource "keycloak_authentication_flow" "browser_v5" {
  realm_id    = local.realm_id
  alias       = "Browser-Passkey-First"
  description = "Passkey first, password plus second factor as fallback, then RBAC"
}

resource "keycloak_authentication_subflow" "v5_login" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_flow.browser_v5.alias
  alias             = "v5-login"
  provider_id       = "basic-flow"
  requirement       = "REQUIRED"
  priority          = 10
}

resource "keycloak_authentication_execution" "v5_cookie" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_login.alias
  authenticator     = "auth-cookie"
  requirement       = "ALTERNATIVE"
  priority          = 10
}

resource "keycloak_authentication_subflow" "v5_forms" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_login.alias
  alias             = "v5-forms"
  provider_id       = "basic-flow"
  requirement       = "ALTERNATIVE"
  priority          = 20
}

resource "keycloak_authentication_execution" "v5_username_password" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_forms.alias
  authenticator     = "auth-username-password-form"
  requirement       = "REQUIRED"
  priority          = 10
}

# Runs when the user has a second factor configured and did not log in with a passkey.
# A user with no second factor yet skips it, then the CONFIGURE_TOTP required action makes them
# set one up before the session opens. Without the user-configured condition the alternatives
# below all fail with "credential setup required" and the first login of a new account errors.
resource "keycloak_authentication_subflow" "v5_second_factor" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_forms.alias
  alias             = "v5-second-factor"
  provider_id       = "basic-flow"
  requirement       = "CONDITIONAL"
  priority          = 20
}

resource "keycloak_authentication_execution" "v5_condition_user_configured" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_second_factor.alias
  authenticator     = "conditional-user-configured"
  requirement       = "REQUIRED"
  priority          = 5
}

resource "keycloak_authentication_execution" "v5_condition_no_passkey" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_second_factor.alias
  authenticator     = "conditional-credential"
  requirement       = "REQUIRED"
  priority          = 10
}

resource "keycloak_authentication_execution_config" "v5_condition_no_passkey" {
  realm_id     = local.realm_id
  execution_id = keycloak_authentication_execution.v5_condition_no_passkey.id
  alias        = "v5-second-factor-unless-passkey"
  config = {
    credentials = "webauthn-passwordless"
    included    = "false"
  }
}

resource "keycloak_authentication_execution" "v5_otp" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_second_factor.alias
  authenticator     = "auth-otp-form"
  requirement       = "ALTERNATIVE"
  priority          = 20
}

resource "keycloak_authentication_execution" "v5_security_key" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_second_factor.alias
  authenticator     = "webauthn-authenticator"
  requirement       = "ALTERNATIVE"
  priority          = 30
}

resource "keycloak_authentication_execution" "v5_recovery_code" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_second_factor.alias
  authenticator     = "auth-recovery-authn-code-form"
  requirement       = "ALTERNATIVE"
  priority          = 40
}

resource "keycloak_authentication_subflow" "v5_rbac" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_flow.browser_v5.alias
  alias             = "v5-rbac"
  provider_id       = "basic-flow"
  requirement       = "CONDITIONAL"
  priority          = 20
}

resource "keycloak_authentication_execution" "v5_condition_role" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_rbac.alias
  authenticator     = "conditional-user-role"
  requirement       = "REQUIRED"
  priority          = 10
}

resource "keycloak_authentication_execution_config" "v5_condition_role" {
  realm_id     = local.realm_id
  execution_id = keycloak_authentication_execution.v5_condition_role.id
  alias        = "v5-deny-without-app-access"
  config = {
    condUserRole = keycloak_role.app_access.name
    negate       = "true"
  }
}

resource "keycloak_authentication_execution" "v5_deny_access" {
  realm_id          = local.realm_id
  parent_flow_alias = keycloak_authentication_subflow.v5_rbac.alias
  authenticator     = "deny-access-authenticator"
  requirement       = "REQUIRED"
  priority          = 20
}

# Realm-wide binding: every client gets the same MFA and the same RBAC check, with no
# per-client override to forget on a new client.
resource "keycloak_authentication_bindings" "arffornia" {
  realm_id     = local.realm_id
  browser_flow = keycloak_authentication_flow.browser_v5.alias
}

# Bind at realm level. Setting browser_flow on keycloak_realm itself creates a dependency cycle
# (the flow needs the realm id), hence the bindings resource.
resource "keycloak_authentication_bindings" "this" {
  realm_id     = local.realm_id
  browser_flow = keycloak_authentication_flow.browser_v5.alias
}
```

Pitfalls met:
- **Without `conditional-user-configured`** in the 2FA subflow, a new account with no second
  factor yet hits only unconfigured ALTERNATIVE executions, the flow throws, and the first login
  shows "Invalid username or password" on the error page. With it, the subflow is skipped and the
  `CONFIGURE_TOTP` required action enrolls the user before the session opens.
- **Per-client `authentication_flow_binding_overrides`**: every client without one silently
  uses the built-in flow. Bind at realm level and drop the overrides.
- **Removing \`authentication_flow_binding_overrides\` from a client does not clear it** in
  Keycloak: the provider sends nothing, the override stays, and deleting the old flow in the
  same apply fails with \`500 unknown_error\` (server log: "Cannot remove authentication flow, it
  is currently in use"). Terraform also deletes the flow before updating the clients, since
  nothing links them any more. Clear the override first, then apply:
  \`kcadm.sh update clients/<id> -r <realm> -s 'authenticationFlowBindingOverrides.browser=""'\`
  (or \`browser_id = ""\` for one targeted apply; leaving that block in causes a permanent diff).
- Rollout: keep the old flow, bind the new one to one client first, test, then switch.

## Master realm: security key on the admin console

Manage only the flow and its binding (`realm_id = "master"`); importing the master realm as a
`keycloak_realm` puts every one of its settings under the state. Flow: cookie | (username +
password REQUIRED, `webauthn-authenticator` REQUIRED), required action `webauthn-register`
enabled. A REQUIRED authenticator the user has not configured triggers its required action, so
the admin registers a key at the next login. Leave the RP ID unset: it defaults to the host
serving the login page, where the key is also registered.

The provider (`admin-cli`, password grant) uses the direct grant flow and keeps working.
Break-glass: `kc.sh bootstrap-admin user` inside the Keycloak pod. Better still: a master
client with a service account and `client_credentials` for the provider.

## Step-up

- Simplest: the client sends OIDC `max_age=300` (Vault: `max_age` on the OIDC role). The user
  re-authenticates with one passkey touch.
- Finer: realm attribute `acr.loa.map`, a `conditional-level-of-authentication` subflow per
  level, clients requesting `acr_values`. Docs:
  https://www.keycloak.org/docs/latest/server_admin/index.html#_step-up-flow
