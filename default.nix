{ pkgs ? import <nixpkgs> {}
, pythonPackages ? pkgs.python37Packages
}:

let
  ortholang = import ./ortholang;

in pythonPackages.buildPythonPackage rec {
  name = "ortholang_kernel";
  version = "0.1";
  src = ./.;
  buildInputs = [
    pythonPackages."jupyter_client"
    pythonPackages."ipython"
    pythonPackages."ipykernel"
    pythonPackages."pexpect"
    ortholang # TODO need to wrap the final binary to get this?
  ];
  doCheck = false; # TODO needs to set $HOME to run correctly?
}
