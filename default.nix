# This looks a little weird because OrthoLang includes its own pinned nixpkgs
# for reproduciblity, and there's no obvious reason we would want that one to
# be out of sync with the one used to build the Jupyter kernel. So we reach
# into the ortholang submodule and use its nixpkgs settings. That behavior can
# be overridden by passing a different pkgs argument from your system config.

# TODO doCheck needs $HOME set to run correctly?

{ ortholang      ? import ./ortholang
, pkgs           ? import ./ortholang/nixpkgs
, pythonPackages ? pkgs.python37Packages
}:

pythonPackages.buildPythonApplication rec {
  name = "ortholang_kernel";
  version = "0.1";
  src = ./.;
  propagatedBuildInputs = with pythonPackages; [
    jupyter_client
    ipython
    ipykernel
    pexpect
    matplotlib
    pillow
    imageio
    numpy
  ];
  makeWrapperArgs = ["--prefix PATH : ${ortholang}/bin"];
  doCheck = false;
}
