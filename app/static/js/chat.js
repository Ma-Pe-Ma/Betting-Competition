var commentContainer = document.getElementById("commentContainer");
var newCommentButton = document.getElementById("newCommentButton");
var loadOldCommentsButton = document.getElementById("loadOldCommentsButton");
var loadNewCommentsButton = document.getElementById("loadNewCommentsButton");

var commentTemplate = document.getElementById("commentTemplate");

const commentModal = document.getElementById("commentModal");
var modalInstance;
var commentInputArea = document.getElementById("commentInputArea");
var commentPreviewArea = document.getElementById("commentPreviewArea");

var postCommentButton = document.getElementById("postCommentButton");
var previewCommentButton = document.getElementById("previewCommentButton");

var successAlertTemplate = document.getElementById("successalertTemplate");
var failureAlertTemplate = document.getElementById("dangeralertTemplate");

function createAlert(message, success) {
    if (!success) {
        document.body.scrollTop = document.documentElement.scrollTop = 0;
    }
    const alert = success ? successAlertTemplate.content.cloneNode(true) : failureAlertTemplate.content.cloneNode(true);
    const alertMessage = alert.getElementById("message");
    if (message != null) {
        alertMessage.innerText = message;
    }
    
    alertNode.appendChild(alert);
}

function parseReceivedComments(responseObject) {
    var comments = responseObject["comments"]
    var newComment = responseObject["newerComments"];

    if (comments.length < 8 && !newComment) {
        loadOldCommentsButton.disabled = true;
    }

    var childrenCount = commentContainer.children.length;

    for (var comment of comments) {
        const commentElement = commentTemplate.content.cloneNode(true);
        commentElement.getElementById("commentRoot").setAttribute("value", comment["datetime"]);
        commentElement.getElementById("userImage").setAttribute("src", comment['image_path'])
        commentElement.getElementById("commentHeader").innerText = comment["username"];
        commentElement.getElementById("date").innerText = comment["datetime"];
        commentElement.getElementById("content").innerHTML = marked.parse(comment["comment"]);

        if (newComment) {
            commentContainer.append(commentElement);
        }
        else {
            commentContainer.insertBefore(commentElement, commentContainer.firstChild);
        }
    }
}

function getComments(newerComments = true) {
    const request = new XMLHttpRequest();

    request.onload = function() {
        document.getElementById("newSpinner").classList.add("d-none");
        document.getElementById("oldSpinner").classList.add("d-none");

        if (request.status == 200){
            parseReceivedComments(JSON.parse(request.response));

            if (newerComments) {
                window.scrollTo(0, document.body.scrollHeight);
            }
        }

        if (request.status == 400){
            createAlert(request.response, false);
        }

        if (request.status == 500){
            var internalError = document.getElementById("internalError");
            createAlert(internalError.innerText, false);
        }
    }

    request.onerror = function() {
        var connectionError = document.getElementById("connectionError");
        createAlert(connectionError.innerText, false);
    }
    
    var datetime = null;
    if (commentContainer.children.length > 0) {
        commentID = newerComments ? commentContainer.children.length - 1 : 0;
        datetime = commentContainer.children[commentID].getAttribute("value")
    }

    var output = {
        "newerComments" : newerComments,
        "datetime" : datetime
    };

    if (newerComments) {
        document.getElementById("newSpinner").classList.remove("d-none");
    }
    else {
        document.getElementById("oldSpinner").classList.remove("d-none");
    }

    request.open('POST', '/chat', true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.send(JSON.stringify(output));
}

function postNewComment(comment) {
    const request = new XMLHttpRequest();

    request.onload = function() {
        commentInputArea.disabled = false;
        postCommentButton.disabled = false;

        if (request.status == 200){
            parseReceivedComments(JSON.parse(request.response));
            commentInputArea.value = "";
            commentPreviewArea.innerHTML = "";
            createAlert(null, true);
            modalInstance.hide();
        }

        if (request.status == 400){
            createAlert(request.response, false);
            modalInstance.hide();
        }

        if (request.status == 500){
            modalInstance.hide();
            var internalError = document.getElementById("internalError");
            createAlert(internalError.innerText, false);
        }        
    }

    request.onerror = function() {
        postCommentButton.disabled = false;
        commentInputArea.disabled = false

        var connectionError = document.getElementById("connectionError");
        createAlert(connectionError.innerText, false);

        modalInstance.hide();
    }

    var datetime = commentContainer.children.length > 0 ? commentContainer.children[0].getAttribute("value") : null;

    var output = {
        "datetime" : datetime,
        "comment" : comment,
        "newerComments" : true    
    };

    request.open('POST', '/chat', true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.send(JSON.stringify(output));
} 

commentModal.addEventListener('shown.bs.modal', (event) => {
    modalInstance = bootstrap.Modal.getInstance(commentModal);
    commentInputArea.focus();
});

window.onload = function() {
    loadOldCommentsButton.onclick = () => getComments(false);
    loadNewCommentsButton.onclick = () => getComments(true);
    
    previewCommentButton.onclick = () => {commentPreviewArea.innerHTML = marked.parse(commentInputArea.value);}
    postCommentButton.onclick = () => postNewComment(commentInputArea.value);

    getComments(false);
} 