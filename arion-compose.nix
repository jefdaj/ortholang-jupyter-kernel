{ pkgs, ... }:

let

  # from https://github.com/tweag/jupyterWith shell.nix example
  jupyter = import (builtins.fetchGit {
    url = https://github.com/tweag/jupyterWith;
    rev = "";
  }) {};
  iPython = jupyter.kernels.iPythonWith {
    name = "python";
    packages = p: with p; [ numpy ];
  };
  jupyterEnvironment =
    jupyter.jupyterlabWith {
      kernels = [ iPython ];
  };

in {
  config.services = {

    jupyter = {
      service.useHostStore = true;

      # TODO don't allow root?
      service.command = [ "${pkgs.bashInteractive}/bin/bash" "-c" ''
        ${pkgs.coreutils}/bin/mkdir -p "$$LAB_ROOT"
        ${pkgs.coreutils}/bin/chown jupyter:jupyter "$$LAB_ROOT" -R
        cd "$$LAB_ROOT"
        ${jupyterEnvironment}/bin/jupyter-lab --allow-root --no-browser --log-level=DEBUG --ip=0.0.0.0
      '' ];
      service.ports = [

        # 8888 is the default jupyter lab port
        # but here we change the host side to avoid messing with the system version
        "9999:8888" # host:container

      ];
      # TODO where would this be ideally?
      service.environment.LAB_ROOT = "/home/jupyter";
    };
  };
}
