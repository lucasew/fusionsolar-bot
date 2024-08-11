{ dockerTools
, python3Packages
, lib
, self
}:

dockerTools.streamLayeredImage {
  name = "fusionsolar-bot";
  tag = self.rev or self.dirtyRev;
  maxLayers = 2;

  extraCommands = ''
    mkdir -m777 -p tmp etc
  '';

  uid = 1000;
  gid = 1000;
  uname = "user";
  gname = "user";

  config = {
    Entrypoint = [
      (lib.getExe (python3Packages.callPackage ./package.nix {}))
      "--headless"
    ];
    User = "1000:1000";
    Env = [
      "HOME=/tmp"
    ];
  };
}
