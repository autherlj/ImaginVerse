document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(this);
    fetch('/upload', {
        method: 'POST',
        body: formData
    });
});

const eventSource = new EventSource('/stream');
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    document.getElementById('output').value += data.message + '\n';
};