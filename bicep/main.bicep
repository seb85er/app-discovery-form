// Parameters
param location string = resourceGroup().location
param appServicePlanSku string = 'B1'
param appServicePlanTier string = 'Basic' // Tier for the App Service Plan
param cosmosDbAccountName string = 'apppassportcosmos'
param appName string = 'apppassports'
param keyVaultName string = 'apppassports099'
param cosmosDbRegion string = location
param cosmosDbDatabaseName string = 'apppassports'
param cosmosDbContainerName string = 'applications'
param rgName string = 'apppass-rsg'  // Resource group name

// App Service Plan using standard resources
resource appServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: appName
  location: location
  sku: {
    tier: appServicePlanTier
    name: appServicePlanSku
  }
  properties: {
    reserved: true // For Linux, set to false if using Windows
  }
}

// App Service using standard resources
resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: appName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
  }
}

// Cosmos DB Account using standard resources
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2021-04-15' = {
  name: cosmosDbAccountName
  location: cosmosDbRegion
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: cosmosDbRegion
        failoverPriority: 0
      }
    ]
  }
}

// Cosmos DB SQL Database (Correct resource name and parent relationship)
resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2021-04-15' = {
  name: cosmosDbDatabaseName
  parent: cosmosDbAccount // Correct parent-child relationship
  properties: {
    resource: {
      id: cosmosDbDatabaseName
    }
    options: {
      throughput: 400 // Set the throughput (RU/s)
    }
  }
}

// Cosmos DB Container (Correct resource name and parent relationship)
resource cosmosDbContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-04-15' = {
  name: cosmosDbContainerName
  parent: cosmosDbDatabase // Correct parent-child relationship
  properties: {
    resource: {
      id: cosmosDbContainerName
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
    options: {
      throughput: 400 // Set the throughput (RU/s) for the container if needed
    }
  }
}

// Key Vault using standard resources
resource keyVault 'Microsoft.KeyVault/vaults@2021-06-01-preview' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    accessPolicies: []
  }
}

// Output Section
output resourceGroupName string = rgName
output appServiceUrl string = appService.properties.defaultHostName
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
output keyVaultUri string = keyVault.properties.vaultUri
