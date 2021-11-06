# TODO doCheck needs $HOME set to run correctly?

let
  sources = import ./nix/sources.nix {};
  nixpkgs = import sources.nixpkgs {};
in

{ pkgs           ? nixpkgs
, ortholang      ? pkgs.callPackage sources.ortholang {}
, pythonPackages ? pkgs.python37Packages
}:

pythonPackages.buildPythonApplication rec {
  name = "ortholang_jupyter_kernel";
  version = "0.1";

  # prevents copying the src dir into the nix store on every shell invocation
  src = if pkgs.lib.inNixShell then null else ./.;

  propagatedBuildInputs = with pythonPackages; [
    jupyter_client
    ipython
    ipykernel
    pexpect
    matplotlib
    # pillow
    # imageio
    numpy
  ];

  # adds ortholang to PATH in the wrapper script
  makeWrapperArgs = ["--prefix PATH : ${ortholang}/bin"];

  doCheck = false;
}
