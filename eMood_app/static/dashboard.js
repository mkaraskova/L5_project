$(document).ready(function () {
    $('.dropdown-toggle').click(function () {
        $(this).next('.dropdown-menu').slideToggle();
    });

    $('#addPersonForm').on('submit', function (e) {
        e.preventDefault();

        // FormData from form
        let formData = new FormData(this);

        fetch("/add-person", {
            method: "POST",
            body: formData
        })
            .then(response => {
                // Trigger file download directly
                response.blob().then(blob => {
                    var link = document.createElement('a');
                    link.href = window.URL.createObjectURL(blob);
                    link.download = `eMood_plugin_${formData.get('name')}.zip`;
                    link.click();

                    // Hide the "Add" button and display the success message
                    $('.modal-footer .btn-primary').hide();
                    $('.modal-body').html('<h6 style="font-style: italic; text-align: center; color: grey;">Plugin successfully downloaded</h6>');
                });
            })
            .catch(error => console.log('error', error));
    });

    $('.dropdown-item').on('click', function () {
        var selectedUserName = $(this).text();
        $('#selectedUserName').text(selectedUserName);

        $.get(`/user/${selectedUserName}`, function (data) {

        });
        $(this).closest('.dropdown').find('.dropdown-toggle').trigger('click');
    });
});
