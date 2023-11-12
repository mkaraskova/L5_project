let urlLog = [];
let token = null;

async function fetchTokenAndPostUrls() {
  chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
    const tab = tabs[0]; // There will be only one active tab in the current window
    if (tab.status === 'complete') {
      urlLog.push(tab.url);
    }

    try {
      const response = await fetch('http://localhost:4000/get-csrf-token');
      const data = await response.json();
      token = data['csrf_token']; // Token fetched from server
    } catch (error) {
      console.error('Error while fetching CSRF token:', error);
    }

    if (urlLog.length > 0 && token) {
      try {
        const response = await fetch('http://localhost:4000/webpage', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token // Token is used here
          },
          body: JSON.stringify({ urls: urlLog }),
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

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('fetchAndPost', { periodInMinutes: 1 });
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'fetchAndPost') {
    fetchTokenAndPostUrls();
  }
});
