let selectedUser = null;
let moodChart;
moodColors = {
    "happy": {'backgroundColor': 'rgba(255, 255, 0, 0.2)', 'borderColor': 'rgba(255, 255, 0, 1)'},   // Yellow
    "sad": {'backgroundColor': 'rgba(0, 0, 255, 0.2)', 'borderColor': 'rgba(0, 0, 255, 1)'},         // Blue
    "angry": {'backgroundColor': 'rgba(255, 0, 0, 0.2)', 'borderColor': 'rgba(255, 0, 0, 1)'},       // Red
    "fear": {'backgroundColor': 'rgba(0, 255, 0, 0.2)', 'borderColor': 'rgba(0, 255, 0, 1)'},        // Green
    "surprise": {'backgroundColor': 'rgba(128, 0, 128, 0.2)', 'borderColor': 'rgba(128, 0, 128, 1)'}, // Purple
    "neutral": {'backgroundColor': 'rgba(255, 165, 0, 0.2)', 'borderColor': 'rgba(255, 165, 0, 1)'},  // Orange
}
$(document).ready(function () {
    displayUserData();
    $('button.btn.btn-secondary').on('click', function (e) {
        location.reload();
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
    $('#deletePersonForm').on('submit', function (e) {
        e.preventDefault();

        let form = $(this);
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: {
                csrf_token: form.find('input[name="csrf_token"]').val(),
                userId: selectedUser
            },
            success: function (response) {
                console.log(response);
                selectedUser = null;
                $('.modal-footer .btn-primary').hide();
                $('.modal-body').html('<h6 style="font-style: italic; text-align: center; color: grey;">Monitored user successfully deleted</h6>');
            },
            error: function (error) {
                console.log(error);
                $('.modal-body').html('<h6 style="font-style: italic; text-align: center; color: grey;">There was an error deleting the user, please try again.</h6>');
            }
        });
    });
});

function fetchUserInfo(userName) {
    $.ajax({
        url: `/dashboard/${userName}`,
        type: 'GET',
        success: function (data) {
            selectedUser = data.id;
            // Update the content with user information
            displayUserData(data);
        },
        error: function (error) {
            console.error('Error fetching user info:', error);
        }
    });
}

function findMostFrequent(arr) {
    if (arr.length === 0)
        return null;

    let freqMap = {};
    let maxCount = 0;
    let mostFrequentItem = null;

    arr.forEach(function (item) {
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
    $('#deleteUser').empty();
    $('#selectedUserPicture').empty();
    $('#selectedUserInfo').empty();

    $('#moodPieChartHeading').empty();
    $('#userWebsitesHeading').empty();

    if (moodChart) {
        moodChart.destroy();
    }

    if (!userData) {
        $('#noUserSelected').append('<em><p style=\"color:gray;\">No user selected</p></em>');
        return;
    } else {
        $('#noUserSelected').empty();

        var webpageList = $('<ul>');
        userData.webpages.forEach(function (webpage) {
            webpageList.append('<li>URL: ' + webpage.urls + '</li>');
        });

        var ctx = document.getElementById('moodPieChart').getContext('2d');
        let moodData = {};
        userData.moods.forEach(m => {
            moodData[m.mood] = (moodData[m.mood] + 1) || 1;
        });
        let moodBackgroundColors = [];
        let moodBorderColors = [];
        for (let mood in moodData) {
            if (moodColors[mood]) {
                moodBackgroundColors.push(moodColors[mood]['backgroundColor']);
                moodBorderColors.push(moodColors[mood]['borderColor']);
            } else {
                console.log(`Undefined Mood:${mood}`);
            }
        }
        var data = {
            labels: Object.keys(moodData),
            datasets: [{
                data: Object.values(moodData),
                backgroundColor: moodBackgroundColors,
                borderColor: moodBorderColors,
                borderWidth: 1
            }]
        };
        console.log(moodData);
        console.log(moodBackgroundColors);
        console.log(moodBorderColors);
        moodChart = new Chart(ctx, {
            type: 'pie',
            data: data,
        });

        let moods = userData.moods.map(m => m.mood);
        const mostFrequentMood = findMostFrequent(moods);
        let webpages = userData.webpages.map(w => w.urls);
        let mostFrequentWebsite = 'http://' + findMostFrequent(webpages);

        var userImage = $('<img>').attr('src', '/static/images/profile.png').css({
            'max-width': '200px',
            'max-height': '200px'
        }).addClass('img-fluid');
        var deleteUser = $('<button class="transparent-button">').html('<img src="/static/images/bin.png" style="max-width: 30px; max-heigth: 30px;">').addClass('img-fluid');
        deleteUser.click(function () {
            $('#deletePersonModal').modal('show');
        });

        $('#deleteUser').append(deleteUser);
        $('#selectedUserPicture').append(userImage);
        $('#selectedUserInfo').append('<p></p><p></p>');
        $('#selectedUserInfo').append('<p><strong>Name:</strong>  ' + userData.name + '</p>');
        $('#selectedUserInfo').append('<p><strong>Last active:</strong>  ' + userData.active + '</p>');
        $('#selectedUserInfo').append('<p><strong>Most frequent mood:</strong>  ' + mostFrequentMood + '</p>');
        $('#selectedUserInfo').append(`<p><strong>Most visited website:</strong> <a href="${mostFrequentWebsite}" target="_blank">${mostFrequentWebsite}</a></p>`);

        $('#moodPieChartHeading').append('Mood Overview')
        $('#userWebsitesHeading').append('Website Overview')
    }
}