let selectedUser = null;
let moodChart;
let webpageBarChart;
let calendar;

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
    $('button.btn.refresh-btn').on('click', function (e) {
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

function fetchDataForDate(selectedDate, userData) {
    let dataForDate = {
        pieData: {labels: [], datasets: []},
        barData: {labels: [], datasets: []},
        timelineData: []
    };

    let moodDataForDate = {};
    let timelineMoodDataForDate = {};
    moodDataForDate[selectedDate] = [];
    timelineMoodDataForDate[selectedDate] = [];
    userData.moods.forEach(mood => {
        let date = new Date(mood.timestamp);
        let formattedMoodDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

        if (formattedMoodDate == selectedDate) {
            moodDataForDate[selectedDate].push(mood.mood);
            timelineMoodDataForDate[selectedDate].push(mood);
        }
    });

    let pieData = {};
    moodDataForDate[selectedDate].forEach(m => {
        pieData[m] = (pieData[m] + 1) || 1;
    });
    let pieBackgroundColors = [];
    let pieBorderColors = [];
    for (let mood in pieData) {
        if (moodColors[mood]) {
            pieBackgroundColors.push(moodColors[mood]['backgroundColor']);
            pieBorderColors.push(moodColors[mood]['borderColor']);
        } else {
            console.log(`Undefined Mood:${mood}`);
        }
    }
    dataForDate.pieData.labels = Object.keys(pieData);
    dataForDate.pieData.datasets.push({data: Object.values(pieData), backgroundColor: pieBackgroundColors});

    let webPageDataForDate = {};
    let timelineWebPageDataForDate = {};
    webPageDataForDate[selectedDate] = [];
    timelineWebPageDataForDate[selectedDate] = [];
    userData.webpages.forEach(web => {
        let date = new Date(web.timestamp);
        let formattedWebDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

        if (formattedWebDate == selectedDate) {
            webPageDataForDate[selectedDate].push(web.urls);
            timelineWebPageDataForDate[selectedDate].push(web);
        }
    });

    let barData = {};
    webPageDataForDate[selectedDate].forEach(w => {
        barData[w] = (barData[w] + 1) || 1;
    });
    dataForDate.barData.labels = Object.keys(barData);

    dataForDate.barData.datasets.push({data: barData, label: 'Webpage frequency', backgroundColor: '#B89BC7'});

    // Convert moods data into timeline items
    let moodItems = timelineMoodDataForDate[selectedDate].map((moodRecord) => {
        let moodDate = new Date(moodRecord.timestamp)
        return {
            start: moodDate,
            title: moodRecord.mood
        };
    });

    // Convert webpage data into timeline items
    let webpageItems = timelineWebPageDataForDate[selectedDate].map((webRecord) => {
        let webpageDate = new Date(webRecord.timestamp)
        return {
            start: webpageDate,
            title: webRecord.urls,
        };
    });

    dataForDate.timelineData = [...moodItems, ...webpageItems]
    console.log(dataForDate.timelineData)
    return dataForDate;
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
    if (webpageBarChart) {
        webpageBarChart.destroy();
    }

    if (!userData) {
        $('#noUserSelected').append('<em><p style=\"color:gray;\">No user selected</p></em>');
        return;
    } else {
        $('#noUserSelected').empty();

        // mood Pie Chart
        {
            let moodData = {};
            var ctx = document.getElementById('moodPieChart').getContext('2d');
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

            moodChart = new Chart(ctx, {
                type: 'pie',
                data: data,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'right'
                        }
                    }
                }
            });
        }

        // webpage Bar Chart
        {
            let webpageData = {};
            userData.webpages.forEach(w => {
                try {
                    let urlString = w.urls;
                    // Add 'https://' if it is not present
                    if (!/^https?:\/\//i.test(urlString)) {
                        urlString = 'https://' + urlString;
                    }
                    let url = new URL(urlString).hostname;
                    webpageData[url] = (webpageData[url] + 1) || 1;
                } catch (e) {
                    console.error('Invalid URL: ', w.urls);
                }
            });
            var ctxWebpage = document.getElementById('webPageBarChart').getContext('2d');
            var webpageChartData = {
                labels: Object.keys(webpageData),
                datasets: [{
                    label: 'Webpage frequency',
                    data: Object.values(webpageData),
                    backgroundColor: '#B89BC7',
                    borderColor: '#B89BC7'
                }]
            };

            webpageBarChart = new Chart(ctxWebpage, {
                type: 'bar',
                data: webpageChartData
            });
        }

        let moods = userData.moods.map(m => m.mood);
        const mostFrequentMood = findMostFrequent(moods);
        let webpages = userData.webpages.map(w => w.urls);
        let mostFrequentWebsite = 'http://' + findMostFrequent(webpages);
        let CalendarPieChart = null;
        let CalendarBarChart = null;
        let CalendarTimeline = null;

        // calendar
        {
            var userImage = $('<img>').attr('src', '/static/images/profile.png').css({
                'max-width': '200px',
                'max-height': '200px'
            }).addClass('img-fluid');
            var deleteUser = $('<button class="transparent-button">').html('<img src="/static/images/bin.png" style="max-width: 30px; max-heigth: 30px;">').addClass('img-fluid');
            deleteUser.click(function () {
                $('#deletePersonModal').modal('show');
            });

            let dailyMoods = {};
            let moodsByDate = {};
            userData.moods.forEach(moodData => {
                let date = new Date(moodData.timestamp);
                let formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

                if (moodsByDate[formattedDate]) {
                    moodsByDate[formattedDate].push(moodData.mood);
                } else {
                    moodsByDate[formattedDate] = [moodData.mood];
                }
            });

            for (let date in moodsByDate) {
                dailyMoods[date] = findMostFrequent(moodsByDate[date]);
            }

            var calendarEl = document.getElementById('calendar');

            var calendar = new FullCalendar.Calendar(calendarEl, {
                firstDay: 1,
                height: 'auto',
                initialView: 'dayGridMonth',
                dayMaxEventRows: true,
                dayCellClassNames: ['calendarButtonClass'],
                events: Object.keys(dailyMoods).map((date) => ({
                    title: dailyMoods[date],
                    start: date,
                    allDay: true,
                    color: moodColors[dailyMoods[date]].backgroundColor,
                    display: 'background',
                    overlap: false,
                    textColor: 'black'
                })),
                eventContent: function (arg) {
                    var arrayOfDomNodes = []
                    var el = document.createElement('div');
                    el.innerHTML = arg.event.title;
                    el.style.lineHeight = 'normal'; // Set back to normal
                    el.style.height = '100%';
                    el.style.display = 'flex';
                    el.style.justifyContent = 'center';
                    el.style.alignItems = 'center';
                    arrayOfDomNodes.push(el);
                    return {domNodes: arrayOfDomNodes};
                },
                dateClick: function (info) {
                    let dateClicked = info.dateStr;
                    let calendarData = fetchDataForDate(dateClicked, userData);

                    if (CalendarPieChart != null) CalendarPieChart.destroy();
                    let pieCtx = document.getElementById('dailyMoodPieChart').getContext('2d');
                    CalendarPieChart = new Chart(pieCtx, {
                        type: 'pie',
                        data: calendarData.pieData,
                        options: {
                            responsive: true,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Mood Day Overview',
                                    font: {
                                        size: 20
                                    }
                                },
                                legend: {
                                    display: true,
                                    position: 'right'
                                }
                            }
                        }
                    });

                    if (CalendarBarChart != null) CalendarBarChart.destroy();
                    let barCtx = document.getElementById('dailyWebPageBarChart').getContext('2d');
                    CalendarBarChart = new Chart(barCtx, {
                        type: 'bar',
                        data: calendarData.barData,
                        options: {
                            responsive: true,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Website Day Overview',
                                    font: {
                                        size: 20
                                    }
                                },
                                legend: {
                                    display: true
                                }
                            }
                        }
                    });
                    console.log(new Date(info.dateStr));
                    var dayCalendar = document.getElementById('dayCalendar');
                    var timelineCalendar = new FullCalendar.Calendar(dayCalendar, {
                        initialView: 'timeGridDay',
                        height: 'auto',
                        events: calendarData.timelineData,
                    });
                    $("#calendarModal").modal('show');
                    timelineCalendar.render();

                }
            });

            calendar.render();
        }

        $('#deleteUser').append(deleteUser);
        $('#selectedUserPicture').append(userImage);
        $('#selectedUserInfo').append('<p></p><p></p>');
        $('#selectedUserInfo').append('<p><strong>Name:</strong>  ' + userData.name + '</p>');
        $('#selectedUserInfo').append('<p><strong>Last active:</strong>  ' + userData.active + '</p>');
        $('#selectedUserInfo').append('<p><strong>Most frequent mood:</strong>  ' + mostFrequentMood + '</p>');
        $('#selectedUserInfo').append(`<p><strong>Most visited website:</strong> <a href="${mostFrequentWebsite}" target="_blank">${mostFrequentWebsite}</a></p>`);

        $('#moodPieChartHeading').append('Mood Overview');
        $('#userWebsitesHeading').append('Website Overview');
    }
}