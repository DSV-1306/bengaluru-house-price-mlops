resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.prefix}"
  location = var.location
  tags     = var.tags
}

# ---- Azure Container Registry (Basic = cheapest) ------------------------------
resource "azurerm_container_registry" "acr" {
  name                = "${var.prefix}acr${random_string.suffix.result}" # must be globally unique
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = var.tags
}

# ---- AKS cluster (Free control plane, 1 small node) ---------------------------
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "aks-${var.prefix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "${var.prefix}-aks"
  sku_tier            = "Free"

  default_node_pool {
    name            = "system"
    node_count      = var.node_count
    vm_size         = var.node_vm_size
    os_disk_size_gb = 30
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Let AKS nodes pull images from ACR without any password
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.acr.id
  skip_service_principal_aad_check = true
}

# ---- Identity used by GitHub Actions CD (OIDC, no stored secret) -------------
resource "azurerm_user_assigned_identity" "github" {
  count               = var.github_repo == "" ? 0 : 1
  name                = "id-${var.prefix}-github-cd"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = var.tags
}

resource "azurerm_federated_identity_credential" "github" {
  count               = var.github_repo == "" ? 0 : 1
  name                = "github-environment-production"
  resource_group_name = azurerm_resource_group.rg.name
  parent_id           = azurerm_user_assigned_identity.github[0].id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  subject             = "repo:${var.github_repo}:environment:production"
}

# Contributor on this resource group only: push to ACR + get AKS credentials
resource "azurerm_role_assignment" "github_rg_contributor" {
  count                = var.github_repo == "" ? 0 : 1
  principal_id         = azurerm_user_assigned_identity.github[0].principal_id
  role_definition_name = "Contributor"
  scope                = azurerm_resource_group.rg.id
}
