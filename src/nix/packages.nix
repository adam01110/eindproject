_: {
  perSystem = {pkgs, ...}: {
    packages.python-minifier = pkgs.python3Packages.buildPythonApplication rec {
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
  };
}
