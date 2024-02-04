let urlLog = [];
let token = null;
let userId = null;
let periodInMinutes = null;

function getBaseUrl(url) {
    let urlObj = new URL(url);
    return urlObj.hostname;
}

// Fetch the user ID and period in minutes when the extension starts up
fetch(chrome.runtime.getURL('userid.txt'))
    .then(response => response.text())
    .then(text => {
        const [id, period] = text.split('\n');
        userId = id.trim();
        periodInMinutes = Number(period.trim());

        console.log("Setting alarm with period:", periodInMinutes);
        chrome.alarms.create('fetchAndPost', {periodInMinutes: periodInMinutes}, function (alarm) {
            console.log("Alarm created", alarm);
        });
    });

async function isServerReachable(url) {
    try {
        const response = await fetch(url, {method: 'HEAD', mode: 'no-cors'});
        return true;
    } catch (e) {
        return false;
    }
}

async function fetchTokenAndPostUrls() {
    chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
        const tab = tabs[0]; //only detecting the active tab
        if (tab && tab.status === 'complete') {
            urlLog.push(getBaseUrl(tab.url));
        }

        let isReachable = await isServerReachable('https://emood.pythonanywhere.com/get-csrf-token');
        if (!isReachable) {
            return; // If the server is unreachable, don't throw an error, simply return
        }

        // Regular logic here
        try {
            const response = await fetch('https://emood.pythonanywhere.com/get-csrf-token');
            const data = await response.json();
            token = data['csrf_token']; // Token fetched from server
        } catch (error) {
            console.error('Error while fetching CSRF token:', error);
        }

        if (urlLog.length > 0 && token) {
            try {
                const response = await fetch('https://emood.pythonanywhere.com/webpage', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': token // Token is used here
                    },
                    body: JSON.stringify({urls: urlLog, userId: userId}),
                });

                const data = await response.json();
                console.log(data);
                urlLog = [];
            } catch (error) {
                console.error('Error while posting webpages:', error);
                urlLog = [];
            }
        }
    });
}

chrome.alarms.onAlarm.addListener(function (alarm) {
    console.log("Alarm fired!", alarm);
    if (alarm.name === 'fetchAndPost') {
        fetchTokenAndPostUrls();
    }
});