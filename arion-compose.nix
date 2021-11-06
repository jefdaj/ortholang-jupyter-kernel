let

  ortholang = import ./ortholang;
  pkgs      = import ./ortholang/nixpkgs;
  ortholang-jupyter-kernel = pkgs.callPackage ./default.nix rec {
    inherit pkgs ortholang;
    pythonPackages = pkgs.python3Packages;
  };

in {
  services.jupyterServer = { config, pkgs, ... }: {
    service.useHostStore = true;
    service.ports = [
      "8001:8888" # host:container TODO use 80 in the container?
    ];
    service.command = [ config.nixos.build.run-jupyter ];

    nixos.configuration  = { config, pkgs, ... }: {
      boot.isContainer = true;
      system.build.run-jupyter = pkgs.writeScript "run-jupyter" ''
        $!{pkgs.coreutils}/bin/bash
        ${pkgs.coreutils}/bin/mkdir -p /home/jupyter
        PATH='${config.systemd.services.jupyter.environment.PATH}'
        ${config.systemd.services.jupyter.runner}
      '';

      users.users.jupyter = {
        isNormalUser = true;
      };
      # jupyter server based on:
      # https://old.reddit.com/r/NixOS/comments/e4hl0r/problems_setting_up_jupyterserver_with_nginxproxy/
      services.jupyter = {
        enable = true; # disabled so i can test it separately
        notebookDir = "/home/jupyter"; # TODO figure this out
        port = 8888;
        ip = "127.0.0.1";
    
        # generated with `jupyter notebook password`,
        # using the jupyter-notebook binary in the systemctl status
        # and then copied from the json file it creates in the homedir
        # TODO no password?
        password = "'argon2:$argon2id$v=19$m=10240,t=10,p=8$jE3igPGObhJsYzgolBNYTQ$AUQfMvf6WNd0GoDTdR435A'";
    
        # TODO are any of the inline settings important?
        notebookConfig = ''
          c.NotebookApp.open_browser=False
          c.NotebookApp.allow_remote_access=True
          c.NotebookApp.disable_check_xsrf=True
          c.NotebookApp.matplotlib = "inline"
          c.InteractiveShellApp.matplotlib = "inline"
          c.IPKernelApp.matplotlib = 'inline'
        '';
    
        kernels = {
          ortholang = {
            displayName = "OrthoLang 0.9.5 (2020-05-15)";
            argv = [ "${ortholang-jupyter-kernel}/bin/ortholang_jupyter_kernel" "-f" "{connection_file}" ];
            language = "ortholang";
          };
        };
      };
    };
  };
}
