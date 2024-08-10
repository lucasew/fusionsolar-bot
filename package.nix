{ chromedriver
, chromium
, lib
, python3
, writeShellScriptBin
}:

let
  python = python3.withPackages (p: [p.selenium]);
in

writeShellScriptBin "fusionsolar-bot" ''
  export PATH=$PATH:${lib.makeBinPath [chromedriver chromium]}
  exec ${python.interpreter} ${./payload.py} "$@"
''
