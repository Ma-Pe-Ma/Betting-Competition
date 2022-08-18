<script type="module">
    var sortableArray = [];

    window.onload = populateSortableArray();

    function populateSortableArray() {
        {% for group in groups %}
        
        sortableArray.push(["{{group.ID}}", new Sortable(document.getElementById('list-{{group.ID}}'), {
            animation: 150,
            ghostClass: 'blue-background-class'
        })]);
        {% endfor %}
    }

    var sendButton = document.getElementById("sendButton");
        sendButton.onclick = function() {
        //console.log('Sending data');

        const XHR = new XMLHttpRequest();

        XHR.onload = function() {
            var responseObject = JSON.parse(XHR.response);

            var message = "{{unknown_event}}";
            var messageNode = document.getElementById("errorMessage");

            if (responseObject["result"] == "OK") {
                message = "{{set_success}}";
                messageNode.style = "padding-left:1em; color:green;"
            }
            else if (responseObject["result"] == "error") {
                message = "{{set_failure}}";
                messageNode.style = "padding-left:1em; color:red;"
            }
            
            messageNode.innerText = message;                                
        }

        XHR.onerror = function() {
            alert( '{{communication_error}}' );
        }

        // Set up our request
        XHR.open( 'POST', '/admin/group-evaluation', true);

        // Add the required HTTP header for form data POST requests
        //XHR.setRequestHeader( 'Content-Type', 'application/x-www-form-urlencoded' );
        XHR.setRequestHeader('Content-Type', 'application/json');
        
        var groupsObject = {};

        for (const sortableElement of sortableArray) {
            let[groupID, group] = sortableElement;

            var groupObject = {}
            groupsObject[groupID] = group.toArray();
        }

        XHR.send(JSON.stringify(groupsObject));
    }
</script>