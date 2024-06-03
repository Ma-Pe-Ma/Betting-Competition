var sortableDict = {};
var tournamentOdds = {}

var teamSelector = document.getElementById("teamSelector");
var resultSelector = document.getElementById("resultSelector");
var tournamentBetOdd = document.getElementById("tournamentBetOdd");
var tournamentBetCredit = document.getElementById("tournamentBetCredit");
var tournamentExpectedPrize = document.getElementById("tournamentExpectedPrize");
var remainingCredit = document.getElementById("remainingCredit");
var groupSendButton = document.getElementById("sendButton");
var alertNode = document.getElementById("alertNode");
var alertTemplate = document.getElementById("alertTemplate");

function createAlert(message) {
    const alert = alertTemplate.content.cloneNode(true);
    const alertMessage = alert.getElementById("message");
    alertMessage.innerText = message;
    alertNode.appendChild(alert);
}

function populateSortableArray() {
    const sortableGroups = document.getElementsByName("sortableGroup");

    for (var sortableGroup of sortableGroups) {
        var sortableCredit = sortableGroup.querySelector("#sortableCredit")
        sortableCredit.oninput = trimGroupCredit;

        sortableDict[sortableGroup.getAttribute("value")] = [
            new Sortable(sortableGroup.querySelector('#sortableOrder'), {
                animation: 150,
                ghostClass: 'blue-background-class'
            }), sortableCredit
        ];
    }
}

function calculateRemainingCredit() {
    var remainingValue = parseInt(tournamentExpectedPrize.getAttribute("data-start-credit"));

    for (const groupTuple of Object.values(sortableDict)) {
        remainingValue -= groupTuple[1].value;
    }

    remainingValue -= tournamentBetCredit.value;
    remainingCredit.innerText = remainingValue;
}

function trimGroupCredit() {
    this.value =  Math.min(Math.max(this.value, this.min), this.max);
    calculateRemainingCredit();
}

function updateTournamentOdd() {
    //get the proper odd from selecting
    var newOdd = Object.values(tournamentOdds)[teamSelector.selectedIndex][resultSelector.selectedIndex];
    tournamentBetOdd.innerText = newOdd;

    //clamp value to proper range
    tournamentBetCredit.value =  Math.min(Math.max(tournamentBetCredit.value, tournamentBetCredit.min), tournamentBetCredit.max);    

    //calculate the expected prize
    tournamentExpectedPrize.value = Math.round(parseFloat(newOdd) * tournamentBetCredit.value * 100) / 100;
    tournamentExpectedPrize.innerText = Math.round(parseFloat(newOdd) * tournamentBetCredit.value * 100) / 100;

    calculateRemainingCredit();
}

function postGroupBet() {
    const request = new XMLHttpRequest();

    request.onload = function() {
        groupSendButton.disabled = true;
        
        if (request.status == 200) {
            window.location.replace("/");
        }
        else if (request.status == 400) {
            createAlert(request.response);
            groupSendButton.disabled = false;
        }
        else if (request.status == 500) {
            var internalError = document.getElementById("internalError");
            createAlert(internalError.innerText);
            groupSendButton.disabled = false;
        }
    }

    request.onerror = function() {
        var connectionError = document.getElementById("connectionError");
        createAlert(connectionError.innerText);
        groupSendButton.disabled = false;
    }

    var groupsObject = {};

    for (const [groupID, group_tuple] of Object.entries(sortableDict)) {
        groupsObject[groupID] = {            
            "bet" : group_tuple[1].value,            
            "order" : group_tuple[0].toArray()
        };
    }

    var output = {
        "tournament" : {"team" : teamSelector.options[teamSelector.selectedIndex].value, "result" : resultSelector.options[resultSelector.selectedIndex].value, "bet" : tournamentBetCredit.value},
        "group" : groupsObject
    };

    request.open('POST', '/group-bet', true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.send(JSON.stringify(output));
}

window.onload = function() {
    teamSelector.onchange = updateTournamentOdd;
    resultSelector.onchange = updateTournamentOdd;
    tournamentBetCredit.oninput = updateTournamentOdd;
    
    groupSendButton.onclick = postGroupBet;

    //load tournament bet data
    fetch('/tournament-bet.json')
    .then(response => response.json())
    .then(data => {
        tournamentOdds = data;

        var index = 0;

        var tableBodyElement = document.getElementById("oddBody");
        var teamOddTemplate = document.getElementById("teamTemplate")

        //initialize teamselector
        for (const [key, value] of Object.entries(tournamentOdds)) {
            teamSelector.options[teamSelector.options.length] = new Option(value["tr"], key);

            if (key == teamSelector.getAttribute("data-user-team")) {
                teamSelector.selectedIndex = index;
                tournamentBetOdd.innerText = value[resultSelector.selectedIndex];
                tournamentBetOdd.value = value[resultSelector.selectedIndex];
            }

            index++;

            var newTableRow = teamOddTemplate.content.cloneNode(true);
            
            newTableRow.getElementById("team").innerText = value["tr"];
            newTableRow.getElementById("t1").innerText = value[0].toFixed(2);
            newTableRow.getElementById("t2").innerText = value[1].toFixed(2);
            newTableRow.getElementById("t4").innerText = value[2].toFixed(2);
            newTableRow.getElementById("t8").innerText = value[3].toFixed(2);

            tableBodyElement.appendChild(newTableRow);
        }

        populateSortableArray();
        updateTournamentOdd();
    })
  .catch(error => console.error('Error fetching file:', error));   
}