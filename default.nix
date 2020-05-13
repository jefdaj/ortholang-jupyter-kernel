# The iPython kernel examples are all packaged as Python modules, but it seems
# that what we really want is a wrapped binary? Maybe that's just more
# convenient to set up without Nix via modules.

{ pkgs           ? (import <nixpkgs> {})
, ortholang      ? (pkgs.callPackage ./ortholang { inherit pkgs; })
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
  doCheck = false; # TODO needs to set $HOME to run correctly?
  inherit ortholang;
  postInstall = ''
    for f in $out/bin/*; do
      wrapProgram $f --prefix PATH : "${ortholang}/bin"
    done
  '';
}
