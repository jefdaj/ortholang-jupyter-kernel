{ }:

let
  pkgs = import <nixpkgs> {};
  python = import ./requirements.nix { inherit pkgs; };

in python.mkDerivation rec {
  name = "ortholang_kernel";
  version = "0.1";
  buildInputs = [
    pkgs.pythonPackages.jupyter_client
    pkgs.pythonPackages.ipython
    pkgs.pythonPackages.ipykernel
  ];
}
