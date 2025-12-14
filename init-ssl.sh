#!/bin/bash
# SSL Certificate Setup Script for smeinterviews.organicengineer.com
# Run this ONCE on the server to get initial Let's Encrypt certificates

DOMAIN="smeinterviews.organicengineer.com"
EMAIL="admin@organicengineer.com"  # Change this to your email
APP_DIR="/opt/sme-interview"

cd $APP_DIR

# Create certbot directories
mkdir -p certbot/conf certbot/www

# Create temporary nginx config for certificate request (HTTP only)
cat > nginx-init.conf << 'EOF'
events {
    worker_connections 1024;
}
http {
    server {
        listen 80;
        server_name smeinterviews.organicengineer.com;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 200 'Setting up SSL...';
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Start temporary nginx for ACME challenge
echo "Starting temporary nginx for certificate request..."
docker run -d --name nginx-init \
    -p 80:80 \
    -v $APP_DIR/nginx-init.conf:/etc/nginx/nginx.conf:ro \
    -v $APP_DIR/certbot/www:/var/www/certbot \
    nginx:alpine

# Request certificate
echo "Requesting Let's Encrypt certificate..."
docker run --rm \
    -v $APP_DIR/certbot/conf:/etc/letsencrypt \
    -v $APP_DIR/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Stop temporary nginx
echo "Stopping temporary nginx..."
docker stop nginx-init
docker rm nginx-init
rm nginx-init.conf

# Check if certificate was created
if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo ""
    echo "============================================"
    echo "  SSL Certificate obtained successfully!"
    echo "============================================"
    echo ""
    echo "Now run: docker compose up -d"
    echo "Site will be available at: https://$DOMAIN"
else
    echo ""
    echo "ERROR: Certificate not created."
    echo "Make sure DNS for $DOMAIN points to this server."
fi
