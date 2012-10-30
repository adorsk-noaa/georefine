requirejs = require('requirejs');

fs = require('fs');
vm = require('vm');

requireConfig = {};
BASE_URL = __dirname + '/';
requireConfigPath = BASE_URL + 'require_config.js';
script = vm.createScript(fs.readFileSync(requireConfigPath));
requireConfig = {}
sandbox = {
  'require': requireConfig,
  'GRC_BASE_PATH' : __dirname,
  'ASSETS_PATH' : __dirname + '/assets'
};
script.runInNewContext(sandbox);
requirejs.config(requireConfig);

require('coffee-script');
froth = require('/home/adorsk/projects/froth.js/lib/froth.coffee');
frothc = require('/home/adorsk/projects/froth.js/lib/frothc.coffee');
less = require('/home/adorsk/tools/less.js/lib/less/index.js');
less.rewritePath = function(path){
    path = path.replace(/^require:(.*)/, function(){
        newPath = requirejs.toUrl(arguments[1]);
        return newPath;
    });
    return path;
};

srcDir = BASE_URL + '/src/styles';
srcFile = srcDir + '/GeoRefineClient.less';
src = fs.readFileSync(srcFile, 'utf-8');

parser = new less.Parser({
    paths: [srcDir],
    filename: srcFile
});
parser.parse(src, function(err, tree){
    if (err){
        console.error('err: ', err);
    }
    css = tree.toCSS();
    console.log(css);
});

