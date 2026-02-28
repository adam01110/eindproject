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
      ];

      programs = {
        alejandra.enable = true;
        nixf-diagnose.enable = true;
        deadnix.enable = true;
        statix.enable = true;

        biome = {
          enable = true;
          validate.enable = false;
          settings.css.parser.tailwindDirectives = true;
        };
      };
    };
  };
}
