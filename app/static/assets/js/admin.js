var sortableDict = {};
const sortableGroups = document.getElementsByName("sortableGroup");

var groupSendButton = document.getElementById("groupSend");
var tournamentSendButton = document.getElementById("tournamentSend");
var messageSetButton = document.getElementById("messageSet");
var notificationSendButton = document.getElementById("notificationSend");
var standingsSendButton = document.getElementById("standingsSend");
var matchUpdateButton = document.getElementById("matchUpdateSend");
var teamDataSendButton = document.getElementById("teamDataSend");
var databaseUploadButton = document.getElementById("databaseUpload");

var tournamentBets = document.getElementsByName("tournamentBet");
var messages = document.getElementsByName("message");

var alertNode = document.getElementById("alertNode");
var successAlertTemplate = document.getElementById("successalertTemplate");
var failureAlertTemplate = document.getElementById("dangeralertTemplate");

for (var sortableGroup of sortableGroups) {
    sortableDict[sortableGroup.getAttribute("value")] = 
        new Sortable(sortableGroup.querySelector('#sortableOrder'), {
            animation: 150,
            ghostClass: 'blue-background-class'
        });
}

function createAlert(message, success) {
    document.body.scrollTop = document.documentElement.scrollTop = 0;
    const alert = success ? successAlertTemplate.content.cloneNode(true) : failureAlertTemplate.content.cloneNode(true);
    const alertMessage = alert.getElementById("message");
    alertMessage.innerText = message;
    alertNode.appendChild(alert);    
}

function generateGenericRequest(button) {
    const request = new XMLHttpRequest();
    button.disabled = true;

    request.onload = function() {        
        if (request.status == 200) {
            createAlert(request.response, true);
            button.disabled = false;
        }
        else if (request.status == 400) {
            createAlert(request.response, false);
            button.disabled = false;
        }
        else if (request.status == 500) {            
            var internalError = document.getElementById("internalError");
            createAlert(internalError.innerText, false);
            button.disabled = false;
        }
    }

    request.onerror = function() {
        var connectionError = document.getElementById("connectionError");
        createAlert(connectionError.innerText, false);
        button.disabled = false;
    }

    return request;
}

function getData(address, button) {
    const request = generateGenericRequest(button);

    request.open('GET', address, true);
    request.send();
}

function postData(address, content, button) {
    const request = generateGenericRequest(button);

    request.open('POST', address, true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.send(JSON.stringify(content));
}

if (groupSendButton != null) {
    groupSendButton.onclick = function() {
        var groupsDict = {};
    
        for (const sortableElement of Object.entries(sortableDict)) {
            let[groupID, group] = sortableElement;
            groupsDict[groupID] = group.toArray();
        }
    
        postData("/admin/group-evaluation", groupsDict, this);
    }
}

if (tournamentSendButton != null) {
    tournamentSendButton.onclick = function() {
        var tournamentsDict = {};
    
        for (var tournamentBet of tournamentBets) {
            tournamentsDict[tournamentBet.getAttribute("data-user")] = tournamentBet.value;
        }
    
        postData("/admin/tournament-bet", tournamentsDict, this);
    }
}

messageSetButton.onclick = function() {
    var messageArray = [];

    for (var messageElement of messages) {        
        messageArray.push(messageElement.value);
    }

    postData("/admin/message", messageArray, this);
}

if (notificationSendButton != null) {
    notificationSendButton.onclick = () => {
        var notificationDict = {
            "subject" : document.getElementById("messageSubject").value,
            "text" : document.getElementById("messageText").value
        }
    
        postData("/admin/send-notification", notificationDict, this);
    }
}

if (matchUpdateButton != null) {
    matchUpdateButton.onclick = () => {
        getData("/admin/match-update", matchUpdateButton);
    }
}

if (standingsSendButton != null) {
    standingsSendButton.onclick = () => {
        getData("/admin/standings-notification", standingsSendButton);
    }
}

function uploadFiles(address, sendButton, fileData) {
    sendButton.disabled = true;

    const request = new XMLHttpRequest();
    request.timeout = 2000;

    request.upload.addEventListener("loadend", (event) => {
        
    });

    request.onerror = function() {
        var connectionError = document.getElementById("connectionError");
        createAlert(connectionError.innerText, false);
        sendButton.disabled = false;
    }

    request.onload = function() {        
        if (request.status == 200) {
            createAlert(request.response, true);
            sendButton.disabled = false;
        }
        else if (request.status == 400) {
            createAlert(request.response, false);
            sendButton.disabled = false;
        }
        else if (request.status == 500) {            
            var internalError = document.getElementById("internalError");
            createAlert(internalError.innerText, false);
            sendButton.disabled = false;
        }
    }

    request.open("POST", address, true);
    request.send(fileData);
}

teamDataSendButton.onclick = () => {
    const fileData = new FormData();
    fileData.append("team", document.getElementById("teamFile").files[0]);
    fileData.append("translation", document.getElementById("translationFile").files[0]);

    uploadFiles("/admin/team-data", teamDataSendButton, fileData);
}

databaseUploadButton.onclick = () => {
    const fileData = new FormData();
    fileData.append("database", document.getElementById("databaseFile").files[0]);
    
    uploadFiles("/admin/database", databaseUploadButton, fileData);
}
