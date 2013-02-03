$(document).ready(function(){

    $('#printer').hide();

    $("span[id='print']").click(function() {

        if ($("#printer").is(":hidden")) {
            $('#printer').slideDown('fast', function() {});
        } else {
            $('#printer').slideUp('fast', function() {});
        }
        
    });

});