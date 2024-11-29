#!/bin/bash

# Jenkins admin password from secret
echo "Jenkins Admin Password:"
kubectl get secret jenkins -n jenkins -o jsonpath='{.data.jenkins-admin-password}' | base64 -d

# Argocd admin password from secret
echo -e "\nArgoCD Admin Password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo -e "\n"