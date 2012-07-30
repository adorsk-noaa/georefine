define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
		],
function($, Backbone, _, _s, Util){

    var GeoRefineFormatter = function(f, s){
        var re = /%(\.(\d+))?(H|h)/;
        var m = re.exec(f)
        if (m){
            f = f.replace(re, '%s');
            var d = parseInt(m[2])|| 1;
            var use_long = (m[3] == 'H');
            s = Util.util.friendlyNumber(s, d, use_long)
        }
        return _s.sprintf(f, s);
    };

    // Objects to expose.
    var formatUtil = {
        GeoRefineFormatter: GeoRefineFormatter
    };
    return formatUtil;
});
