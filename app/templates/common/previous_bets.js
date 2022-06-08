<script>
    var listSelector = document.getElementById("players");

    window.onload = function() {
        askPlayerPreviousBets(String(listSelector.value));
    }

    var betMap = new Map();

    var resultNode = document.getElementById("resultNode");

    function askPlayerPreviousBets(nameID) {
        var resultRequest = new XMLHttpRequest();
        resultRequest.open("GET", "./previous-bets?name=" +nameID);
        

        resultRequest.onload = function() {
            resultNode.innerHTML = resultRequest.response;
            betMap.set(nameID, resultRequest.response);
        }

        resultRequest.ontimeout = function() {
            resultNode.innerHTML = "{{load_timeout}}";
        }

        resultRequest.send();
    }
    
    listSelector.onchange = function() {
        if (betMap.get(this.value) == null) {
            resultNode.innerHTML = "{{load_in_progress}}";
            askPlayerPreviousBets(this.value);
        }
        else {
            resultNode.innerHTML = betMap.get(this.value);
        }
    }
</script>