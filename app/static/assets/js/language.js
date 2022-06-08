var languageSelect = document.getElementById("langSelect");

var titleDisplay = document.getElementById("titleDisplay"); 
var langDisplay = document.getElementById("langDisplay");
var nickDisplay = document.getElementById("nickDisplay");
var emailDisplay = document.getElementById("emailDisplay");
var password1Diplay = document.getElementById("password1Diplay");
var password2Diplay = document.getElementById("password2Diplay");
var invitationDisplay = document.getElementById("invitationDisplay");
var matchReminderDisplay = document.getElementById("matchReminderDisplay");
var reminder1Display = document.getElementById("reminder1Display");
var reminder2Display = document.getElementById("reminder2Display");
var reminder3Display = document.getElementById("reminder3Display");

var standingsDisplay = document.getElementById("standingsDisplay");
var standing1Display = document.getElementById("standing1Display");
var standing2Display = document.getElementById("standing2Display");

var registerButton = document.getElementById("registerButton");
var signIn = document.getElementById("signIn");
var haveAccount = document.getElementById("haveAccount");

languageSelect.onchange = function() {
    switch(this.value) {
        case 'hu':
            titleDisplay.innerText = "Regisztráció";
        
            langDisplay.innerText = "Nyelv";
            languageSelect.options[0].innerText = "Magyar";
            languageSelect.options[1].innerText = "Angol";
            nickDisplay.innerText = "Felhasználónév/becenév";
            emailDisplay.innerText = "Email-cím";
            password1Diplay.innerText = "Jelszó";
            password2Diplay.innerText = "Jelszó újra";
            invitationDisplay.innerText = "Megívókód";
            matchReminderDisplay.innerText = "Meccsemlékeztetők emailben (a nap első meccsének kezdése előtt egy órával)";
            reminder1Display.innerText = "Azokon a meccsnapokon amelyiken van olyan meccs, amelyiknél nem lett megrakva tét";
            reminder2Display.innerText = "Minden meccsnap";
            reminder3Display.innerText = "Nem kérek emlékeztetőt";
            standingsDisplay.innerText = "Állásközlő email meccsnapok végén";
            standing1Display.innerText = "Igen";
            standing2Display.innerText = "Nem";

            registerButton.innerText = "Regisztráció";
            signIn.innerText = "Bejelentkezés";
            haveAccount.innerText = "Van már fiókod?";
        break;

        case 'en': 
            titleDisplay.innerText = "Registration";
            langDisplay.innerText = "Language";
            languageSelect.options[0].innerText = "Hungarian";
            languageSelect.options[1].innerText = "English";
            nickDisplay.innerText = "Nickname/username";
            emailDisplay.innerText = "Email-address";
            password1Diplay.innerText = "Password";
            password2Diplay.innerText = "Password again";
            invitationDisplay.innerText = "Invitaion-key";
            matchReminderDisplay.innerText = "Match reminder emails (1 hour before the starting of the first match)";
            reminder1Display.innerText = "On those days when there is a match without a bet";
            reminder2Display.innerText = "Every matchday";
            reminder3Display.innerText = "I don't want to receive reminders";
            standingsDisplay.innerText = "Standing notification email at the end of matchdays";
            standing1Display.innerText = "Yes";
            standing2Display.innerText = "No";

            registerButton.innerText = "Registration";
            signIn.innerText = "Sign-in";
            haveAccount.innerText = "Already have an account?";
        break;
    }
}