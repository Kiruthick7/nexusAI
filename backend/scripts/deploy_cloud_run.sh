#!/bin/bash
# ==============================================================================
# Google Cloud Run Deployment Script - Nexus AI Operations Platform
# ==============================================================================
# Resolves Google Cloud parameters, builds production images via gcloud,
# pushes to Artifact Registry, and deploys with appropriate runtime variables.
# ==============================================================================

set -euo pipefail

# ANSI color codes for high-fidelity console feedback
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}======================================================================"
echo -e "          NEXUS AI OPERATIONS PLATFORM - CLOUD RUN DEPLOY"
echo -e "======================================================================${NC}"

# 1. Resolve configuration parameters
GCP_PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "nexus-ai-orchestration")
REGION=$(gcloud config get-value run/region 2>/dev/null || echo "asia-south1")
SERVICE_NAME="nexus-backend"
IMAGE_TAG="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest"

echo -e "${YELLOW}Deploying with the following parameters:${NC}"
echo -e "  - ${BOLD}GCP Project ID:${NC} ${GCP_PROJECT_ID}"
echo -e "  - ${BOLD}Region:${NC}         ${REGION}"
echo -e "  - ${BOLD}Service Name:${NC}   ${SERVICE_NAME}"
echo -e "  - ${BOLD}Image Tag:${NC}      ${IMAGE_TAG}"
echo ""

# 2. Build and push image via Cloud Build
echo -e "\n${CYAN}Step 1: Building production container using Google Cloud Build...${NC}"
gcloud builds submit --tag "${IMAGE_TAG}" .

# Resolve .env file location and extract active environment variables
SCRIPT_DIR="$(dirname "$0")"
if [ -f "${SCRIPT_DIR}/../.env" ]; then
  ENV_FILE="${SCRIPT_DIR}/../.env"
elif [ -f "./.env" ]; then
  ENV_FILE="./.env"
else
  echo -e "${RED}Error: .env file not found!${NC}"
  exit 1
fi

# Parse .env to extract valid environment variables, excluding empty lines, comments, and the reserved PORT variable
ENV_VARS_LIST=$(grep -v '^#' "$ENV_FILE" | grep -v '^PORT=' | grep -v '^[[:space:]]*$' | tr '\n' ',' | sed 's/,$//')

# 3. Deploy to Cloud Run
echo -e "\n${CYAN}Step 2: Deploying container image to Cloud Run...${NC}"
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_TAG}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars="${ENV_VARS_LIST}"

echo -e "\n${GREEN}${BOLD}✔ Deployment complete!${NC}"
echo -e "Your service has been deployed successfully."
