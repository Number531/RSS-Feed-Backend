#!/bin/bash
echo "🔐 Generating Secure Secrets for Staging"
echo "========================================="
echo ""
echo "SECRET_KEY (for JWT signing):"
openssl rand -hex 32
echo ""
echo "ADMIN_PASSWORD (secure random password):"
openssl rand -base64 24 | tr -d '/+=' | head -c 32
echo ""
echo "Database Password (if needed):"
openssl rand -base64 16 | tr -d '/+='
echo ""
echo "⚠️  Save these securely! Never commit to git."
echo "========================================="
