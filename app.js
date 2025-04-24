document.getElementById("convertForm").onsubmit = function(e) {
    e.preventDefault();
    convertInput();
};

document.getElementById("historyButton").onclick = getHistory;
document.getElementById("clearButton").onclick = clearResults;

// Show history on page load
window.onload = getHistory;

function convertInput() {
    const userInput = document.getElementById("userInput").value;
    fetch("http://127.0.0.1:8888/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input_string: userInput })
    })
    .then(response => response.json())
    .then(data => {
        const resultArea = document.getElementById("resultArea");
        if (data.output) {
            resultArea.innerHTML = `<strong>Output:</strong> [${data.output.join(', ')}]`;
        } else if (data.result) {
            resultArea.innerHTML = `<strong>Output:</strong> [${data.result.join(', ')}]`;
        } else if (data.detail) {
            resultArea.innerHTML = `<span class="text-danger">Error: ${data.detail}</span>`;
        }
        getHistory(); // Refresh history after conversion
    })
    .catch(error => {
        document.getElementById("resultArea").innerHTML = `<span class="text-danger">Error: ${error}</span>`;
    });
}

function getHistory() {
    fetch("http://127.0.0.1:8888/api/history")
    .then(response => response.json())
    .then(data => {
        const historyArea = document.getElementById("historyArea");
        historyArea.innerHTML = "";
        if (data.history && data.history.length > 0) {
            data.history.forEach(item => {
                const div = document.createElement("div");
                div.innerHTML = `<strong>Input:</strong> ${item.input} <br><strong>Output:</strong> [${item.output.join(', ')}]`;
                historyArea.appendChild(div);
            });
        } else {
            historyArea.innerHTML = "<span class='text-muted'>No history found.</span>";
        }
    })
    .catch(error => {
        document.getElementById("historyArea").innerHTML = `<span class="text-danger">Error: ${error}</span>`;
    });
}

function clearResults() {
    document.getElementById("resultArea").innerHTML = "";
    document.getElementById("historyArea").innerHTML = "";
}