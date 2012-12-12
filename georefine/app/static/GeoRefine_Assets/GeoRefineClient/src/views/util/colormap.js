define(
  ['jquery'],
  function($){

    var CMAPS = {};

    //
    // Generate colormaps, based on ColorBrewer.
    //

    var CB_PREFIX = 'ColorBrewer';

    var MIN_V = .97;
    var MAX_V = .94;
    var MIN_S = 0;
    var MAX_S = .6;

    var CB_HUES = {
      Rd: .05,
      Bu: .55,
      Br: .11,
      BG: .49,
      Pi: .9,
      G: .25,
      PR: .77,
      Gn: .32,
      Or: .09,
      Pu: .7
    };

    // Sequential.
    $.each(CB_HUES, function(hue_id, hue){
      var cmapId = CB_PREFIX + ':' + hue_id;
      CMAPS[cmapId] = {
        'h': [[0, hue],[1, hue]],
        's': [[0, MIN_S], [1, MAX_S]],
        'v': [[0, MIN_V], [1, MAX_V]]
      };
    });

    // Diverging.
    var diverging_hue_pairs = [
      ['Rd', 'Bu'],
      ['Br', 'BG'],
      ['Pi', 'G'],
      ['PR', 'Gn'],
      ['Or', 'Pu']
    ];

    $.each(diverging_hue_pairs, function(i, orig_pair){
      var reversed_pair = [orig_pair[1], orig_pair[0]];
      $.each([orig_pair, reversed_pair], function(j, pair){
        var cmapId = CB_PREFIX + ':' + pair.join('');
        var h1 = CB_HUES[pair[0]];
        var h2 = CB_HUES[pair[1]];
        CMAPS[cmapId] = {
          'h': [[0, h1],[.5, h1],[.5, h2],[1, h2]],
          's': [[0, MAX_S], [.5, MIN_S], [.5, MIN_S], [1, MAX_S]],
          'v': [[0, MAX_V], [.5, MIN_V], [.5, MIN_V], [1, MAX_V]]
        };
      });
    });

    return {
      CMAPS: CMAPS
    };
  }
);
