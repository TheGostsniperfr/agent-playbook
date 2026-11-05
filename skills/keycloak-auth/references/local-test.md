# Local end-to-end test

Run the real Keycloak, the real theme JAR and the real Terraform, then drive passkeys with a
Chrome virtual authenticator. About ten minutes; it caught two bugs that review missed (a first
login that always failed, and a login page reloading forever).

## 1. Keycloak with the theme

```sh
mkdir -p providers && cp dist_keycloak/keycloak-theme-for-kc-all-other-versions.jar providers/
docker run -d --name kc-test -p 18080:8080 \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
  -v "$PWD/providers:/opt/keycloak/providers:ro" \
  quay.io/keycloak/keycloak:<server version> start-dev --spi-theme--cache-themes=false
```
After a new JAR: copy it and `docker restart kc-test` (dev mode keeps the database).

## 2. Apply the Terraform to it

Copy only the Keycloak files of the real config into a scratch folder, with a provider block on
`http://localhost:18080` (`admin-cli`, admin/admin) and the RP ID variable set to `localhost`
(WebAuthn accepts `http://localhost` as a secure context). `terraform apply`, then read back
what matters: `kcadm.sh get realms/<realm> --fields browserFlow,passwordPolicy,loginTheme`.
Reset a test user between runs with `terraform apply -replace='keycloak_user.x["name"]'` and
`kcadm.sh set-password ... --temporary`.

## 3. Playwright with a virtual authenticator

```js
const ctx = await browser.newContext({ colorScheme: "dark" });
const page = await ctx.newPage();
const cdp = await ctx.newCDPSession(page);
await cdp.send("WebAuthn.enable");
const { authenticatorId } = await cdp.send("WebAuthn.addVirtualAuthenticator", { options: {
  protocol: "ctap2", transport: "internal", hasResidentKey: true,
  hasUserVerification: true, isUserVerified: true, automaticPresenceSimulation: true } });
```
- Drive required actions by `window.kcContext.pageId`: `login-config-totp.ftl` (TOTP from
  `kcContext.totp.totpSecretEncoded`, RFC 6238 in a few lines of `crypto`),
  `login-recovery-authn-code-config.ftl` (codes in
  `kcContext.recoveryAuthnCodesConfigBean.generatedRecoveryAuthnCodesList`),
  `webauthn-register.ftl` (the "Register" button), `login-update-password.ftl`.
- Export the passkey with `WebAuthn.getCredentials` and add it to a fresh context with
  `WebAuthn.addCredential` to test a passkey-only login. The conditional UI picks it on its
  own; assert that no `login-otp.ftl` page appears and the client URL is reached.
- Reusing an exported credential in a second context replays its sign counter: Keycloak logs
  "Malicious counter value is detected". That is the test, not the config; bump `signCount`.
- Read failures in `docker logs kc-test | grep LOGIN_ERROR`: the event carries the real reason
  (`not_allowed`, `invalid_user_credentials`, the WebAuthn error detail).

## Playwright on NixOS

Downloaded browsers do not run (missing shared libraries). Point Playwright at the nixpkgs
build, aliased to the revision the npm package expects:
```sh
B=$(nix build --no-link --print-out-paths nixpkgs#playwright-driver.browsers)
mkdir -p pw && ln -s $B/chromium_headless_shell-* pw/chromium_headless_shell-<expected rev>
export PLAYWRIGHT_BROWSERS_PATH=$PWD/pw PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
```
The expected revision is in the "Executable doesn't exist at .../chromium_headless_shell-NNNN"
error.
