#!/bin/bash

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function for colored print
print_status() {
    echo -e "${1}${2}${NC}"
}

# Add Helm repositories
print_status "${BLUE}" "Adding Helm repositories..."
helm repo add jenkins https://charts.jenkins.io
helm repo add argo https://argoproj.github.io/argo-helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
print_status "${GREEN}" "Helm repositories added successfully!"

# Install Jenkins
print_status "${YELLOW}" "Installing Jenkins in jenkins namespace..."
kubectl create namespace jenkins
helm upgrade --install jenkins jenkins/jenkins --namespace jenkins --create-namespace
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=jenkins -n jenkins
kubectl patch svc jenkins -n jenkins -p '{"spec":{"type":"NodePort"}}'
print_status "${GREEN}" "Jenkins installation complete!"

# Install ArgoCD
print_status "${YELLOW}" "Installing ArgoCD in argocd namespace..."
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd
kubectl patch svc argocd-server -n argocd -p '{"spec":{"type":"NodePort"}}'
print_status "${GREEN}" "ArgoCD installation complete!"

# Install Prometheus and Grafana
print_status "${YELLOW}" "Installing Prometheus and Grafana in monitoring namespace..."
kubectl create namespace monitoring
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring
kubectl patch svc prometheus-grafana -n monitoring -p '{"spec":{"type":"NodePort"}}'
print_status "${GREEN}" "Prometheus and Grafana installation complete!"

print_status "${GREEN}" "🎉 All installations successful! 🚀"

# Jenkins admin password from secret
echo "Jenkins Admin Password:"
kubectl get secret jenkins -n jenkins -o jsonpath='{.data.jenkins-admin-password}' | base64 -d

# Argocd admin password from secret
echo -e "\nArgoCD Admin Password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo -e "\n"