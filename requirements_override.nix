{ pkgs, python }:

self: super: {
  # the standard nixpkgs versions of these work better:
  inherit (pkgs.python37Packages) flit ipython;
  # flit = pkgs.python37Packages.flit;
}
