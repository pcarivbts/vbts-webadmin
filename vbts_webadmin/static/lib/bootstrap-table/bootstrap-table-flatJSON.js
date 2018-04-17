/**
 * @author: Dennis Hernández
 * @webSite: http://djhvscf.github.io/Blog
 * @version: v1.3.0
 */

(function ($) {
    'use strict';

    var flat = function (element, that) {
        var result = {};

        function recurse(cur, prop) {
            if (Object(cur) !== cur) {
                result[prop] = cur;
            } else if ($.isArray(cur)) {
            	
                for (var i = 0, l = cur.length; i < l; i++) {
        	 	        for (var p in cur[i]) {
							if(i==0){
								result[prop + that.options.flatSeparator + p] = [];
							}	
							result[prop + that.options.flatSeparator + p] = result[prop + that.options.flatSeparator + p] + cur[i][p] + "&nbsp;&nbsp;&nbsp;&nbsp;";
	                	}
                }   
            } else {
                var isEmpty = true;
                for (var p in cur) {
                    isEmpty = false;
                    recurse(cur[p], prop ? prop + that.options.flatSeparator + p : p);
                }
                if (isEmpty) {
                    result[prop] = {};
                }
            }
        }

        recurse(element, "");
   		console.log(result);
        return result;
    };

    var flatHelper = function (data, that) {
        var flatArray = [];

        $.each(!$.isArray(data) ? [data] : data, function (i, element) {
            flatArray.push(flat(element, that));
        });
        return flatArray;
    };

    $.extend($.fn.bootstrapTable.defaults, {
        flat: false,
        flatSeparator: '.'
    });

    var BootstrapTable = $.fn.bootstrapTable.Constructor,
        _initData = BootstrapTable.prototype.initData;

    BootstrapTable.prototype.initData = function (data, type) {
        if (this.options.flat) {
            data = flatHelper(data ? data : this.options.data, this);
        }
        _initData.apply(this, [data, type]);
    };
})(jQuery);
