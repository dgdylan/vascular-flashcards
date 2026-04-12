// Inject IE8 support
(function() {
    var canvasSupport = document.createElement('canvas').getContext,
        _proto = $.circleProgress.defaults,
        _originalInit = _proto.init;

    _proto.staticClass = 'static-circle';

    _proto.init = function(config) {
        $.extend(this, config);

        this.canvas = this.canvas || $('<canvas>').prependTo(this.el)[0];

        if (!canvasSupport) {
            if (window.G_vmlCanvasManager) {
                // `excanvas` polyfill
                G_vmlCanvasManager.initElement(this.canvas);

                if (this.fill.gradient || this.fill.image || !this.fill.color)
                    console.warn("Your circle fill will not work correctly in IE8. Please, use only solid color fill");

                this.el.removeClass(_proto.staticClass);
            } else {
                // no polyfill - no drawing
                this.initWidget = this.initFill = this.drawFrame = $.noop;
                this.el.addClass(_proto.staticClass);
            }
        }

        return _originalInit.call(this, config);
    };
}());
