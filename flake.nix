{
  description = "Tang Nano 9K panel case reproducible design environment";

  # Keep this revision aligned with sabas0ba/dotfiles commit
  # fc4cdecc02a6a95c81a259549d3fb9e7df18bb8f.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/597283ad8aa0b331c788e97c4c262d58877074ef";

  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems =
        function:
        nixpkgs.lib.genAttrs systems (
          system:
          function (import nixpkgs {
            inherit system;
            config = { };
            overlays = [ ];
          })
        );
      projectPython =
        pkgs:
        pkgs.python312.withPackages (
          ps: with ps; [
            charset-normalizer
            contourpy
            cycler
            fonttools
            kiwisolver
            matplotlib
            numpy
            packaging
            pillow
            pyparsing
            python-dateutil
            reportlab
            six
          ]
        );
    in
    {
      packages = forAllSystems (pkgs: {
        default = projectPython pkgs;
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShellNoCC {
          name = "tang-nano-9k-case";
          packages = [
            pkgs.bashInteractive
            pkgs.coreutils
            pkgs.findutils
            pkgs.fontconfig
            pkgs.git
            pkgs.gnumake
            pkgs.poppler-utils
            pkgs.ripgrep
            (projectPython pkgs)
          ];
          env = {
            CASE_ENV = "nix-develop";
            DEJAVU_FONT_PATH = "${pkgs.dejavu_fonts.minimal}/share/fonts/truetype/DejaVuSans.ttf";
            FONTCONFIG_FILE = "${pkgs.fontconfig.out}/etc/fonts/fonts.conf";
            FONTCONFIG_PATH = "${pkgs.fontconfig.out}/etc/fonts";
            LC_ALL = "C.UTF-8";
            PYTHONHASHSEED = "0";
          };
          shellHook = ''
            if root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
              export CASE_ROOT="$root"
              export MPLCONFIGDIR="$root/tmp/matplotlib"
              export PYTHONPYCACHEPREFIX="$root/tmp/pycache"
              export XDG_CACHE_HOME="$root/tmp/cache"
              mkdir -p "$MPLCONFIGDIR" "$PYTHONPYCACHEPREFIX" "$XDG_CACHE_HOME"
            fi
            echo "Tang Nano 9K case dev shell (${pkgs.stdenv.hostPlatform.system})"
          '';
        };
      });
    };
}
