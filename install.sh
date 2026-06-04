#!/bin/bash

echo "I: $instance_directory"

if [ -z "$instance_directory" ]; then
	echo -n "Enter the instance directory path: "
	read -r instance_directory
fi

if [ -z "$instance_directory" ]; then
    echo "Instance directory is not specified!"
    exit 1
fi

if [[ "$instance_directory" =~ [\*\[\]\?[:cntrl:]] ]]; then
    echo "Error: Path contains invalid or dangerous characters."
    exit 1
fi

if ! mkdir -p "$instance_directory" 2>/dev/null; then
    echo "Error: '$instance_directory' is not a valid or writable path."
    exit 1
fi

export instance_directory

config_file="$instance_directory/configuration.json"

if [ ! -f "$config_file" ]; then
    cp ./BettingServer/app/assets/configuration.json "$config_file"
    echo "Please set the proper parameters in the $config_file file"
    exit 1
fi

echo "Select configuration mode:"
echo "1) Standard"
echo "2) Precompiled"
echo "3) Low-memory"
echo -n "Enter choice [1-3]: "
read -r mode_choice

export client_docker_file="Dockerfile-builder"
export BUILD_ENV="standard"
export MEM_LIMIT="2048M"
export CPU_LIMIT="1"

case "$mode_choice" in
    1)
        configuration="standard"
        echo "Standard mode activated."
        ;;
    2)
        configuration="precompiled"
        export client_docker_file="Dockerfile-precompiled"        
		
		if [ -z "$PRECOMPILED_DIR" ]; then
            echo -n "Enter the path to the precompiled client app: "
            read -r PRECOMPILED_DIR
        fi
        export PRECOMPILED_DIR
        
        if [ -z "$PRECOMPILED_DIR" ]; then
            echo "Error: Precompiled app directory not specified!"
            exit 1
        fi

        if [[ "$PRECOMPILED_DIR" =~ [\*\[\]\?[:cntrl:]] ]]; then
            echo "Error: Path contains invalid or dangerous characters."
            exit 1
        fi
        
        if [ -d "$PRECOMPILED_DIR" ]; then
            echo "Precompiled assets found."
        else
            echo "Error: Precompiled folder missing at $PRECOMPILED_DIR"
            exit 1
        fi
        ;;
    3)
        configuration="low-mem"
        export BUILD_ENV="low-mem"
        export MEM_LIMIT="768M"
        export CPU_LIMIT="0.80"
        echo "Low-resource mode activated for Droplet."    
        ;;
    *)
        echo "Invalid choice! Exiting"
        exit 1
        ;;
esac

echo "Setting up live deployment..."

site_address=$(jq -r '.BACKEND_ADDRESS' "$config_file")
cert_email=$(jq -r '.CERT_EMAIL' "$config_file")
certificate_directory="/etc/letsencrypt/live/$site_address"

if [ "$site_address" = "betting.app" ] || [ "$cert_email" = "email@betting.app" ]; then
	echo "The configuration file is not configured properly! (site address or certification email is invalid)"
	exit 1
fi

echo "Site address: $site_address"
echo "Cert. expiration notification email address: $cert_email"
echo "Certificate directory: $certificate_directory"

export site_address
export cert_email
export certificate_directory

client_config='{ "endpoint": "https://${site_address}/api/" }'
echo $client_config | envsubst '$site_address' > ./config.json

en_client_config='{ "endpoint": "https://en.${site_address}/api/" }'
echo $en_client_config | envsubst '$site_address' > ./en-config.json

cat ./nginx.conf.template | envsubst '$site_address $certificate_directory' > ./nginx.conf

echo "Nginx config file created."

# Live deployment options prompt
echo "Select launch mode:"
echo "1) Standard Compose (Just bring up services)"
echo "2) Rebuild betting-server"
echo "3) Rebuild betting-client"
echo "4) Down / Delete all containers for this deployment"
echo -n "Enter choice [1-4]: "
read -r launch_choice

case "$launch_choice" in
	1)
		echo "Running standard compose..."
		docker compose up -d
		;;
	2)
		echo "Rebuilding betting-server..."
		docker compose up -d --build --force-recreate --no-deps betting-server
		;;
	3)
		echo "Rebuilding betting-client..."
		docker compose up -d --build --force-recreate --no-deps betting-client
		;;
	4)
		echo "Stopping and destroying all containers/networks for this stack..."
		docker compose down
		;;
	*)
        echo "Invalid choice! Exiting"
		;;
esac

echo "Composing finished."
