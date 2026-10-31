# home-manager module: install Brian's generic skills for Claude Code, Codex and OpenCode.
# Works on NixOS (home-manager.users.<name>) and on macOS (nix-darwin + home-manager), or with
# standalone home-manager. See skills/DESIGN.md, section "Nix".
{ src ? ../.. }:
{ config, lib, pkgs, ... }:
let
  cfg = config.programs.agent-playbook;
  p = import ./package.nix { inherit pkgs; src = cfg.source; };
  rendered = p.renderSkills { overlay = overlayFile; targets = cfg.targets; };
  # A selection or exclusion becomes a generated user-level overlay.
  generated = pkgs.writeText "agent-playbook-overlay.json" (builtins.toJSON {
    apiVersion = "agentskills/v1";
    skills = if cfg.skills == null then "*" else cfg.skills;
    exclude = cfg.exclude;
  });
  overlayFile =
    if cfg.overlay != null then cfg.overlay
    else if cfg.skills != null || cfg.exclude != [ ] then generated
    else null;
  userDirs = {
    claude = ".claude/skills";
    codex = ".agents/skills"; # Codex's user dir; ~/.codex/skills is legacy and not deduplicated
    opencode = ".config/opencode/skills";
  };
  # Names known at evaluation time (no import-from-derivation): the base skill folders,
  # narrowed by `skills` / `exclude`. A custom `overlay` that renames or adds skills needs the
  # default copy method, which does not need names.
  baseNames = lib.attrNames (lib.filterAttrs
    (n: t: t == "directory" && builtins.pathExists (cfg.source + "/skills/${n}/SKILL.md"))
    (builtins.readDir (cfg.source + "/skills")));
  names = lib.subtractLists cfg.exclude (if cfg.skills == null then baseNames else cfg.skills);
  linkFiles =
    lib.optionalAttrs (lib.elem "claude" cfg.targets) {
      ".claude/skills/playbook" = { source = "${rendered}/claude/playbook"; recursive = true; };
    }
    // lib.listToAttrs (lib.concatMap
      (t: map (n: lib.nameValuePair "${userDirs.${t}}/playbook-${n}" { source = "${rendered}/${t}/playbook-${n}"; recursive = true; }) names)
      (lib.filter (t: t != "claude") cfg.targets));
in
{
  options.programs.agent-playbook = {
    enable = lib.mkEnableOption "Brian's generic agent skills (agent-playbook) for Claude Code, Codex and OpenCode";
    source = lib.mkOption {
      type = lib.types.path;
      default = src;
      defaultText = lib.literalExpression "the agent-playbook flake source";
      description = "agent-playbook checkout whose skills/ folder is the base.";
    };
    targets = lib.mkOption {
      type = lib.types.listOf (lib.types.enum [ "claude" "codex" "opencode" ]);
      default = [ "claude" "codex" "opencode" ];
      description = "Tools to install the skills for.";
    };
    skills = lib.mkOption {
      type = lib.types.nullOr (lib.types.listOf lib.types.str);
      default = null;
      example = [ "review-stack" "artifact-style" ];
      description = "Base skills to install; null installs all of them.";
    };
    exclude = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Base skills not to install.";
    };
    overlay = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = "A user-level overlay file (agentskills/v1, YAML or JSON) applied to the base. Overrides skills/exclude.";
    };
    method = lib.mkOption {
      type = lib.types.enum [ "copy" "symlink" ];
      default = "copy";
      description = ''
        copy: real files written at activation by `agentskills render --user` (only folders it
        manages are touched; works with every tool). symlink: home.file links into the Nix store
        (read-only, per-file links; Claude Code, Codex and OpenCode 1.19 follow them). Do not switch
        from symlink to copy without removing the links first.
      '';
    };
    opencodeIgnoreExternal = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Set OPENCODE_DISABLE_EXTERNAL_SKILLS=1 so OpenCode reads only its own skills folders.
        OpenCode also scans ~/.claude/skills and ~/.agents/skills (recursively, so it would see the
        Claude plugin's skills and the Codex copies too) and picks a random winner among skills with
        the same name. Projects then need the opencode target in their overlay.
      '';
    };
    globalInstructions = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Install overlay/global/AGENTS.md as the user-level instructions of each target
        (~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, ~/.config/opencode/AGENTS.md): every session
        looks for live project state and runs `resume`, or proposes `bootstrap`/`new-project`
        with the continuity pack first. Turn off if you manage those files yourself.
      '';
    };
    installResolver = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Put the agentskills command on PATH (for project overlays).";
    };
  };

  config = lib.mkIf cfg.enable (lib.mkMerge [
    { home.packages = lib.optional cfg.installResolver p.agentskills; }
    (lib.mkIf cfg.globalInstructions {
      home.file =
        lib.optionalAttrs (lib.elem "claude" cfg.targets) { ".claude/CLAUDE.md".source = "${cfg.source}/overlay/global/AGENTS.md"; }
        // lib.optionalAttrs (lib.elem "codex" cfg.targets) { ".codex/AGENTS.md".source = "${cfg.source}/overlay/global/AGENTS.md"; }
        // lib.optionalAttrs (lib.elem "opencode" cfg.targets) { ".config/opencode/AGENTS.md".source = "${cfg.source}/overlay/global/AGENTS.md"; };
    })
    (lib.mkIf (cfg.opencodeIgnoreExternal && lib.elem "opencode" cfg.targets) {
      home.sessionVariables.OPENCODE_DISABLE_EXTERNAL_SKILLS = "1";
    })
    (lib.mkIf (cfg.method == "symlink") { home.file = linkFiles; })
    (lib.mkIf (cfg.method == "copy") {
      home.activation.agentPlaybookSkills = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${p.agentskills}/bin/agentskills render --user --no-lock \
          --base ${p.base} --overlay ${if overlayFile == null then "none" else toString overlayFile} \
          --target ${lib.concatStringsSep "," cfg.targets} \
          || echo "agent-playbook: skills not fully installed (see the message above)" >&2
      '';
    })
  ]);
}
