{
  services.jupyterServer = { config, pkgs, ... }: {

    service.capabilities.SYS_ADMIN = true;
    service.useHostStore = true; # TODO does this work with systemd?
    service.ports = [
      "8889:8889" # host:container TODO use 80 in the container?
    ];

    nixos.useSystemd = true; # TODO remove?

    nixos.configuration  = { config, pkgs, ... }: {
      boot.isContainer = true;
      users.users.jupyter.isSystemUser = true; # TODO remove?

      # jupyter server based on:
      # https://old.reddit.com/r/NixOS/comments/e4hl0r/problems_setting_up_jupyterserver_with_nginxproxy/
      services.jupyter = {
        enable = true;
        notebookDir = "/var/lib/jupyter/lab"; # TODO is this a good place?
        port = 8889;
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
    
        kernels =

          # TODO get this working with niv instead
          # TODO try switching to jupyterWith without systemd?
          let
            pinnedOrtholang = import ./ortholang;
            pinnedNixpkgs   = import ./ortholang/nixpkgs;
            kernel = pinnedNixpkgs.callPackage ./default.nix rec {
              ortholang      = pinnedOrtholang;
              pkgs           = pinnedNixpkgs;
              pythonPackages = pinnedNixpkgs.python37Packages;
            };
          in {
            ortholang = {
              displayName = "OrthoLang 0.9.5 (2020-05-15)";
              argv = [ "${kernel}/bin/ortholang_jupyter_kernel" "-f" "{connection_file}" ];
              language = "ortholang";
            };
          };

      };
    };
  };
}
