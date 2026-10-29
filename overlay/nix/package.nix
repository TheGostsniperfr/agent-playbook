# The agentskills resolver and the rendered skill trees, as plain functions of pkgs.
{ pkgs, src ? ../.. }:
let
  inherit (pkgs) lib;
  # Only what the resolver and the skills need, so unrelated edits elsewhere in the repo
  # (runbook/, veille/) do not rebuild anything.
  base = lib.cleanSourceWith {
    name = "agent-playbook-skills";
    src = src;
    filter = path: type:
      let rel = lib.removePrefix (toString src + "/") (toString path);
      in rel == "skills" || lib.hasPrefix "skills/" rel;
  };
in
rec {
  inherit base;

  agentskills = pkgs.stdenvNoCC.mkDerivation {
    pname = "agentskills";
    version = "1.0.0";
    src = src + "/overlay";
    dontBuild = true;
    installPhase = ''
      install -Dm755 agentskills $out/libexec/agentskills
      mkdir -p $out/bin
      cat > $out/bin/agentskills <<EOF
      #!${pkgs.runtimeShell}
      exec ${pkgs.python3}/bin/python3 $out/libexec/agentskills "\$@"
      EOF
      chmod +x $out/bin/agentskills
    '';
    meta = {
      description = "Render generic Agent Skills plus project overlays for Claude Code, Codex and OpenCode";
      mainProgram = "agentskills";
      platforms = lib.platforms.unix;
    };
  };

  # Every base skill rendered in the user-level layout:
  #   $out/claude/playbook/   a personal Claude Code plugin (skills show as /playbook:<name>)
  #   $out/codex/playbook-<name>/, $out/opencode/playbook-<name>/
  # overlay: optional user-level overlay file (YAML or JSON) applied on top of the base.
  renderSkills = { overlay ? null, targets ? [ "claude" "codex" "opencode" ] }:
    pkgs.runCommand "agent-playbook-skills-rendered" { nativeBuildInputs = [ pkgs.python3 ]; } ''
      export HOME=$TMPDIR/home
      python3 ${agentskills}/libexec/agentskills render --user --no-lock \
        --base ${base} --overlay ${if overlay == null then "none" else toString overlay} \
        --target ${lib.concatStringsSep "," targets} >/dev/null
      mkdir -p $out
      if [ -d "$HOME/.claude/skills/playbook" ]; then mkdir -p $out/claude && cp -r "$HOME/.claude/skills/playbook" $out/claude/; fi
      if [ -d "$HOME/.agents/skills" ]; then cp -r "$HOME/.agents/skills" $out/codex; fi
      if [ -d "$HOME/.config/opencode/skills" ]; then cp -r "$HOME/.config/opencode/skills" $out/opencode; fi
      find $out -name .agentskills-managed -delete
    '';

  tests = pkgs.runCommand "agentskills-tests" { nativeBuildInputs = [ pkgs.python3 pkgs.git ]; } ''
    cp -r ${src}/overlay ${src}/skills .
    chmod -R u+w .
    export HOME=$TMPDIR
    python3 -m unittest discover -s overlay/tests
    python3 -m unittest discover -s skills/review-stack/tests
    python3 overlay/agentskills validate skills
    touch $out
  '';
}
