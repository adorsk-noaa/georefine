require(
    [
        "jquery",
        "rless!GeoRefineClient/styles/GeoRefineClient.less",
        "GeoRefineClient"
    ],
    function($, GeoRefineClientCss, GeoRefineClient){
        $(document).ready(function(){
            $(document.body).append('<p id="stylesLoaded" style="display: none;"></p>');
            cssEl = document.createElement('style');
            cssEl.id = 'grc_css';
            cssEl.type = 'text/css';
            cssText = GeoRefineClientCss + "\n#stylesLoaded {position: fixed;}\n";
            if (cssEl.styleSheet){
                cssEl.styleSheet.cssText = cssText;
            }
            else{
                cssEl.appendChild(document.createTextNode(cssText));
            }
            document.getElementsByTagName("head")[0].appendChild(cssEl);

            var cssDeferred = $.Deferred();
            var cssInterval = setInterval(function(){
                $testEl = $('#stylesLoaded');
                var pos = $testEl.css('position');
                if (pos == 'fixed'){
                    clearInterval(cssInterval);
                    cssDeferred.resolve();
                }
                else{
                    console.log('loading styles...', pos);
                }
            }, 500);

            cssDeferred.done(function(){
                m = new Backbone.Model();
                c = new GeoRefineClient.views.GeoRefineClientView({
                    model: m,
                    el: $(GeoRefine.mainEl)
                });
            });
        });
    }
);
