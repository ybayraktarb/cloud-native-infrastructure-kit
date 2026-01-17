# =============================================================================
# Cloudflare DNS Configuration Guide
# =============================================================================
# This document provides instructions for configuring Cloudflare DNS records
# to point to your EKS cluster's Network Load Balancer.
# =============================================================================

## Prerequisites

1. Cloudflare account with your domain added
2. EKS cluster running with Nginx Ingress Controller deployed
3. AWS NLB created by the Ingress Controller

---

## Step 1: Get the NLB DNS Name

After deploying the Nginx Ingress Controller, retrieve the NLB DNS name:

```bash
# Get the external hostname of the ingress controller
kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Example output:
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-1234567890.us-east-1.elb.amazonaws.com
```

---

## Step 2: Configure Cloudflare DNS Records

### API Subdomain (CNAME Record)

| Field | Value |
|-------|-------|
| **Type** | CNAME |
| **Name** | api |
| **Target** | `<NLB-DNS-NAME>` (from Step 1) |
| **Proxy status** | Proxied (orange cloud) |
| **TTL** | Auto |

### Cloudflare Dashboard Steps:

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select your domain
3. Go to **DNS** → **Records**
4. Click **Add record**
5. Configure as shown above
6. Click **Save**

---

## Step 3: Configure Cloudflare SSL/TLS

### SSL/TLS Mode

Navigate to **SSL/TLS** → **Overview** and set:

| Setting | Recommended Value |
|---------|------------------|
| **Encryption mode** | Full (strict) |

### Edge Certificates

Navigate to **SSL/TLS** → **Edge Certificates**:

| Setting | Value |
|---------|-------|
| **Always Use HTTPS** | On |
| **Automatic HTTPS Rewrites** | On |
| **Minimum TLS Version** | TLS 1.2 |

---

## Step 4: Configure Cloudflare Security

### Security Settings

Navigate to **Security** → **Settings**:

| Setting | Recommended Value |
|---------|------------------|
| **Security Level** | Medium |
| **Challenge Passage** | 30 minutes |
| **Browser Integrity Check** | On |

### WAF Rules (Optional)

Navigate to **Security** → **WAF**:

1. Enable Cloudflare Managed Ruleset
2. Enable OWASP Core Ruleset
3. Configure custom rules as needed

---

## Step 5: Origin Certificate (Alternative to Let's Encrypt)

For Full (strict) SSL mode, you need a valid certificate on the origin.

### Option A: Cloudflare Origin Certificate

1. Navigate to **SSL/TLS** → **Origin Server**
2. Click **Create Certificate**
3. Configure:
   - Hostnames: `*.cloud-native-ops.example.com, cloud-native-ops.example.com`
   - Certificate Validity: 15 years
4. Download the certificate and private key
5. Create Kubernetes secret:

```bash
kubectl create secret tls cloud-native-ops-tls \
  --cert=origin-cert.pem \
  --key=origin-key.pem \
  -n cloud-native-ops
```

### Option B: Let's Encrypt with cert-manager

Deploy cert-manager and create a ClusterIssuer:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

---

## Terraform Cloudflare Module (Optional)

If you prefer Infrastructure as Code for Cloudflare:

```hcl
# terraform/modules/cloudflare/main.tf

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "nlb_dns_name" {
  description = "AWS NLB DNS name"
  type        = string
}

variable "subdomain" {
  description = "Subdomain for the API"
  type        = string
  default     = "api"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_record" "api" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  value   = var.nlb_dns_name
  type    = "CNAME"
  proxied = true
  ttl     = 1  # Auto when proxied
}

output "fqdn" {
  value = cloudflare_record.api.hostname
}
```

---

## Verification

After configuration, verify the setup:

```bash
# DNS Resolution
dig api.cloud-native-ops.example.com

# HTTPS connectivity
curl -v https://api.cloud-native-ops.example.com/health

# Check SSL certificate
openssl s_client -connect api.cloud-native-ops.example.com:443 -servername api.cloud-native-ops.example.com
```

---

## Traffic Flow Diagram

```
User Request
     │
     ▼
┌─────────────────────┐
│     Cloudflare      │  ← SSL Termination (Edge)
│   (DNS + CDN + WAF) │  ← DDoS Protection
└──────────┬──────────┘  ← Geographic Routing
           │
           │ HTTPS (re-encrypted)
           ▼
┌─────────────────────┐
│      AWS NLB        │  ← Layer 4 Load Balancing
│  (Network LB)       │  ← Health Checks
└──────────┬──────────┘
           │
           │ TCP/HTTP
           ▼
┌─────────────────────┐
│   Nginx Ingress     │  ← TLS Termination (Origin)
│   Controller        │  ← Routing Rules
└──────────┬──────────┘  ← Rate Limiting
           │
           │ HTTP
           ▼
┌─────────────────────┐
│   Kubernetes Pod    │  ← Application
│   (FastAPI)         │
└─────────────────────┘
```
