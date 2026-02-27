_: {
  perSystem = {pkgs, ...}: {
    devShells.default = let
      inherit (builtins) attrValues;
      inherit (pkgs) mkShell;
      inherit (pkgs.lib) getExe;
    in
      mkShell {
        packages = attrValues {
          inherit
            (pkgs)
            bun
            codex
            zed-editor
            ;
        };

        shellHook = ''${getExe pkgs.zed-editor} .'';
      };
  };
}
