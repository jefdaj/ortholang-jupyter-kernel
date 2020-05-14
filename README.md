ortholang_kernel
================

A [Jupyter Lab][jupyterlab] kernel for [OrthoLang][ortholang].
Still a work in progress, but ready for testing by a few intrepid biologists!


Initial setup
-------------

It could be installed using the regular Jupyter kernel method:
```
python -m ortholang_kernel.install
```

... But since OrthoLang already requires [Nix][nix], we might as well do it the
reproducible Nix way instead! [NixOS][nixos] has a Jupyter server module. Just
add something like this to your `/etc/nixos/configuration.nix`:

```
services.jupyter = {
  enable = true;

  # This is where the notebooks + checkpoint files go.
  # Users will have write access to any files in here.
  notebookDir = "/PATH/TO/YOUR/JUPYTER/NOTEBOOKS/DIR";

  # This enables access from localhost; see Nginx config below for remote access
  port = 8888;
  ip = "127.0.0.1";

  # generated with `jupyter notebook password` (or `sha1sum` would probably work?)
  password = "'sha1:YOURSHA1PASSWORDHASHHERE'";

  notebookConfig = '' 
    c.NotebookApp.open_browser=False 
    c.NotebookApp.allow_remote_access=True 
    c.NotebookApp.disable_check_xsrf=True 
  '';

  kernels = {

    ortholang =
      let kernel = pkgs.callPackage /PATH/TO/YOUR/ORTHOLANG_KERNEL/REPO/default.nix {
        inherit pkgs;
        pythonPackages = pkgs.python3Packages;
      };
      in {
        displayName = "OrthoLang 0.9.5";
        argv = [ "${kernel}/bin/ortholang_kernel" "-f" "{connection_file}" ];
        language = "ortholang";
      };

  };
};
```

Clone this repo somewhere, fill in the variables above, and do `sudo
nixos-rebuild test` to start it. Go to `localhost:8888` in your browser, or see
`journalctl -f | grep -i jupyter` for debugging information if it doesn't work.


Complete webserver
------------------

Once you have the server running, you'll probably want other people to be able
to access it! Assuming you already have a domain name, adding something like
this to the config should set it up properly for the public internet:

```
services.nginx = {
  enable = true;
  recommendedTlsSettings   = true;
  recommendedOptimisation  = true;
  recommendedGzipSettings  = true;
  recommendedProxySettings = true;
  virtualHosts = {
    "YOUR.DOMAIN.NAME.HERE" = {
      forceSSL = true;
      enableACME = true;
      default = true;
      locations = {
        "/" = {
          proxyPass = "http://localhost:8888"; # matches the jupyter service port above
          proxyWebsockets = true;
        };
      };
    };
  };
};

security.acme = {
  acceptTerms = true;
  certs = {
    "YOUR.DOMAIN.NAME.HERE" = {
      email = "your@email.here";
    };
  };
};
```

The `virtualHosts` section is useful if you want to tack this server on to an existing site.
In that case you might also want `useACMEHost` to re-use an existing SSL certificate instead.

Usage
-----

There's one extra rule for parsing in the notebook interface: when a cell
contains multiple statements, they must be separated by blank lines. For
example the blank lines here are important:

```
test1 = ["one",
         "two"]

test2 = ["two", "three"]

:show
```

Otherwise we have no obvious way to know how many prompts to expect
without re-implementing the OrthoLang parser in Python!

TODO the "can't return both text and data" gotcha


[nixos]: https://nixos.org
[nix]: https://nixos.org/nix
[jupyterlab]: https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html
[ortholang]: https://ortholang.pmb.berkeley.edu/
