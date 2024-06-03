function createMatchAlert(message) {
    while (matchAlertNode.children.length > 1) {
        matchAlertNode.removeChild(matchAlertNode.children[matchAlertNode.children.length - 1]);
    }

    const alert = alertTemplate.content.cloneNode(true);
    const alertMessage = alert.getElementById("message");
    alertMessage.innerText = message;
    matchAlertNode.appendChild(alert);
}

const myModal = document.getElementById("matchModal");
var modalInstance;
const alertTemplate = document.querySelector("#alertTemplate");
const matchAlertNode = document.getElementById("matchAlertNode");
const sendMatchButton = document.getElementById("sendMatchButton");

var modalTitle = document.getElementById("matchModalLabel");
var loadingText = modalTitle.innerText;
var creditInput = document.getElementById("creditInput");
var maxBetCredit = document.getElementById("maxCredit");
var matchDate = document.getElementById("matchDate");
var teamLabel1 = document.getElementById("teamLabel1");
var teamLabel2 = document.getElementById("teamLabel2");
var goalInput1 = document.getElementById("goalInput1");
var goalInput2 = document.getElementById("goalInput2");
var odd1 = document.getElementById("odd1");
var oddX = document.getElementById("oddX");
var odd2 = document.getElementById("odd2");

var admin = (myModal.getAttribute("data-admin") === "true");

sendMatchButton.onclick = function() {
    if (admin) {
        if (Number.isNaN(parseInt(goalInput1.value)) != Number.isNaN(parseInt(goalInput2.value))) {
            var differentGoals = document.getElementById("differentGoals");
            var message = differentGoals.innerText;
            createMatchAlert(message);
            return;
        }        
    }
    else {
        if (Number.isNaN(parseInt(goalInput1.value)) || Number.isNaN(parseInt(goalInput2.value)) || Number.isNaN(parseInt(creditInput.value))) {
            var invalidType = document.getElementById("invalidType");
            var message = invalidType.innerText;
            createMatchAlert(message);
            return;
        }
    
        if (goalInput1.value < 0 || goalInput2.value < 0 || creditInput.value <= 0) {
            var invalidValue = document.getElementById("invalidValue");
            var message = invalidValue.innerText;
            createMatchAlert(message);
            return;
        }
    }    

    var request = new XMLHttpRequest();

    request.onerror = function() {
        var invalidValue = document.getElementById("connectionError");
        var message = invalidValue.innerText;
        createMatchAlert(message);
        sendMatchButton.disabled = false;
    }

    request.onload = function() {
        if (request.status == 200) {
            modalInstance.hide();
            window.location.replace(admin ? "/admin" : "/");
        }
        else if (request.status == 400) {
            createMatchAlert(request.response);
            sendMatchButton.disabled = false;
        }
        else if (request.status == 500) {
            var invalidValue = document.getElementById("internalError");
            var message = invalidValue.innerText;
            createMatchAlert(message);
            sendMatchButton.disabled = false;
        }
    }

    var content = {
        'id' : modalTitle.value,
        'goal1': parseInt(goalInput1.value),
        'goal2': parseInt(goalInput2.value),
    };

    if (admin) {
        content['odd1'] = parseFloat(odd1.value);
        content['oddX'] = parseFloat(oddX.value);
        content['odd2'] = parseFloat(odd2.value);
        content['max_bet'] = parseInt(creditInput.value);
    }
    else {
        content['bet'] = parseInt(creditInput.value);
    }

    var address = admin ? `/admin/match` : `/match`;

    request.open('POST', address, true);
    request.setRequestHeader('Content-Type', 'application/json');

    request.send(JSON.stringify(content));

    sendMatchButton.disabled = true;
}

myModal.addEventListener('shown.bs.modal', (event) => {
    modalInstance = bootstrap.Modal.getInstance(myModal);

    var request = new XMLHttpRequest();
    
    request.onerror = function() {
        var invalidValue = document.getElementById("connectionError");
        var message = invalidValue.innerText;
        createMatchAlert(message);
        sendMatchButton.disabled = false;
    }

    request.onload = function() {
        if (request.status == 200) {
            var response = JSON.parse(request.response);
            var matchID = response['id'];
            modalTitle.innerText = matchID;
            modalTitle.value = matchID;

            teamLabel1.innerText = response['team1'];
            teamLabel2.innerText = response['team2'];

            goalInput1.value = response['goal1'];
            goalInput2.value = response['goal2'];

            if (admin) {
                matchDate.innerText = `${response['datetime']}`;
                creditInput.value = response['max_bet'];

                odd1.value = response['odd1'].toFixed(2);
                oddX.value = response['oddX'].toFixed(2);
                odd2.value = response['odd2'].toFixed(2);
            }
            else {
                matchDate.innerText = `${response['date']} ${response['time']} `;

                creditInput.max = response['max_bet'];
                creditInput.value = response['bet'];

                maxBetCredit.innerText = `/ ${response['max_bet']}`;

                odd1.innerText = `1: ${response['odd1'].toFixed(2)}`;
                oddX.innerText = `X: ${response['oddX'].toFixed(2)}`;
                odd2.innerText = `2: ${response['odd2'].toFixed(2)}`;
            }

        }
        else if (request.status == 400) {
            createMatchAlert(request.response);
            sendMatchButton.disabled = false;
        }
        else if (request.status == 500) {
            var invalidValue = document.getElementById("internalError");
            var message = invalidValue.innerText;
            createMatchAlert(message);
            sendMatchButton.disabled = false;
        }
    }

    var address = admin ? `/admin/match?matchID=${event.relatedTarget.id}` : `/match?matchID=${event.relatedTarget.id}`;

    request.open('GET', address, true);
    request.setRequestHeader('Content-Type', 'application/json');

    request.send();
});

myModal.addEventListener('hidden.bs.modal', (event) => {
    while (matchAlertNode.children.length > 0) {
        matchAlertNode.removeChild(matchAlertNode.children[matchAlertNode.children.length - 1]);
    }

    modalTitle.innerText = loadingText;
    matchDate.innerText = ""
    creditInput.value = "";

    if (admin) {
        odd1.value = "";
        oddX.value = "";
        odd2.value = "";
    }
    else {
        maxBetCredit.innerText = `/ ?`;
        odd1.innerText = "1: ";
        oddX.innerText = "X: ";
        odd2.innerText = "2: ";
    }    

    teamLabel1.innerText = "";
    teamLabel2.innerText = "";
    
    goalInput1.value = "";
    goalInput2.value = "";
});

window.history.pushState({}, document.title, window.location.pathname);