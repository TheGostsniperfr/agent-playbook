#!/bin/sh
# Install (or update) agent-playbook's generic skills for Claude Code, Codex and OpenCode without Nix.
#
#   curl -fsSL https://raw.githubusercontent.com/TheGostsniperfr/agent-playbook/main/overlay/install.sh | sh
#   sh overlay/install.sh [--ref REF] [--target claude,codex,opencode] [--overlay FILE] [--dir DIR] [--no-bin]
#   sh overlay/install.sh --uninstall
#
# Clones the repo into DIR (default ~/.local/share/agent-playbook), links `agentskills` into
# ~/.local/bin, and renders the skills as real files into ~/.claude/skills, ~/.agents/skills (Codex)
# and ~/.config/opencode/skills. Only folders listed in each dir's .agentskills-managed are touched.
# POSIX sh; needs git and python3 >= 3.8. Works on macOS (bash 3.2 / BSD tools) and Linux.
set -eu

repo="${AGENT_PLAYBOOK_REPO:-https://github.com/TheGostsniperfr/agent-playbook}"
dir="${AGENT_PLAYBOOK_HOME:-$HOME/.local/share/agent-playbook}"
ref="main"
targets="claude,codex,opencode"
overlay="${AGENTSKILLS_USER_OVERLAY:-none}"
bin=1
uninstall=0

die() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --ref) [ $# -ge 2 ] || die "--ref needs a value"; ref="$2"; shift ;;
    --target) [ $# -ge 2 ] || die "--target needs a value"; targets="$2"; shift ;;
    --overlay) [ $# -ge 2 ] || die "--overlay needs a file"; overlay="$2"; shift ;;
    --dir) [ $# -ge 2 ] || die "--dir needs a value"; dir="$2"; shift ;;
    --no-bin) bin=0 ;;
    --uninstall) uninstall=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) die "unknown option $1 (see --help)" ;;
  esac
  shift
done

command -v git >/dev/null 2>&1 || die "git is required"
command -v python3 >/dev/null 2>&1 || die "python3 is required (macOS: xcode-select --install)"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' || die "python3 >= 3.8 is required"

if [ "$uninstall" -eq 1 ]; then
  if [ -x "$dir/overlay/agentskills" ]; then
    python3 "$dir/overlay/agentskills" clean --user --overlay none --base "$dir" --target "$targets"
  fi
  if [ -L "$HOME/.local/bin/agentskills" ]; then rm -f "$HOME/.local/bin/agentskills"; fi
  printf 'Removed the rendered skills and the agentskills link. The checkout stays in %s.\n' "$dir"
  exit 0
fi

if [ -d "$dir/.git" ]; then
  git -C "$dir" fetch -q --depth 1 origin "$ref"
  git -C "$dir" -c advice.detachedHead=false checkout -q --force FETCH_HEAD
else
  mkdir -p "$(dirname "$dir")"
  git clone -q --depth 1 --branch "$ref" "$repo" "$dir"
fi
printf 'agent-playbook at %s (%s)\n' "$(git -C "$dir" rev-parse --short HEAD)" "$dir"

if [ "$bin" -eq 1 ]; then
  mkdir -p "$HOME/.local/bin"
  ln -sf "$dir/overlay/agentskills" "$HOME/.local/bin/agentskills"
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) printf 'Add ~/.local/bin to your PATH to use the agentskills command.\n' ;;
  esac
fi

python3 "$dir/overlay/agentskills" render --user --no-lock --base "$dir" --overlay "$overlay" --target "$targets"
case ",$targets," in
  *,opencode,*)
    if [ "${OPENCODE_DISABLE_EXTERNAL_SKILLS:-}" != "1" ]; then
      printf 'OpenCode: add "export OPENCODE_DISABLE_EXTERNAL_SKILLS=1" to your shell profile, otherwise it also\n'
      printf 'reads the Claude and Codex copies and picks one at random when names repeat.\n'
    fi ;;
esac
# Global instructions: never overwrite a file the user already has; print how to include ours.
for f in "$HOME/.claude/CLAUDE.md" "$HOME/.codex/AGENTS.md" "$HOME/.config/opencode/AGENTS.md"; do
  if [ -e "$f" ]; then
    grep -q 'agent-playbook' "$f" 2>/dev/null || printf 'Keeping your %s; append %s to it for session continuity by default.\n' "$f" "$dir/overlay/global/AGENTS.md"
  else
    mkdir -p "$(dirname "$f")" && cp "$dir/overlay/global/AGENTS.md" "$f"
  fi
done
printf 'Done. Claude Code shows these skills as /playbook:<name>; Codex and OpenCode as playbook-<name>.\n'
printf 'Re-run this script to update; start a new agent session to pick up new skills.\n'
