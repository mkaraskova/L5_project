$(document).ready(function () {
    displayUserData();
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

function findMostFrequent(arr) {
    if(arr.length === 0)
        return null;

    let freqMap = {};
    let maxCount = 0;
    let mostFrequentItem = null;

    arr.forEach(function(item) {
        freqMap[item] = (freqMap[item] + 1) || 1;
        if (freqMap[item] > maxCount) {
            maxCount = freqMap[item];
            mostFrequentItem = item;
        }
    });

    return mostFrequentItem;
}

function displayUserData(userData) {
    // Clear old data
    $('#selectedUserPicture').empty();
    $('#selectedUserInfo').empty();
    $('#selectedUserMoods').empty();
    $('#selectedUserWebsites').empty();

    if (!userData) {
        $('#noUserSelected').append('<em><p style=\"color:gray;\">No user selected</p></em>');
        return;
    }

    else {
        $('#noUserSelected').empty();

        var webpageList = $('<ul>');
        userData.webpages.forEach(function (webpage) {
            webpageList.append('<li>URL: ' + webpage.urls + '</li>');
        });

        var moodList = $('<ul>');
        userData.moods.forEach(function (m) {
            moodList.append('<li>Mood: ' + m.mood + '</li>');
        });

        let moods = userData.moods.map(m => m.mood);
        const mostFrequentMood = findMostFrequent(moods);
        let webpages = userData.webpages.map(w => w.urls);
        let mostFrequentWebsite = findMostFrequent(webpages);

        var userImage = $('<img>').attr('src', '/static/images/profile.png').css({ 'max-width': '200px', 'max-height': '200px' });
        userImage.addClass('img-fluid');
        $('#selectedUserPicture').append(userImage);
        $('#selectedUserInfo').append('<p></p><p></p>');
        $('#selectedUserInfo').append('<p><strong>Name:</strong>  ' + userData.name + '</p>');
        $('#selectedUserInfo').append('<p><strong>Last active:</strong>  ' + userData.active + '</p>');
        $('#selectedUserInfo').append('<p><strong>Most frequent mood:</strong>  ' + mostFrequentMood + '</p>');
        $('#selectedUserInfo').append(`<p><strong>Most visited website:</strong> <a href="${mostFrequentWebsite}" target="_blank">${mostFrequentWebsite}</a></p>`);

        $('#selectedUserMoods').append('<p>User Moods:</p>').append(moodList);
        $('#selectedUserWebsites').append('<p>User Visited pages:</p>').append(webpageList);
    }
}