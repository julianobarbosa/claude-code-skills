#!/bin/bash
# Verify DNS configuration for GitHub Pages custom domain
# Usage: ./verify-dns.sh example.com

set -euo pipefail

DOMAIN="${1:-}"

if [[ -z "$DOMAIN" ]]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 example.com"
    exit 1
fi

# GitHub Pages IP addresses
GITHUB_IPS=(
    "185.199.108.153"
    "185.199.109.153"
    "185.199.110.153"
    "185.199.111.153"
)

GITHUB_IPV6=(
    "2606:50c0:8000::153"
    "2606:50c0:8001::153"
    "2606:50c0:8002::153"
    "2606:50c0:8003::153"
)

echo "========================================="
echo "GitHub Pages DNS Verification"
echo "Domain: $DOMAIN"
echo "========================================="
echo ""

# Check if it's an apex domain or subdomain
if [[ "$DOMAIN" == www.* ]]; then
    IS_SUBDOMAIN=true
    RECORD_TYPE="CNAME"
else
    IS_SUBDOMAIN=false
    RECORD_TYPE="A"
fi

# Function to check A records
check_a_records() {
    local domain=$1
    echo "Checking A records for $domain..."
    echo ""

    local a_records
    a_records=$(dig "$domain" +noall +answer -t A | awk '{print $5}')

    if [[ -z "$a_records" ]]; then
        echo "  ❌ No A records found"
        return 1
    fi

    local found=0
    for ip in "${GITHUB_IPS[@]}"; do
        if echo "$a_records" | grep -q "$ip"; then
            echo "  ✅ Found: $ip"
            ((found++))
        else
            echo "  ❌ Missing: $ip"
        fi
    done

    if [[ $found -eq 4 ]]; then
        echo ""
        echo "  All GitHub Pages A records configured correctly!"
        return 0
    else
        echo ""
        echo "  ⚠️  Only $found/4 GitHub Pages IPs configured"
        return 1
    fi
}

# Function to check AAAA records
check_aaaa_records() {
    local domain=$1
    echo ""
    echo "Checking AAAA records for $domain..."
    echo ""

    local aaaa_records
    aaaa_records=$(dig "$domain" +noall +answer -t AAAA | awk '{print $5}')

    if [[ -z "$aaaa_records" ]]; then
        echo "  ⚠️  No AAAA records found (IPv6 optional but recommended)"
        return 0
    fi

    local found=0
    for ip in "${GITHUB_IPV6[@]}"; do
        if echo "$aaaa_records" | grep -qi "$ip"; then
            echo "  ✅ Found: $ip"
            ((found++))
        fi
    done

    if [[ $found -eq 4 ]]; then
        echo ""
        echo "  All GitHub Pages AAAA records configured correctly!"
    else
        echo ""
        echo "  ⚠️  Only $found/4 GitHub Pages IPv6 addresses configured"
    fi
}

# Function to check CNAME records
check_cname_records() {
    local domain=$1
    echo "Checking CNAME record for $domain..."
    echo ""

    local cname
    cname=$(dig "$domain" +noall +answer -t CNAME | awk '{print $5}')

    if [[ -z "$cname" ]]; then
        echo "  ❌ No CNAME record found"
        return 1
    fi

    if [[ "$cname" == *.github.io. ]] || [[ "$cname" == *.github.io ]]; then
        echo "  ✅ CNAME points to: $cname"
        return 0
    else
        echo "  ❌ CNAME points to: $cname"
        echo "  ⚠️  Should point to <username>.github.io"
        return 1
    fi
}

# Function to check CAA records
check_caa_records() {
    local domain=$1
    echo ""
    echo "Checking CAA records for $domain..."
    echo ""

    local caa_records
    caa_records=$(dig "$domain" +noall +answer -t CAA)

    if [[ -z "$caa_records" ]]; then
        echo "  ✅ No CAA records (Let's Encrypt can issue certificates)"
        return 0
    fi

    if echo "$caa_records" | grep -qi "letsencrypt"; then
        echo "  ✅ CAA allows Let's Encrypt"
        return 0
    else
        echo "  ⚠️  CAA records exist but may not allow Let's Encrypt"
        echo "  Add: 0 issue \"letsencrypt.org\""
        return 1
    fi
}

# Main checks
if $IS_SUBDOMAIN; then
    check_cname_records "$DOMAIN"
else
    check_a_records "$DOMAIN"
    check_aaaa_records "$DOMAIN"
    check_caa_records "$DOMAIN"

    # Also check www subdomain
    echo ""
    echo "========================================="
    echo "Checking www subdomain (recommended)..."
    echo "========================================="
    echo ""
    check_cname_records "www.$DOMAIN" || echo "  Consider adding www.$DOMAIN as CNAME"
fi

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "If DNS is not propagated yet, wait up to 24-48 hours."
echo "Use https://whatsmydns.net to check global propagation."
echo ""
echo "GitHub Pages documentation:"
echo "https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site"
