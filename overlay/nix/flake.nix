{
  # Use from another flake:  inputs.agent-playbook.url = "github:TheGostsniperfr/agent-playbook?dir=overlay/nix";
  description = "agent-playbook: agentskills resolver, rendered skills and a home-manager module";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      src = ../..; # the agent-playbook repository root (this flake lives in overlay/nix)
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin" ];
      forAll = f: nixpkgs.lib.genAttrs systems (system: f (import ./package.nix {
        pkgs = nixpkgs.legacyPackages.${system};
        inherit src;
      }));
    in
    {
      packages = forAll (p: {
        default = p.agentskills;
        agentskills = p.agentskills;
        skills = p.renderSkills { };
      });
      apps = forAll (p: {
        default = { type = "app"; program = "${p.agentskills}/bin/agentskills"; };
      });
      checks = forAll (p: { tests = p.tests; skills = p.renderSkills { }; });
      homeManagerModules.default = import ./home-manager.nix { inherit src; };
      homeManagerModules.agent-playbook = self.homeManagerModules.default;
    };
}
