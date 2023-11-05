$(function () {
    $('#loginForm').on('submit', function (e) {
        e.preventDefault();
        var dataToSend = $('#loginForm').serialize();
        console.log('Data to send: ', dataToSend);
         $.ajax({
            type: 'post',
            url: '/login',
            data: $('#loginForm').serialize(),
            success: function(response) {
                if (response === 'Email not found') {
                    $('#result').html('The email you entered does not match any account');
                } else if (response === 'Email and password do not match') {
                    $('#result').html('The password you entered is incorrect');
                } else {
                    window.location.href = '/profile';
                }
            }
        });
    })
});