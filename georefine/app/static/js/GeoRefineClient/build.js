requirejs = require('requirejs');

fs = require('fs');
vm = require('vm');

requireConfig = {};
BASE_URL = __dirname + '/';
requireConfigPath = BASE_URL + 'config.js';
script = vm.createScript(fs.readFileSync(requireConfigPath));
requireConfig = {}
sandbox = {
  'require': requireConfig,
  'BASE_PATH' : __dirname,
  'ASSETS_PATH' : __dirname + '/assets'
};
script.runInNewContext(sandbox);

buildConfig = {
    name: "GeoRefineClient/app",
    include: ['requireLib'],
    out: BASE_URL + 'dist/GeoRefineClient.min.js'
};

for (var k in requireConfig){
    buildConfig[k] = requireConfig[k];
}

requirejs.optimize(buildConfig, function(buildResponse){
    console.log("done building");
});
