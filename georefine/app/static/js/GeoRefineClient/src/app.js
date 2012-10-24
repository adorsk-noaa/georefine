require(
    [
        "jquery",
        "GeoRefineClient"
    ],
    function($, GeoRefineClient){
        var grc_m = new Backbone.Model();
        var grc_v = new GeoRefineClient.views.GeoRefineClientView({
            model: grc_m,
            el: $(GeoRefine.mainEl)
        });
    }
);
