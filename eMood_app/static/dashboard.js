$(document).ready(function(){
        $('.dropdown-toggle').click(function(){
            $(this).next('.dropdown-menu').slideToggle();
        });
    });