# This looks a little weird because OrthoLang includes its own pinned nixpkgs
# for reproduciblity, and there's no obvious reason we would want that one to
# be out of sync with the one used to build the Jupyter kernel. So we reach
# into the ortholang submodule and use its nixpkgs settings. That behavior can
# be overridden by passing a different pkgs argument from your system config.

# TODO doCheck needs $HOME set to run correctly?

let
  sources         = import ./nix/sources.nix {};
  pinnedPkgs      = import sources.nixpkgs {};
  pinnedOrtholang = import sources.ortholang;
in

{ ortholang      ? pinnedOrtholang
, pkgs           ? pinnedPkgs
, pythonPackages ? pkgs.python37Packages # TODO update this?
}:

pythonPackages.buildPythonApplication rec {
  name = "ortholang_jupyter_kernel";
  version = "0.1";

  # prevents copying the src dir into the nix store on every shell invocation
  # ... but breaks jupyterWith which uses src inside a nix-shell by default
  # src = if pkgs.lib.inNixShell then null else ./.;
  src = ./.;

  propagatedBuildInputs = with pythonPackages; [
    jupyter_client
    ipython
    ipykernel
    pexpect
    matplotlib
    numpy
    # pillow
    # imageio
  ];

  # adds ortholang to PATH in the wrapper script
  makeWrapperArgs = ["--prefix PATH : ${ortholang}/bin"];

  doCheck = false;
}
