const form = document.getElementById('upload-form');
const fileInput = document.getElementById('fileInput');
const result = document.getElementById('result');

form.addEventListener('submit', (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    fetch('/process', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        result.innerText = JSON.stringify(data.result); // Display the JSONified result string
    })
    .catch(error => {
        console.error(error);
        result.innerText = 'An error occurred. Please try again.';
    });
});
