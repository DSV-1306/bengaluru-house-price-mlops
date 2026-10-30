output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "aks_name" {
  value = azurerm_kubernetes_cluster.aks.name
}

output "get_credentials_command" {
  value = "az aks get-credentials --resource-group ${azurerm_resource_group.rg.name} --name ${azurerm_kubernetes_cluster.aks.name} --overwrite-existing"
}

# Values for the GitHub Actions secrets (IDs, not passwords)
output "github_cd_client_id" {
  value = var.github_repo == "" ? "" : azurerm_user_assigned_identity.github[0].client_id
}

output "azure_tenant_id" {
  value = var.github_repo == "" ? "" : azurerm_user_assigned_identity.github[0].tenant_id
}
