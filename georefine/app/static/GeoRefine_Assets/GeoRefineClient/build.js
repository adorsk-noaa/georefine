requirejs = require('requirejs');
wrench = require('wrench');

fs = require('fs');
vm = require('vm');

requireConfig = {};
BASE_URL = __dirname + '/';
DIST_DIR = __dirname + '/dist';

// Create dist dir if it does not exist.
if (! fs.existsSync(DIST_DIR)){
  wrench.mkdirSyncRecursive(DIST_DIR);
}

requireConfigPath = BASE_URL + 'require_config.js';
script = vm.createScript(fs.readFileSync(requireConfigPath));
requireConfig = {};
sandbox = {
  'require': requireConfig,
  'GRC_BASE_PATH' : __dirname,
  'ASSETS_PATH' : __dirname + '/assets'
};
script.runInNewContext(sandbox);

buildConfig = {
    include: ['requireLib', 'GeoRefineClient'],
    out: DIST_DIR + '/GeoRefineClient.min.js',
    optimize: 'uglify'
};

for (var k in requireConfig){
    buildConfig[k] = requireConfig[k];
}

// First build JS.
requirejs.optimize(buildConfig, function(buildResponse){
    console.log("done building JS.");

    // Then build CSS.
    require('coffee-script');
    requirejs.config(requireConfig);
    less = require(__dirname + '/assets/js/less.js/lib/less/index.js');
    less.rewritePath = function(path){
        path = path.replace(/^require:(.*)/, function(){
            newPath = requirejs.toUrl(arguments[1]);
            return newPath;
        });
        return path;
    };
    less.addBasePath = true;
    less.compileCss = true;

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

        bundler = require('./bundler.coffee');
        bundler.bundle(css, {
            outputDir: DIST_DIR + '/css'
        });

        console.log("done building CSS.");
        console.log("done building.");

    });

});
