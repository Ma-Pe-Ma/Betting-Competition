<script>
var commentsElement = document.getElementById("comments");
var postCommentButton = document.getElementById("postCommentButton");
var loadOldCommentsButton = document.getElementById("loadOldCommentsButton");
var refreshCommentsButton = document.getElementById("refreshCommentsButton");
var commentField = document.getElementById("commentField");

var statusMap = new Map([
    ["INVALID_DATA", "{{invalid_data}}"],
    ["SHORT_MESSAGE", "{{short_message}}"],
    ["ERROR", "{{error_connection}}"],
]);

function parseReceivedComments(responseObject) {
    var comments = responseObject["comments"]
    var newComment = responseObject["newerComments"];

    if (comments.length < 10 && !newComment) {
        loadOldCommentsButton.disabled = true;
    }

    var colors = ["lightgreen", "yellow"]

    var offset = 0;

    var lastElement = commentsElement.children[commentsElement.children.length -1];

    if (!newComment || (commentsElement.children.length != 0 && lastElement.style.backgroundColor == colors[0])) {
        offset = 1;
    }

    for (var i = 0; i < comments.length; i++ ) {
        let comment = comments[i];            
        var content = comment["comment"];

        var commentElement = document.createElement("div");
        commentElement.style = "background-color: " + colors[(offset + i) % 2];
        commentElement.setAttribute("value", comment["datetime"]);
        commentElement.innerHTML =
        `<h4 style="display:inline-flex; margin-left: 10px;">${comment["username"]}</h4>
        <h4 style="display:inline-flex;">-</h4>
        <h4 style="display:inline-flex;">${comment["datetime"]}</h4><br>
        <div style="margin-left: 20px;">${content}</div><br>`;

        if (newComment) {                
            commentsElement.append(commentElement);
            commentsElement.scrollTop = commentsElement.scrollHeight;
        }
        else {
            commentsElement.insertBefore(commentElement, commentsElement.children[0]);
            commentsElement.scrollTop = 0;
        }
    }

    if (newComment) {
        commentsElement.scrollTop = commentsElement.scrollHeight;
    }
    else {
        if (commentsElement.children.length == comments.length) {
            commentsElement.scrollTop = commentsElement.scrollHeight;
        }
        else {
            commentsElement.scrollTop = 0;
        }
    }
}

function getComments(newerComments = true) {
    const getCommentRequest = new XMLHttpRequest();

    getCommentRequest.onload = function() {
        var responseObject = JSON.parse(getCommentRequest.response);   
        var status = responseObject["STATUS"];

        if (status != "OK") {
            alert(statusMap.get(status));
            return;
        }

        parseReceivedComments(responseObject);
    }

    getCommentRequest.onerror = function() {
        alert(statusMap.get("ERROR"));
    }
    
    var datetime = null;
    if (commentsElement.children.length > 0) {
        if (newerComments) {
            datetime = commentsElement.children[commentsElement.children.length - 1].getAttribute("value");
        }
        else {
            datetime = commentsElement.children[0].getAttribute("value");
        }
    }

    getCommentRequest.open('POST', '/comment', true);
    getCommentRequest.setRequestHeader('Content-Type', 'application/json');

    var output = {};
    output["newerComments"] = newerComments;
    output["datetime"] = datetime;

    getCommentRequest.send(JSON.stringify(output));
}

function postNewComment(comment) {
    if (comment.length < 4) {
        alert(statusMap.get("SHORT_MESSAGE"));
        return;
    }

    const postNewCommentRequest = new XMLHttpRequest();

    commentField.disabled = true;
    postCommentButton.disabled = true;

    postNewCommentRequest.onload = function() {
        var responseObject = JSON.parse(postNewCommentRequest.response);
        var status = responseObject["STATUS"];

        commentField.disabled = false;
        postCommentButton.disabled = false;

        if (status != "OK") {
            alert(statusMap.get(status));
            return;
        }

        commentField.value = "";            

        parseReceivedComments(responseObject);
    }

    postNewCommentRequest.onerror = function() {
        alert(statusMap.get("ERROR"));
        postCommentButton.disabled = false;
        commentField.disabled = false
    }

    var datetime = null;

    if (commentsElement.children.length > 0) {
        datetime = commentsElement.children[commentsElement.children.length - 1].getAttribute("value");
    }

    postNewCommentRequest.open('POST', '/comment', true);
    postNewCommentRequest.setRequestHeader('Content-Type', 'application/json');

    var output = {};
    output["datetime"] = datetime
    output["comment"] = comment;
    output["newerComments"] = true

    postNewCommentRequest.send(JSON.stringify(output));
} 

window.onload = function() {
    loadOldCommentsButton.onclick = function() {
        getComments(false);
    }

    refreshCommentsButton.onclick = function() {
        getComments(true);
    }

    postCommentButton.onclick = function() {
        postNewComment(commentField.value);
    }

    getComments(false);
    commentsElement.scrollTop = commentsElement.scrollHeight;
}    
</script>