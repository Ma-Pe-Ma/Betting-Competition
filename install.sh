#!/bin/sh

if [ -n "$LOCAL_TEST" ]; then
    echo "Setting up local deployment..."
    site_address="localhost"	
    #cert_email="test@email.com"
    certificate_directory="/BettingApp/app/"
    
    if [ ! -e ./app/privkey.pem ] || [ ! -e ./app/fullchain.pem ]; then
        openssl req -x509 -nodes -newkey rsa:2048 -keyout "./app/privkey.pem" -out "./app/fullchain.pem" -days 4096 -subj "/CN=localhost"
    fi
else
    echo "Setting up live deployment..."
    
    if [ ! -e ./deployment/configuration.json ]; then
        cp ./app/assets/configuration.json ./deployment/
        echo "Please set the proper parameters in the ./deployment/configuration.json file"
        exit
    fi
    
    site_address=$(jq -r '.SITE_ADDRESS' ./deployment/configuration.json)
    cert_email=$(jq -r '.CERT_EMAIL' ./deployment/configuration.json)
    certificate_directory="/etc/letsencrypt/live/$site_address"
	
    if [ "$site_address" = "betting.app" ] || [ "$cert_email" = "email@betting.app" ]; then
        echo "The configuration file is not configured properly! (site address or certification email is invalid)"
        exit
    fi
fi

echo "Site address: $site_address"
echo "Cert. expiration notification email address: $cert_email"
echo "Certificate directory: $certificate_directory"

export site_address
export cert_email
export certificate_directory

cat ./deployment/nginx.conf.template | envsubst '$site_address $certificate_directory' > ./deployment/nginx.conf

echo "Nginx config file created."
echo "Starting composing project..."

if [ -n "$LOCAL_TEST" ]; then
    docker compose up -d
else
    docker compose -f ./docker-compose.yml -f ./deployment/certbot-override.yml up -d
fi

echo "Composing finished."
