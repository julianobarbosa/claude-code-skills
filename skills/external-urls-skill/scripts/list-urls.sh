#!/bin/bash
# list-urls.sh - List URLs by environment or category
# Usage: ./list-urls.sh [filter] [--format=table|json|plain]
#
# Examples:
#   ./list-urls.sh                      # List all URLs
#   ./list-urls.sh hub                  # List hub environment
#   ./list-urls.sh dev                  # List development environment
#   ./list-urls.sh prd                  # List production environment
#   ./list-urls.sh apps                 # List application URLs
#   ./list-urls.sh clusters             # List cluster API endpoints
#   ./list-urls.sh repos                # List repository URLs
#   ./list-urls.sh helm                 # List Helm repository URLs
#   ./list-urls.sh --format=json        # Output as JSON

set -euo pipefail

# Configuration
FORMAT="table"
FILTER="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --format=*)
            FORMAT="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [filter] [--format=table|json|plain]"
            echo ""
            echo "Filters:"
            echo "  all       All URLs (default)"
            echo "  hub       Hub environment applications"
            echo "  dev       Development environment applications"
            echo "  prd       Production environment applications"
            echo "  apps      All application URLs"
            echo "  clusters  Cluster API endpoints"
            echo "  repos     Git repository URLs"
            echo "  helm      Helm repository URLs"
            echo ""
            echo "Formats:"
            echo "  table     Formatted table (default)"
            echo "  json      JSON output"
            echo "  plain     Plain URLs only"
            exit 0
            ;;
        hub|dev|prd|all|apps|clusters|repos|helm)
            FILTER="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Application URLs by environment
print_hub_apps() {
    echo "ArgoCD|https://argocd.cafehyna.com.br|Hub|GitOps UI & API"
    echo "Sentry Hub|https://sentry-hub.cafehyna.hypera.com.br|Hub|Error tracking"
    echo "SonarQube Hub|https://sonarqube-hub.cafehyna.com.br|Hub|Code quality"
    echo "phpMyAdmin Hub|https://dba.cafehyna.com.br|Hub|MySQL admin"
    echo "Adminer Hub|https://dba2.cafehyna.com.br|Hub|Multi-DB admin"
    echo "Mimir Hub|https://mimir-hub.cafehyna.com.br|Hub|Metrics storage"
}

print_dev_apps() {
    echo "Sentry Dev|https://sentry.adocyl.com.br|Development|Error tracking"
    echo "SonarQube Dev|https://sonarqube.hypera.com.br|Development|Code quality"
    echo "Grafana OnCall|https://oncall-dev.cafehyna.com|Development|On-call management"
    echo "phpMyAdmin Dev|https://dev-dba.cafehyna.com.br|Development|MySQL admin"
    echo "RabbitMQ|https://rabbitmq-painelclientes-dev.cafehyna.com.br|PainelClientes Dev|Message queue"
}

print_prd_apps() {
    echo "Sentry Prd|https://sentry.cafehyna.hypera.com.br|Production|Error tracking"
}

print_clusters() {
    echo "cafehyna-hub|https://aks-cafehyna-default-b2ie56p8.5bbf1042-d320-432c-bd11-cea99f009c29.privatelink.eastus.azmk8s.io:443|East US|Standard"
    echo "cafehyna-dev|https://aks-cafehyna-dev-hlg-q3oga63c.30041054-9b14-4852-9bd5-114d2fac4590.privatelink.eastus.azmk8s.io:443|East US|Spot"
    echo "cafehyna-prd|https://aks-cafehyna-prd-hsr83z2k.c7d864af-cbd7-481b-866b-8559e0d1c1ea.privatelink.eastus.azmk8s.io:443|East US|Standard"
    echo "painelclientes-dev|https://akspainelclientedev-dns-vjs3nd48.hcp.eastus2.azmk8s.io:443|East US 2|Standard"
    echo "painelclientes-prd|https://akspainelclientesprd-dns-kezy4skd.hcp.eastus2.azmk8s.io:443|East US 2|Standard"
    echo "loyalty-dev|https://loyaltyaks-qas-dns-d330cafe.hcp.eastus.azmk8s.io:443|East US|Spot"
}

print_repos() {
    echo "infra-team|https://hypera@dev.azure.com/hypera/Cafehyna%20-%20Desenvolvimento%20Web/_git/infra-team|Infrastructure configs"
    echo "argo-cd-helm-values|https://hypera@dev.azure.com/hypera/Cafehyna%20-%20Desenvolvimento%20Web/_git/argo-cd-helm-values|Helm values"
    echo "kubernetes-configuration|https://hypera@dev.azure.com/hypera/Cafehyna%20-%20Desenvolvimento%20Web/_git/kubernetes-configuration|K8s configs"
}

print_helm() {
    echo "ingress-nginx|https://kubernetes.github.io/ingress-nginx|ingress-nginx"
    echo "jetstack|https://charts.jetstack.io|cert-manager"
    echo "bitnami|https://charts.bitnami.com/bitnami|external-dns, phpmyadmin, rabbitmq"
    echo "prometheus-community|https://prometheus-community.github.io/helm-charts|kube-prometheus-stack"
    echo "robusta|https://robusta-charts.storage.googleapis.com|robusta"
    echo "cetic|https://cetic.github.io/helm-charts|adminer"
    echo "defectdojo|https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/helm-charts|defectdojo"
}

# Output functions
output_table() {
    local title="$1"
    local headers="$2"
    shift 2

    echo ""
    echo "=== $title ==="
    echo ""

    # Print header
    echo "$headers" | awk -F'|' '{printf "%-25s %-70s %s\n", $1, $2, $3}'
    echo "--------------------------------------------------------------------------------"

    # Print data
    while IFS='|' read -r col1 col2 col3 col4; do
        if [[ -n "$col4" ]]; then
            printf "%-25s %-70s %-15s %s\n" "$col1" "$col2" "$col3" "$col4"
        else
            printf "%-25s %-70s %s\n" "$col1" "$col2" "$col3"
        fi
    done
}

output_json() {
    local category="$1"
    shift

    echo "  \"$category\": ["
    local first=true
    while IFS='|' read -r col1 col2 col3 col4; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi
        if [[ -n "$col4" ]]; then
            printf "    {\"name\": \"%s\", \"url\": \"%s\", \"env\": \"%s\", \"purpose\": \"%s\"}" "$col1" "$col2" "$col3" "$col4"
        else
            printf "    {\"name\": \"%s\", \"url\": \"%s\", \"info\": \"%s\"}" "$col1" "$col2" "$col3"
        fi
    done
    echo ""
    echo "  ]"
}

output_plain() {
    while IFS='|' read -r col1 col2 col3 col4; do
        echo "$col2"
    done
}

# Main execution
case $FORMAT in
    json)
        echo "{"
        case $FILTER in
            hub)
                print_hub_apps | output_json "hub_applications"
                ;;
            dev)
                print_dev_apps | output_json "dev_applications"
                ;;
            prd)
                print_prd_apps | output_json "prd_applications"
                ;;
            apps)
                print_hub_apps | output_json "hub_applications"
                echo ","
                print_dev_apps | output_json "dev_applications"
                echo ","
                print_prd_apps | output_json "prd_applications"
                ;;
            clusters)
                print_clusters | output_json "clusters"
                ;;
            repos)
                print_repos | output_json "git_repositories"
                ;;
            helm)
                print_helm | output_json "helm_repositories"
                ;;
            all)
                print_hub_apps | output_json "hub_applications"
                echo ","
                print_dev_apps | output_json "dev_applications"
                echo ","
                print_prd_apps | output_json "prd_applications"
                echo ","
                print_clusters | output_json "clusters"
                echo ","
                print_repos | output_json "git_repositories"
                echo ","
                print_helm | output_json "helm_repositories"
                ;;
        esac
        echo "}"
        ;;
    plain)
        case $FILTER in
            hub) print_hub_apps | output_plain ;;
            dev) print_dev_apps | output_plain ;;
            prd) print_prd_apps | output_plain ;;
            apps)
                print_hub_apps | output_plain
                print_dev_apps | output_plain
                print_prd_apps | output_plain
                ;;
            clusters) print_clusters | output_plain ;;
            repos) print_repos | output_plain ;;
            helm) print_helm | output_plain ;;
            all)
                print_hub_apps | output_plain
                print_dev_apps | output_plain
                print_prd_apps | output_plain
                print_clusters | output_plain
                print_repos | output_plain
                print_helm | output_plain
                ;;
        esac
        ;;
    table|*)
        echo "Hypera Infrastructure URLs"
        echo "=========================="

        case $FILTER in
            hub)
                print_hub_apps | output_table "Hub Applications" "Name|URL|Environment|Purpose"
                ;;
            dev)
                print_dev_apps | output_table "Development Applications" "Name|URL|Environment|Purpose"
                ;;
            prd)
                print_prd_apps | output_table "Production Applications" "Name|URL|Environment|Purpose"
                ;;
            apps)
                print_hub_apps | output_table "Hub Applications" "Name|URL|Environment|Purpose"
                print_dev_apps | output_table "Development Applications" "Name|URL|Environment|Purpose"
                print_prd_apps | output_table "Production Applications" "Name|URL|Environment|Purpose"
                ;;
            clusters)
                print_clusters | output_table "Cluster API Endpoints" "Cluster|API Server|Region|Node Type"
                ;;
            repos)
                print_repos | output_table "Git Repositories" "Name|URL|Purpose"
                ;;
            helm)
                print_helm | output_table "Helm Repositories" "Name|URL|Charts"
                ;;
            all)
                print_hub_apps | output_table "Hub Applications" "Name|URL|Environment|Purpose"
                print_dev_apps | output_table "Development Applications" "Name|URL|Environment|Purpose"
                print_prd_apps | output_table "Production Applications" "Name|URL|Environment|Purpose"
                print_clusters | output_table "Cluster API Endpoints" "Cluster|API Server|Region|Node Type"
                print_repos | output_table "Git Repositories" "Name|URL|Purpose"
                print_helm | output_table "Helm Repositories" "Name|URL|Charts"
                ;;
        esac
        echo ""
        ;;
esac
