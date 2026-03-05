_: {
  perSystem = {pkgs, ...}: {
    devShells.default = let
      inherit (builtins) attrValues;
      inherit (pkgs) mkShell;
      inherit (pkgs.lib) getExe;

      python-minifier = pkgs.python3Packages.buildPythonApplication rec {
        pname = "python-minifier";
        version = "3.2.0";
        format = "setuptools";

        src = pkgs.fetchPypi {
          pname = "python_minifier";
          inherit version;
          hash = "sha256-051KqWVSBocLibQQmahHJeGEUxmqWovqahBGtWRM1BM=";
        };

        nativeBuildInputs = [pkgs.python3Packages.setuptools];
      };
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
