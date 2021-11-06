{
  services.jupyterServer = { config, pkgs, ... }: {
    nixos.configuration  = { config, pkgs, ... }: {
      boot.isContainer = true;
      service.useHostStore = true;
      service.ports = [
        "8000":"8000" # host:container TODO use 80 in the container?
      ]
    }
  }
}
