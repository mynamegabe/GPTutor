const button = document.getElementById('loadForm');
button.addEventListener("click", async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  console.log('You clicked something!');
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: loadForm,
  });
});

function loadForm() {
  url = window.location.href;
  newURL = 'http://localhost:8000/create?url=' + url;
  console.log(newURL)
  window.open(newURL, '_blank');
}

// loadButton.addEventListener("click", async () => {
//   let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//   console.log('You clicked the button!');
//   chrome.scripting.executeScript({
//     target: { tabId: tab.id },
//     function: loadForm,
//   });
// });
