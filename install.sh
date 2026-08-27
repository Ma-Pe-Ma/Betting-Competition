#!/bin/bash

# Validates path inputs for empty strings, dangerous characters, and creates/checks directories
validate_path() {
    local path_type="$1"
    local path_val="$2"
    local check_exists="$3"

    if [ -z "$path_val" ]; then
        echo "Error: $path_type is not specified!"
        exit 1
    fi

    if [[ "$path_val" =~ [\*\[\]\?[:cntrl:]] ]]; then
        echo "Error: $path_type contains invalid or dangerous characters."
        exit 1
    fi

    if [ "$check_exists" = "true" ]; then
        if [ ! -d "$path_val" ]; then
            echo "Error: $path_type folder missing at $path_val"
            exit 1
        fi
    else
        if ! mkdir -p "$path_val" 2>/dev/null; then
            echo "Error: '$path_val' is not a valid or writable path."
            exit 1
        fi
    fi
}

# Set default values
export client_docker_file="Dockerfile-builder"
export BUILD_ENV="standard"
export MEM_LIMIT="2048M"
export CPU_LIMIT="1"

# Prompt and set the configuration mode (Standard / Precompiled / Low-memory)
configure_mode() {
    # Only prompt if client_mode isn't already set
    if [ -z "$client_mode" ]; then
        echo "Select configuration mode:"
        echo "1) Standard"
        echo "2) Precompiled"
        echo "3) Low-memory"
        echo -n "Enter choice [1-3]: "
        read -r client_mode
    fi

    case "$client_mode" in
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
            
            validate_path "Precompiled app directory" "$PRECOMPILED_DIR" "true"
            export PRECOMPILED_DIR
            echo "Precompiled assets found."
            ;;
        3)
            configuration="low-mem"
            export BUILD_ENV="low-mem"
            export MEM_LIMIT="768M"
            export CPU_LIMIT="0.80"
            echo "Low-resource mode activated for Droplet."    
            ;;
        *)
            echo "Invalid choice for configuration mode ($client_mode)! Exiting"
            exit 1
            ;;
    esac
}

# Instance Directory Setup
if [ -z "$instance_directory" ]; then
    echo -n "Enter the instance directory path: "
    read -r instance_directory
fi

validate_path "Instance directory" "$instance_directory" "false"
export instance_directory

config_file="$instance_directory/configuration.json"

if [ ! -f "$config_file" ]; then
    cp ./BettingServer/app/assets/configuration.json "$config_file"
    echo "Please set the proper parameters in the $config_file file"
    exit 1
fi

# Extract configuration values
echo "Setting up deployment..."

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

# Process Configuration Templates
client_config='{ "endpoint": "https://${site_address}/api/" }'
printf "%s" "$client_config" | envsubst '$site_address' > ./config.json

en_client_config='{ "endpoint": "https://en.${site_address}/api/" }'
printf "%s" "$en_client_config" | envsubst '$site_address' > ./en-config.json

envsubst '${site_address} ${certificate_directory}' < ./nginx.conf.template > ./nginx.conf
echo "Nginx config file created."

# Live deployment options prompt
if [ -z "$launch_mode" ]; then
    echo "Select launch mode:"
    echo "1) Standard Compose (Just bring up services)"
    echo "2) Rebuild betting-server"
    echo "3) Rebuild betting-client"
    echo "4) Down / Delete all containers for this deployment"
    echo -n "Enter choice [1-4]: "
    read -r launch_mode
fi

case "$launch_mode" in
    1)
        configure_mode
        echo "Running standard compose..."
        docker compose $standard_modifier up -d
        ;;
    2)
        echo "Rebuilding betting-server..."
        docker compose up -d --build --force-recreate --no-deps betting-server
        ;;
    3)
        configure_mode
        echo "Rebuilding betting-client..."
        docker compose up -d --build --force-recreate --no-deps betting-client
        ;;
    4)
        echo "Stopping and destroying all containers/networks for this stack..."
        docker compose down
        ;;
    *)
        echo "Invalid choice for launch mode ($launch_mode)! Exiting"
        exit 1
        ;;
esac

echo "Composing finished."