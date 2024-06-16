var dateSelector = document.getElementById("dateSelector");
var dateSpinner = document.getElementById("dateSpinner");
var matchResultNode = document.getElementById("matchResultNode");

var date_dict = {};

dateSelector.onchange = () => {
    var date = dateSelector.options[dateSelector.selectedIndex].value;
    
    if (!(date in date_dict)) {
        getMatchDataByDate(date);
    }
    else {        
        matchResultNode.innerHTML = date_dict[date];
    }
}

document.addEventListener("DOMContentLoaded", function() {
    var date = dateSelector.options[dateSelector.selectedIndex].value;
    getMatchDataByDate(date);
});

function getMatchDataByDate(date) {
    dateSelector.disabled = true;
    dateSpinner.classList.remove("d-none");

    var request = new XMLHttpRequest();    

    request.onload = function() {
        date_dict[date] = request.response;
        matchResultNode.innerHTML = request.response;

        dateSelector.disabled = false;
        dateSpinner.classList.add("d-none")
    }

    request.ontimeout = function() {
        const alert = document.getElementById("alertTemplate").content.cloneNode(true);
        const rootElement = document.getElementById("alertNode");
        rootElement.insertBefore(alert, rootElement.children[0]);

        dateSelector.disabled = false;
        dateSpinner.classList.add("d-none")
    }

    request.open(`GET`, `./previous-bets/match?date=${date}`);
    request.send();
}
