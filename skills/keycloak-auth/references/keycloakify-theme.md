# Keycloakify theme: login, account, email

Stack that works with Keycloak 26.5: Keycloakify 11, React 19, Tailwind 4,
`@oussemasahbeni/keycloakify-login-shadcn` (every login page, passkey pages included, with
stories), `@keycloakify/keycloak-account-ui` for the account console.

## Theme types

| Type | Use | Notes |
|---|---|---|
| login | Always | shadcn extension; base is Keycloak 25 templates, works on 26.5 |
| account | Always | **Single-Page** (`accountThemeImplementation: "Single-Page"`): the real v3 console, passkeys, security keys, OTP, recovery codes, sessions. Multi-Page is the old console, with no passkey management |
| email | When an SMTP relay exists | `npx keycloakify initialize-email-theme` |
| admin | Only if non-technical people administer the realm | `@keycloakify/keycloak-admin-ui` |

## Gotchas (each one cost real time)

1. **Duplicate extensions.** `@keycloakify/login-ui-storybook` and the shadcn extension ship
   the same 39 `Page.stories.tsx` and `mocks/KcPageStory.tsx`. Their copies collide in
   `node_modules/.cache/keycloakify/extension-modules`, leaving truncated files and random
   `tsc` failures. Remove the storybook extension; to recover a broken checkout:
   `rm -rf node_modules/.cache/keycloakify src/login/pages/*/Page.stories.tsx && npx keycloakify sync-extensions`.
2. **Passkey autofill reload loop.** In `login/components/WebAuthnConditionalUi/useLogic.tsx`
   (own it first), the conditional request must submit only `result.success`. Posting its error
   reloads the page, which starts the same request again: endless reloads whenever a browser,
   a password manager or headless Chromium rejects the silent request ("Resident credentials or
   empty allowCredentials lists are not supported"). The modal button may keep posting errors.
3. **Early color scheme.** Keycloakify injects `public/keycloak-theme/<themeType>/early-color-scheme.js`
   in `<head>`. The shadcn extension ships it at `public/keycloak-theme/early-color-scheme.js`,
   where it never runs, so dark pages flash white. Put yours under `login/` and `account/`.
4. **Account console version.** `npx keycloakify initialize-account-theme` installs the latest
   (26.7 today). Pin `@keycloakify/keycloak-account-ui` to the server's minor (`260502.0.2` for
   26.5); `sync-extensions` then aligns `keycloak-ui-shared` and the admin client.
5. **`allowObjectInHTMLChildren`.** The account extension sets it `true` in
   `account/i18next.d.ts`, which widens React children types project-wide and breaks the shadcn
   components (`ReactI18NextChildren` errors). Own the file and set `false`: the account pages
   are `@ts-nocheck`.
6. **Two JARs.** `keycloakify build` emits a 22-to-25 JAR and an all-other-versions JAR with the
   same theme name. Copy only the one for your Keycloak major into `/providers`.
7. **Theme name** comes from `themeName` in `vite.config.ts` (else `package.json` name). Keep it
   equal to `login_theme`/`account_theme` in Terraform; a mismatch silently falls back to the
   built-in theme.
8. **Owning files.** Edit a synced file only after `npx keycloakify own --path "<path>"`
   (`--public` for files under `public/`). `sync-extensions` may rewrite `package.json` (dependency
   ranges, key order): never revert `package.json` blindly after it, reinstall instead.
9. **Building the JAR** needs Maven and a JDK. On NixOS:
   `nix shell nixpkgs#maven nixpkgs#jdk21 -c npx keycloakify build`.

## Light, dark and system

- A three-way selector (System, Light, Dark) stored in `localStorage` under one key, read by the
  React provider, by `login/early-color-scheme.js` and by `account/early-color-scheme.js` plus
  the owned `account/colorScheme.ts`. Login and account share the origin, so one choice applies
  to both.
- "System" listens to `matchMedia("(prefers-color-scheme: dark)")` changes, not only at load.
- Respect `kcContext.darkMode === false` (realm setting) by forcing light.

## Brand and motion that stay fast

- Palette as CSS variables over the shadcn tokens, in a file imported by the owned
  `Template.tsx`, selectors one notch more specific (`html:root`, `html.dark`).
- Fonts as WOFF2, subset with `pyftsubset --flavor=woff2` (Latin ranges): a wordmark font drops
  from 78 KB to 7 KB.
- A looping background (WebM VP9, 720p, 6 s, about 300 KB) with a JPEG poster, one per theme
  mode, desktop only, a still under `prefers-reduced-motion`. Never delay the form or redirects.
- A status light on the card: idle brand colour, a pulse while a form submits or a security key
  is awaited (`webauthn-authenticate.ftl`, `webauthn-register.ftl`), hazard stripes on an error.
- Account console (PatternFly 5): override `--pf-v5-global--primary-color--100`,
  `--pf-v5-global--link--Color`, `--pf-v5-global--active-color--400` (nav marker), font
  families; component variables such as `--pf-v5-c-masthead--BackgroundColor` must be set on
  `html .pf-v5-c-masthead`, not on `:root`. White text on a light brand orange fails WCAG AA:
  darken the primary in light mode, use dark text on it in dark mode.
- The account header logo is an `<img>`: web fonts do not load there. Outline the wordmark into
  SVG paths (fontTools `SVGPathPen`) and embed the icon as a data URI.
