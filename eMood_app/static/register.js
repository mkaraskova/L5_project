$(function() {
  $('#registerForm').on('submit', function(e) {
    if($('#form3Example4').val() === $('#form3Example5').val()) {
        e.preventDefault();
        $.ajax({
            type: 'post',
            url: '/register',
            data: $('#registerForm').serialize(),
            success: function(response) {
                if (response.startsWith('Email already exists')) {
                    $('#result').html(response);
                } else {
                    window.location.href = '/login';
                }
            }
        });
    } else {
        e.preventDefault();
        $('#result').html('Passwords must match!');
    }
  });
});