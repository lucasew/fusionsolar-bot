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
    mkdir -m0777 -p tmp
  '';

  config = {
    Entrypoint = [
      (lib.getExe (python3Packages.callPackage ./package.nix {}))
      "--headless"
    ];
    User = "1000:1000";
    Env = [
      "HOME=/tmp"
      "CHROME_USER_DATA_DIR=/tmp/chrome"
    ];
  };
}
