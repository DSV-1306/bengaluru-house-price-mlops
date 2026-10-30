variable "subscription_id" {
  description = "Azure subscription ID (from: az account show --query id -o tsv)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "centralindia"
}

variable "prefix" {
  description = "Short lowercase alphanumeric prefix for resource names"
  type        = string
  default     = "hpmlops"

  validation {
    condition     = can(regex("^[a-z0-9]{3,12}$", var.prefix))
    error_message = "prefix must be 3-12 lowercase letters/digits (ACR names allow no dashes)."
  }
}

variable "node_vm_size" {
  description = "AKS node size (smallest that AKS allows: 2 vCPU / 4 GB)"
  type        = string
  default     = "Standard_B2s"
}

variable "node_count" {
  description = "Number of AKS nodes"
  type        = number
  default     = 1
}

variable "github_repo" {
  description = "GitHub repo as owner/name, used for the CD OIDC federated credential. Empty = skip."
  type        = string
  default     = ""
}

variable "tags" {
  type = map(string)
  default = {
    project = "bengaluru-house-price-mlops"
    owner   = "student"
  }
}
