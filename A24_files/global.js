function getProfileColor(name) {
    var number = parseInt(first_letter.toUpperCase().charCodeAt(0)) + parseInt(last_letter.toUpperCase().charCodeAt(0)).toString();
    number = parseInt(number[number.length-1]);
    var color = 'brown';
    if ($.inArray(number, [0, 5]) === 1){
        color = 'gold';
    }
    else if ($.inArray(number, [1, 6]) === 1){
        color = 'green';
    }
    else if ($.inArray(number, [2, 7]) === 1){
        color = 'blue';
    }
    else if ($.inArray(number, [3, 8]) === 1){
        color = 'red';
    }
    return color;
}


function renderProfileImage(className, size, fontSize){
    $(className).loadImages({
        imgLoadedClb: function(){}, // Triggered when an image is loaded. ('this' is the loaded image)
        allLoadedClb: function(){}, // Triggered when all images are loaded. ('this' is the wrapper in which all images are loaded, or the image if you ran it on one image)
        imgErrorClb:  function(){
            var firstLetter = $(this).attr('data-firstLetter');
            var lastLetter  = $(this).attr('data-lastLetter');
            var color       = $(this).attr('data-color');
            var circleHtml = '<div class="circle-img '+color+'" style="width: '+ size +'px; height: '+ size +'px; margin: 0 auto;">';
            circleHtml += '<h3 class="no-spacing" style="width: '+ size +'px; height: '+ size +'px; color: #fff; text-align: center; line-height: '+ size +'px; font-size: '+ fontSize +'px;">';
            circleHtml += firstLetter + lastLetter;
            circleHtml += '</h3>';
            circleHtml += '</div>';
            $(this).replaceWith(circleHtml);

        }, // Triggered when the image gives an error. Useful when you want to add a placeholder instead or remove it. ('this' is the loaded image)
        noImgClb:     function(){}, // Triggered when there are no image found with data-src attributes, or when all images give an error. ('this' is the wrapper in which all images are loaded, or the image if you ran it on one image)
        dataAttr:     'src' // The data attribute that contains the source. Default 'src'.
    });
}


/* ── Global modal focus trap ────────────────────────────────────────────── */
var FOCUSABLE = 'a[href], button:not([disabled]), input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])';

function getOpenModal() {
    return $('.modal.in, .modal.show').filter(':visible').last();
}

/* Store the element that opened the modal so focus returns on close */
$(document).on('show.bs.modal', '.modal', function () {
    $(this).data('focusTrigger', document.activeElement);
});

/* When modal is fully visible: remove aria-hidden and move focus to title */
$(document).on('shown.bs.modal', '.modal', function () {
    var $modal = $(this);
    $modal.removeAttr('aria-hidden');
    /* Only move focus if nothing inside is already focused */
    if (!$modal[0].contains(document.activeElement)) {
        var labelId = $modal.attr('aria-labelledby');
        var $title = labelId ? $modal.find('#' + labelId) : $([]);
        if ($title.length) {
            $title.attr('tabindex', '-1').focus();
        } else {
            var $first = $modal.find(FOCUSABLE).filter(':visible').first();
            if ($first.length) $first.focus();
            else $modal.attr('tabindex', '-1').focus();
        }
    }
});

/* When modal closes: restore aria-hidden and return focus to trigger */
$(document).on('hidden.bs.modal', '.modal', function () {
    $(this).attr('aria-hidden', 'true');
    var trigger = $(this).data('focusTrigger');
    if (trigger && trigger.focus) trigger.focus();
});

/* Tab trap — bound directly on document so nothing can block it */
$(document).on('keydown.modalTrap', function (e) {
    if (e.which !== 9) return;
    var $modal = getOpenModal();
    if (!$modal.length) return;

    var $focusable = $modal.find(FOCUSABLE).filter(':visible');
    if (!$focusable.length) return;

    var first = $focusable.first()[0];
    var last  = $focusable.last()[0];

    if (e.shiftKey) {
        if (document.activeElement === first || !$modal[0].contains(document.activeElement)) {
            e.preventDefault();
            last.focus();
        }
    } else {
        if (document.activeElement === last || !$modal[0].contains(document.activeElement)) {
            e.preventDefault();
            first.focus();
        }
    }
});

/* Backup: if focus escapes the modal by any other means, pull it back */
$(document).on('focusin.modalTrap', function (e) {
    var $modal = getOpenModal();
    if ($modal.length && !$modal[0].contains(e.target)) {
        var $focusable = $modal.find(FOCUSABLE).filter(':visible');
        if ($focusable.length) $focusable.first().focus();
        else $modal.attr('tabindex', '-1').focus();
    }
});
/* ── End focus trap ─────────────────────────────────────────────────────── */

$( document ).ready(function() {

    $('.main-select').select2({minimumResultsForSearch: -1, width: 'resolve', dropdownCssClass: 'd-block d-md-none eb-dropdown'});

    /* Remove hidden select2 search inputs from the tab order.
       setTimeout(0) defers until after all page-specific select2 inits run.
       tabindex=-1 keeps them focusable via JS (for keyboard nav) but not via Tab. */
    setTimeout(function() {
        $('.select2-search-hidden .select2-input').attr('tabindex', '-1');
    }, 0);



    $('.back-btn').on('click', function(e) {
        /*return window.location='listCertificates';*/
        if ($('#cancelReturnPath').length > 0)
        {
            console.log($('#cancelReturnPath').val());
            return window.location = $('#cancelReturnPath').val();
        } else {
            console.log(window.history);
            return window.history.back();
        }
    });

    $(':checkbox').radiocheck();


});


function renderProgressCircles(size, scaleProgressImg, fontSize, forceRender=false) {
    $('.circle-progress').each(function(index) {

        // Need to check if there is HTML to stop re-rendering if function is called again
        if ($(this).html().trim() === '' || forceRender == true){
            var obj = $(this);
            if (forceRender==true){
                var c = $(this).children('canvas').eq(0);
                if (c.getContext) {
                    var ctx = c.getContext("2d");
                    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                }
            }
            var circle_type = obj.attr('data-circle-type');
            var size        = obj.attr('data-size');
            var value       = parseInt(obj.attr('data-score')) / 100;
            var attempt     = parseInt(obj.attr('data-attempt'));
            var isEmpty     = obj.attr('data-empty') == 'true';
            var didPass     = obj.attr('data-pass').toLowerCase();
            
            
        
            var color = "#ed1d4f";
            if (didPass === 'y' || didPass.toUpperCase() === 'YES') {
                didPass = true;
                color = "#2abf9e";
            } else {
                didPass = false;
            }
            if (value * 100 <= -1) {
                color = '#0698ce';
            }
            if (attempt <= 0 || isEmpty) {
                color = '#e3e3e3';
            }
            $(this).circleProgress({
                value: value>=0 ? value : 100,
                size: size,
                fill: {
                    color: color,
                    //gradient: ["black", "red"]
                }
            }).on('circle-animation-progress', function(event, progress, stepValue) {
                var obj = $(this).data('circle-progress'),
                    ctx = obj.ctx,
                    s = obj.size,
                    sv = (100 * stepValue).toFixed() + '%',
                    fill = obj.arcFill;
                if (value * 100 <= -1) {
                    if (value < 0 && attempt > 0 && !isEmpty) {
                        var imageObj = new Image();
                        imageObj.src = '/static/images/icons/loading-glass-blue.png';
                        if (scaleProgressImg) {
                            ctx.drawImage(imageObj, s / 2 - 6, s / 2 - 10, imageObj.width * 0.9, imageObj.height * 0.9);
                        } else {
                            ctx.drawImage(imageObj, s / 2 - 6, s / 2 - 10);
                        }
                    }
                } else {
                    // ctx.font = "bold " + s / 3 + "px Open Sans";
                    ctx.font = "bold "+fontSize+"px Open Sans";
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = fill;
                    ctx.fillText(sv, s / 2, s / 2);
                }
            }).on('circle-animation-end', function(event, progress, stepValue) {
                /* when exam submitted and passed exam then
                display fireworks after the score animation ends */
                if ($(".fireworks")[0]){
                    startFirework();
                }
            });

            var scoreLabel;
            if (isEmpty || attempt <= 0) {
                scoreLabel = 'No attempts yet';
            } else if (value * 100 <= -1) {
                scoreLabel = 'Score pending';
            } else {
                scoreLabel = (100 * value).toFixed() + '% \u2013 ' + (didPass ? 'Pass' : 'Fail');
            }
            $(this).attr({
                'role': 'img',
                'aria-label': scoreLabel
            });

        }
    });
}


/* Responsive font size based on container DIV size */
flexFont = function () {
    var divs = document.getElementsByClassName("flexFont");
    for(var i = 0; i < divs.length; i++) {
        var relFontsize = divs[i].offsetWidth*0.05;
        divs[i].style.fontSize = relFontsize+'px';
    }
};

window.onload = function(event) {
    flexFont();
};
window.onresize = function(event) {
    flexFont();
};

/* redirect with Javascript via POST */
function redirectPost(url, data) {
    var form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    form.action = url;
    for (var name in data) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = data[name];
        form.appendChild(input);
    }
    form.submit();
}

var delayFunction = function(f, delay=1000){
    setTimeout(function() { 
        f();
    }, delay);
}


function displayErrorModal(title, text, buttonText='CLOSE'){
    uid = Date.now();
    var trigger = document.activeElement;
    var xmlString =
                '<div id="error-message-'+uid+'" class="modal fade" role="dialog" aria-modal="true" aria-labelledby="error-title-'+uid+'" style="display: none;">\
                    <div class="modal-dialog modal-dialog-centered modal-confirm">\
                        <div class="modal-content">\
                            <div class="modal-header flex-column">\
                                <div class="oops"></div>\
                                <h4 id="error-title-'+uid+'" class="modal-title w-100 mt-0" tabindex="-1">'+title+'</h4>\
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close dialog">×</button>\
                            </div>\
                            <div class="modal-body">\
                                '+text+'\
                            </div>\
                            <div class="modal-footer justify-content-center">\
                                <button type="button" class="btn btn-primary green" data-dismiss="modal">'+buttonText+'</button>\
                            </div>\
                        </div>\
                    </div>\
                </div>';
    $(document.body).append(xmlString);
    $('#error-message-'+uid).modal('show');
    $('#error-message-'+uid).on('shown.bs.modal', function () {
        $('#error-title-'+uid).focus();
    });
    $('#error-message-'+uid).on('hidden.bs.modal', function () {
        $('#error-message-'+uid).remove();
        if (trigger && trigger.focus) { trigger.focus(); }
    });
}
function displaySuccessModal(title, text, buttonText='OK'){
    uid = Date.now();
    var trigger = document.activeElement;
    var xmlString =
                '<div id="success-message-'+uid+'" class="modal fade" role="dialog" aria-modal="true" aria-labelledby="success-title-'+uid+'" style="display: none;">\
                    <div class="modal-dialog modal-dialog-centered modal-confirm">\
                        <div class="modal-content">\
                            <div class="modal-header flex-column">\
                                <div class="icon-box">\
                                    <span class="x-icon" style="background-size:80px 80px; width:100px; height: 100px; "></span>\
                                </div>\
                                <h4 id="success-title-'+uid+'" class="modal-title w-100" tabindex="-1">'+title+'</h4>\
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close dialog">×</button>\
                            </div>\
                            <div class="modal-body">\
                                '+text+'\
                            </div>\
                            <div class="modal-footer justify-content-center">\
                                <button type="button" class="btn btn-primary green" data-dismiss="modal">'+buttonText+'</button>\
                            </div>\
                        </div>\
                    </div>\
                </div>';
    $(document.body).append(xmlString);
    $('#success-message-'+uid).modal('show');
    $('#success-message-'+uid).on('shown.bs.modal', function () {
        $('#success-title-'+uid).focus();
    });
    $('#success-message-'+uid).on('hidden.bs.modal', function () {
        $('#success-message-'+uid).remove();
        if (trigger && trigger.focus) { trigger.focus(); }
    });
}