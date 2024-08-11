{ dockerTools
, python3Packages
, lib
, self
}:

dockerTools.streamLayeredImage {
  name = "fusionsolar-bot";
  tag = self.rev or self.dirtyRev;
  maxLayers = 2;

  contents = [
    dockerTools.binSh
    (dockerTools.fakeNss.override {
      extraPasswdLines = ["user:x:1000:1000:new user:/tmp:/bin/sh"];
      extraGroupLines = ["user:x:1000:"];
    })
  ];

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
    User = "user";
    Env = [
      "HOME=/tmp"
      "LANGUAGE=en_US"
      "UID=1000"
      "GID=1000"
      "TZ=UTC"
    ];
  };
}
