$(document).ready(function () {
    // disable right click
    $("body").on("contextmenu",function(e){
        return false;
    });
});
//disable cut/copy 
$('body').bind('cut copy', function (e) {
    e.preventDefault();
});