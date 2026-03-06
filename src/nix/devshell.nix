_: {
  perSystem = {
    pkgs,
    config,
    ...
  }: {
    devShells.default = let
      inherit (builtins) attrValues;
      inherit (pkgs) mkShell;
      inherit (pkgs.lib) getExe;

      inherit (config.packages) python-minifier;
    in
      mkShell {
        packages =
          (attrValues {
            inherit
              (pkgs)
              alejandra
              biome
              bun
              codex
              nixd
              ruff
              tailwindcss-language-server
              tokei
              vscode-langservers-extracted
              ;
          })
          ++ [python-minifier];

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
