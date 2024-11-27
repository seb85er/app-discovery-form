# Parameters
$TenantId = "832b0908-3585-4294-a01c-7763fc195006"
$SubscriptionId = "abfc46b6-7018-4e13-86ef-bf5c52e18d53" # Set your subscription ID here
$ResourceGroupName = "apppass-rsg" # Set your resource group name here
$Location = "uksouth" # Set the location
$BicepFilePath = "main.bicep" # Path to your Bicep file

#az login --tenant "832b0908-3585-4294-a01c-7763fc195006"
login-AzAccount -Tenant $TenantId
Set-AzContext -SubscriptionId $SubscriptionId
az account set --subscription $SubscriptionId

# check if resource group exists
$rg = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
if (-not $rg) {
    Write-Host "Creating resource group: $ResourceGroupName in $Location"
    New-AzResourceGroup -Name $ResourceGroupName -Location $Location
} else {
    Write-Host "Resource group $ResourceGroupName already exists."
}

# Validate the Bicep template
Write-Host "Validating the Bicep template..."
$validationResult = az deployment group validate `
    --resource-group $ResourceGroupName `
    --template-file $BicepFilePath

if ($validationResult) {
    Write-Host "Validation passed. Proceeding with the deployment..."

    # Deploy the Bicep template
    az deployment group create `
        --resource-group $ResourceGroupName `
        --template-file $BicepFilePath `
        --parameters location=$Location

    Write-Host "Deployment completed successfully."
} else {
    Write-Host "Validation failed. Please check your Bicep template."
}
