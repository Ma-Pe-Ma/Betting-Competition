#!/bin/sh

instance_directory="$1"

if [$instance_directory = ""]; then
    echo "Instance directory argument is missing!"
    exit
fi

export instance_directory
mkdir -p $instance_directory

config_file="$instance_directory/configuration.json"

if [ ! -f $config_file ]; then
    cp ./BettingServer/app/assets/configuration.json $config_file
    echo "Please set the proper parameters in the $config_file file"
    exit
fi

if [ -n "$LOCAL_TEST" ]; then
    echo "Setting up local deployment..."
    site_address="localhost"	
    #cert_email="test@email.com"
    certificate_directory="/BettingInstance/"
    
    if [ ! -f "$instance_directory/privkey.pem" ] || [ ! -f "$instance_directory/fullchain.pem" ]; then
        openssl req -x509 -nodes -newkey rsa:2048 -keyout "$instance_directory/privkey.pem" -out "$instance_directory/fullchain.pem" -days 4096 -subj "/CN=localhost"
    fi
else
    echo "Setting up live deployment..."
    
    site_address=$(jq -r '.BACKEND_ADDRESS' $config_file)
    cert_email=$(jq -r '.CERT_EMAIL' $config_file)
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

client_config='{ "endpoint": "https://${site_address}/api/" }'
echo $client_config | envsubst '$site_address' > ./config.json

cat ./nginx.conf.template | envsubst '$site_address $certificate_directory' > ./nginx.conf

echo "Nginx config file created."
echo "Starting composing project..."

if [ -n "$LOCAL_TEST" ]; then
    docker compose up -d
else
    docker compose -f ./docker-compose.yml -f ./certbot-override.yml up -d
fi

echo "Composing finished."
