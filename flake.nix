{
  description = "Bot to fetch fusionsolar production and send to a list of emails";

  inputs = {
    nixpkgs.url = "nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { nixpkgs, flake-utils, self, ... }: 
  flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs { inherit system; };
  in {
    packages = {
      default = pkgs.python3Packages.callPackage ./package.nix {};
      container = pkgs.python3Packages.callPackage ./container.nix {
        inherit self;
      };
    };
    nixosModules.default = import ./nixos.nix;
  });
}
