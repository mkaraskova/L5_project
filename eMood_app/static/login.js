$(function() {
  $('#loginForm').on('submit', function(e) {
    e.preventDefault();
    $.ajax({
      type: 'post',
      url: '/login',
      data: $('#loginForm').serialize(),
      success: function(response) {
        if(response.startsWith('Bad Login')) {
          $('#result').html(response);
        } else {
          window.location.href = '/protected';
        }
      }
    });
  });
});