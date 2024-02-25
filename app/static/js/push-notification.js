var registration = null

const applicationServerPublicKey = document.currentScript.getAttribute('data-public-key')

function urlB64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
}

async function updateSubscriptionOnServer(subscription) {
   const response = await fetch('/notification/subscribe', {
        method: "POST", 
        mode: "cors", 
        cache: "no-cache", 
        credentials: "same-origin", 
        headers: {
            "Content-Type": "application/json"
        },
        redirect: "follow", 
        referrerPolicy: "no-referrer",
        body : JSON.stringify(subscription.toJSON())
    });

    if (response.status != 200) {
        if (registration != null) {
            registration.unregister().then((success) => {
                console.log('Unregistering...' + success);                    
            });
        }
    }
}

if ('serviceWorker' in navigator && 'PushManager' in window) {
    navigator.serviceWorker.register('sw.js', {scope : "/"})
    .then((newRegistration) => {
        registration = newRegistration;
        
        registration.pushManager.getSubscription()
        .then((subscription) => {
            var isSubscribed = !(subscription === null);
           
            if (!isSubscribed) {
                const applicationServerKey = urlB64ToUint8Array(applicationServerPublicKey);
                registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey
                })
                .then((subscription) => {
                    updateSubscriptionOnServer(subscription);
                })
                .catch((err) => {
                    //console.log('Failed to subscribe the user: ', err);
                })
                .finally((e) => {
                    
                });
            }
        });
    })
    .catch((error) => {
        console.error('Service Worker Error', error);
    });
} else {
    console.warn('Push messaging is not supported');
}