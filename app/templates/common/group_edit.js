<script>
    var sortableArray = [];

    var teamSelect = document.getElementById("teamSelect");
    var resultSelect = document.getElementById("resultSelect");
    var finalResultOdd = document.getElementById("finalResultOdd");
    var finalResultBet = document.getElementById("finalResultBet");
    var expectedWinAmount = document.getElementById("expectedWinAmount");

    function populateSortableArray() {
        {% for group_id, group in groups.items() %}
        sortableArray.push(["{{group_id}}", new Sortable(document.getElementById('list-{{group_id}}'), {
            animation: 150,
            ghostClass: 'blue-background-class'
        })]);
        {% endfor %}

        teamSelect.value = "{{tournament_bet.team}}";
        resultSelect.value = "{{tournament_bet.result}}";
    }

    function calculateRemainingBetAmount() {
        var remainingValue = {{bet_values.starting_bet_amount}}; //??

        for (const sortableElement of sortableArray) {
            let[groupID, group] = sortableElement;
            remainingValue -=  document.getElementById("bet-" + groupID).value;
        }

        remainingValue -= finalResultBet.value;
        remainingAmount.innerText = remainingValue + " {{bet_unit}} ";
    }

    var resultNamemap = {
        "0" : "{{champion}}",
        "1" : "{{finalist}}",
        "2" : "{{semi_final}}",
        "3" : "{{knockout}}"
    }

    var scores = {
    {% for group in groups.values() %}
        {% for team in group.teams %} "{{team.name}}" : [{{team.top1}}, {{team.top2}}, {{team.top4}}, {{team.top16}}],{% endfor %}
    {% endfor %}
    }

    var namemap = {
    {% for group in groups.values() %}
        {% for team in group.teams %} "{{team.name}}" : "{{team.local_name}}",{% endfor %}
    {% endfor %}
    };

    scores = Object.keys(scores).sort().reduce(
        (obj, key) => { 
          obj[key] = scores[key]; 
          return obj;
        }, 
        {}
      );

    for (const [key, value] of Object.entries(scores)) {
        teamSelect.options[teamSelect.options.length] = new Option(namemap[key], key);
    }

    for (let i = 0; i < 4; i++) {
        resultSelect.options[resultSelect.options.length] = new Option(resultNamemap[`${i}`], i);
    }

    function updateFinalBet() {
        var teamID = teamSelect.options[teamSelect.selectedIndex].value;
        var resultID = resultSelect.options[resultSelect.selectedIndex].value;

        var odd = scores[teamID][resultID];
        finalResultOdd.innerText = odd;
        finalResultOdd.value = odd;

        expectedWinAmount.value = Math.round(odd * finalResultBet.value * 100) / 100;

        calculateExpectedWinAmount();
    }

    function calculateExpectedWinAmount() {
        expectedWinAmount.value = Math.round(parseFloat(finalResultOdd.value) * finalResultBet.value * 100) / 100;
        expectedWinAmount.innerText = Math.round(parseFloat(finalResultOdd.value) * finalResultBet.value * 100) / 100;
    }

    teamSelect.onchange = updateFinalBet;
    resultSelect.onchange = updateFinalBet;

    finalResultBet.oninput = function() {
        if (this.value > {{bet_values.max_tournament_bet_value}}) {
            this.value = {{bet_values.max_tournament_bet_value}};
            this.innerText = {{bet_values.max_tournament_bet_value}};
        }

        if (this.value < 0) {
            this.value = 0;
            this.innerText = 0;
        }

        calculateExpectedWinAmount();
        calculateRemainingBetAmount();
    }

    var sendButton = document.getElementById("sendButton");
    sendButton.onclick = function() {
        const XHR = new XMLHttpRequest();

        XHR.onload = function() {
            var responseObject = JSON.parse(XHR.response);
            
            if (responseObject["result"] == "OK") {
                //window.location.href = "./?match_state=group";
            }
            else if (responseObject["result"] == "error") {
                var info = responseObject["info"];

                var errorMessage = "";

                switch(info) {
                    case "FINAL_TEAM":
                    errorMessage = "{{final_team}}";
                    break;

                    case "FINAL_RESULT":
                    errorMessage = "{{final_result}}";
                    break;

                    case "tournament_bet":
                    errorMessage = "{{tournament_bet_message}}";
                    break;

                    case "GROUP_BET":
                    errorMessage = "{{group_bet}}";
                    break;

                    case "GROUP_ID":
                    errorMessage = "{{group_id}}";
                    break;

                    case "GROUP_TEAM":
                    errorMessage = "{{group_team}}";
                    break;
                }
                
                var errorMessageNode = document.getElementById("errorMessage");
                errorMessageNode.innerText = errorMessage;
            }
        }

        XHR.onerror = function() {
            alert("{{communication_error}}" );
        }

        XHR.open('POST', '/group', true);
        XHR.setRequestHeader( 'Content-Type', 'application/json' );
        
        var output = {};

        var finalObject = {"team" : teamSelect.options[teamSelect.selectedIndex].value, "result" : resultSelect.options[resultSelect.selectedIndex].value, "bet" : document.getElementById("finalResultBet").value};
        output["final"] = finalObject;

        var groupsObject = {};

        for (const sortableElement of sortableArray) {
            let[groupID, group] = sortableElement;

            var groupObject = {}

            groupObject["bet"] = document.getElementById("bet-" + groupID).value;
            groupObject["order"] = group.toArray();

            groupsObject[groupID] = groupObject;
        }

        output["group"] = groupsObject;
        XHR.send(JSON.stringify(output));
    }

    var remainingAmount = document.getElementById("remainingAmount");

    window.onload = function() {
        populateSortableArray();
        updateFinalBet();
        calculateRemainingBetAmount();
    }
</script>