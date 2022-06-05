<script>
    var fetchResult = document.getElementById("fetchResult");

    var button = document.getElementById("")
    var sendButton = document.getElementById("fetchMatch");
    sendButton.onclick = function() {
        const XHR = new XMLHttpRequest();

        XHR.onload = function() {
            var responseObject = JSON.parse(XHR.response);
            var result = responseObject["result"];          
            
            if (result == true) {
                fetchResult.style.color = "green";
                fetchResult.innerText = "{{update_success}}";
            }
            else {
                fetchResult.style.color = "red";
                fetchResult.innerText = "{{update_failure}}";
            }
        };

        XHR.ontimeout = function() {
            fetchResult.innerText = "{{update_timeout}}";
            fetchResult.style.color = "red";
        };

        XHR.onerror = function() {
            alert('{{update_error}}');
        };

        XHR.open('GET', '/admin/fetch-match', true);

        fetchResult.innerText = "{{update_in_progress}}";
        fetchResult.style.color = "blue";

        XHR.send(null);
    };
</script>