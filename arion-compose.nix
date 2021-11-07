{ pkgs, ... }:

let

  # this would give you the official version
  # jupyter = import (builtins.fetchGit {
  #   url = https://github.com/tweag/jupyterWith;
  #   rev = "";
  # }) {};

  # but we want my fork with ortholang support instead for now
  jupyter = import (builtins.fetchGit {
    url = https://github.com/jefdaj/jupyterwith-ortholang;
    rev = "";
  }) {};

  # from https://github.com/tweag/jupyterWith shell.nix example
  iPython = jupyter.kernels.iPythonWith {
    name = "python";
    packages = p: with p; [ numpy ];
  };
  ortholang = jupyter.kernels.ortholangKernel {
    name = "test1";
  };
  jupyterEnvironment =
    jupyter.jupyterlabWith {
      kernels = [ iPython ortholang ];
  };

  # pinned ortholang kernel v0.9.5
  # TODO build kernel with current nixpkgs instead of matching ortholang?
  # TODO get all this from niv of course
  pinnedOrtholang = import ./ortholang;
  pinnedNixpkgs   = import ./ortholang/nixpkgs;
  kernel = pinnedNixpkgs.callPackage ./default.nix rec {
    ortholang      = pinnedOrtholang;
    inherit pkgs;
    pythonPackages = pkgs.python37Packages;
  };
 
in {
  config.services = {

    jupyterWithOrholang = {
      service.useHostStore = true;

      # TODO don't allow root?
      service.command = [ "${pkgs.bashInteractive}/bin/bash" "-c" ''
        ${pkgs.coreutils}/bin/mkdir -p "$$LAB_ROOT"
        ${pkgs.coreutils}/bin/chown jupyter:jupyter "$$LAB_ROOT" -R
        echo "including ${pinnedOrtholang} just to show it builds"
        echo "including ${kernel} just to show it builds"
        cd "$$LAB_ROOT"
        ${jupyterEnvironment}/bin/jupyter-lab --allow-root --no-browser --log-level=DEBUG --ip=0.0.0.0
      '' ];
      service.ports = [

        # 8888 is the default jupyter lab port
        # but here we change the host side to avoid messing with the system version
        "8888:8888" # host:container

      ];
      # TODO where would this be ideally?
      service.environment.LAB_ROOT = "/home/jupyter";
    };
  };
}
