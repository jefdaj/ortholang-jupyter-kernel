{ pkgs ? import <nixpkgs> {}
# , python ? pkgs.python37
, pythonPackages ? pkgs.python37Packages # 3.6 doesn't help (same IPython error) :/
}:

let
  # pkgs = import <nixpkgs> {};
  # myPython = import ./requirements.nix { inherit pkgs; };
  ortholang = import ./ortholang;

in pythonPackages.buildPythonPackage rec {
  name = "ortholang_kernel";
  version = "0.1";
  src = ./.;
  buildInputs = [
    # python.interpreter
    pythonPackages."jupyter_client"
    pythonPackages."ipython"
    pythonPackages."ipykernel"
    ortholang
  ];
  doCheck = false; # TODO needs to set $HOME to run correctly?
}
 
# let
#   pkgs = import <nixpkgs> {};
# 
#   ortholang = import ./ortholang;
#   myPython = import ./requirements.nix { inherit pkgs; };
# 
#   runDepends = [
#     myPython.interpreter
#     myPython.packages."jupyter_client"
#     myPython.packages."ipython"
#     myPython.packages."ipykernel"
#     ortholang
#   ];
# 
# in pkgs.stdenv.mkDerivation rec {
#   src = ./.;
#   version = "0.1";
#   name = "ortholang-kernel"; # TODO include version?
#   inherit runDepends;
#   buildInputs = [ pkgs.makeWrapper ] ++ runDepends;
#   builder = pkgs.writeScript "builder.sh" ''
#     #!/usr/bin/env bash
#     source ${pkgs.stdenv}/setup
#     mkdir -p $out/src
#     dest="$out/bin/ortholang-kernel"
#     install -m755 $src/ortholang-demo.py $dest
#     wrapProgram $dest --prefix PATH : "${pkgs.lib.makeBinPath runDepends}"
#   '';
# }
