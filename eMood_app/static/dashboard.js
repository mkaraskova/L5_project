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

    function fetchUserInfo(userName) {
        $.ajax({
            url: `/dashboard/${userName}`,
            type: 'GET',
            success: function (data) {
                // Update the content with user information
                displayUserData(data);
            },
            error: function (error) {
                console.error('Error fetching user info:', error);
            }
        });
    }

    // Call fetchUserInfo when a user is clicked in the dropdown
    $('.dropdown-item').click(function (e) {
        e.preventDefault();
        var userName = $(this).text().trim();

        // Update URL without reloading the page
        history.pushState({}, '', `/dashboard/${userName}`);

        fetchUserInfo(userName);
    });
});

function updateDropdownText(selectedOption) {
    document.getElementById('dropdownMenuButton').innerText = selectedOption + '\u00A0\u00A0\u00A0';
    var dropdownToggle = document.querySelector('.dropdown-toggle');
    dropdownToggle.click();
}

function displayUserData(userData) {

}