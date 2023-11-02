$(function() {
  $('#registerForm').on('submit', function(e) {
    e.preventDefault();
    $.ajax({
      type: 'post',
      url: '/register',
      data: $('#registerForm').serialize(),
      success: function(response) {
        $('#result').html(response);
      }
    });
  });
});