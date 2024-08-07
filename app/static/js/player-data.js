var listSelector = document.getElementById("playerSelector");
var resultNode = document.getElementById("resultNode")
var playerSpinner = document.getElementById("playerSpinner");
var requestAddress = document.currentScript.getAttribute("data-data-path");

listSelector.onchange = function() {
    if (playerDataMap.get(this.value) == null) {
        resultNode.innerHTML = "";
        getPlayerData(this.value);
    }
    else {
        resultNode.innerHTML = playerDataMap.get(this.value);
    }
}

document.addEventListener("DOMContentLoaded", function() {
    getPlayerData(listSelector.value);
});

var playerDataMap = new Map();

var resultNode = document.getElementById("resultNode");

function getPlayerData(nameID) {
    listSelector.disabled = true;
    playerSpinner.classList.remove("d-none");
    
    var request = new XMLHttpRequest();    

    request.onload = function() {
        playerDataMap.set(nameID, request.response);
        resultNode.innerHTML = request.response;
        playerSpinner.classList.add("d-none");
        listSelector.disabled = false;
    }

    request.ontimeout = function() {
        const alert = document.getElementById("alertTemplate").content.cloneNode(true);
        const rootElement = document.getElementById("alertNode");
        rootElement.insertBefore(alert, rootElement.children[0]);
        listSelector.disabled = false;
    }

    request.open(`GET`, `./${requestAddress}?name=${nameID}`);    
    request.send();
}