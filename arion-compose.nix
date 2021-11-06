{ pkgs, ... }:
{
  config.services = {

    webserver = {
      service.useHostStore = true;
      service.command = [ "${pkgs.bashInteractive}/bin/sh" "-c" ''
                            cd "$$WEB_ROOT"
                            ${pkgs.python3}/bin/python -m http.server
                          ''
                        ];
      service.ports = [

        # python server defaults to 8000,
        # but we need to switch to avoid a conflict on the host
        "7000:8000" # host:container

      ];
      service.environment.WEB_ROOT = "${pkgs.nix.doc}/share/doc/nix/manual";
    };
  };
}
