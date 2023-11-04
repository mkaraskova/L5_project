$(function() {
  $('#loginForm').on('submit', function(e) {
    e.preventDefault();
    if($('#form3Example4').val() === $('#form3Example5').val()) {

        $.ajax({
            type: 'post',
            url: '/register',
            data: $('#loginForm').serialize()
        })
        .done(function(response) {
            if (response.startsWith('Email already exists')) {
                $('#result').html(response);
            } else {
                window.location.href = '/login';
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            // Display an error message if something goes wrong
            $('#result').html('Something went wrong. Try again later.');
        });
    } else {
        $('#result').html('Passwords must match!');
    }
  });
});