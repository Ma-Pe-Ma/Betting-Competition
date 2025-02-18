#!/bin/sh

if [ ! -e ./deployment/configuration.json ];
then
    cp ./app/assets/configuration.json ./deployment/
    echo "Please set the proper parameters in the ./deployment/configuration.json file"
else
    site_address=$(python3 -c "import json; print(json.load(open('./deployment/configuration.json'))['SITE_ADDRESS'])")
    cert_email=$(python3 -c "import json; print(json.load(open('./deployment/configuration.json'))['CERT_EMAIL'])")

    echo "Site address: $site_address"
    echo "Cert. expiration notification email address: $cert_email"

    if [ "$site_address" = "betting.app" ] || [ "$cert_email" = "email@betting.app" ];
    then
        echo "The configuration file is not configured properly! (site address or certification email is invalid)"
    else
        export site_address
        export cert_email
        cat ./deployment/nginx.conf.template | envsubst '$site_address' > ./deployment/nginx.conf

        echo "Nginx config file created."
        echo "Starting composing project..."

        docker compose up -d

        echo "Composing finished."
    fi
fi
