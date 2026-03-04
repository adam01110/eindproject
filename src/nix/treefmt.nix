{inputs, ...}: {
  imports = [inputs.treefmt-nix.flakeModule];

  perSystem = _: {
    treefmt = {
      projectRootFile = "flake.nix";

      settings.global.excludes = [
        ".direnv/*"
        ".rumdl_cache/*"
        "node_modules/*"
        "dist/*"
        "src/py/__pycache__"
      ];

      programs = {
        # Nix
        alejandra.enable = true;
        nixf-diagnose.enable = true;
        deadnix.enable = true;
        statix.enable = true;

        # Python
        ruff-check.enable = true;
        ruff-format.enable = true;

        # JavaScript / CSS / JSON
        biome = {
          enable = true;

          validate.enable = false;
          settings.css.parser.tailwindDirectives = true;
        };
      };
    };
  };
}
