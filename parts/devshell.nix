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
            ;
        };

        shellHook = ''
          has_zed() {
            command -v zeditor >/dev/null 2>&1 \
              || [ -x /run/current-system/sw/bin/zeditor ] \
              || [ -x "$HOME/.nix-profile/bin/zeditor" ] \
              || [ -x "/etc/profiles/per-user/$USER/bin/zeditor" ]
          }

          if ! has_zed; then
            ${getExe pkgs.zed-editor} .
          fi
        '';
      };
  };
}
