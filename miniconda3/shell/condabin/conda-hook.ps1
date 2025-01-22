$Env:CONDA_EXE = "/Users/macbook/Desktop/daily-brief/miniconda3/bin/conda"
$Env:_CE_M = $null
$Env:_CE_CONDA = $null
$Env:_CONDA_ROOT = "/Users/macbook/Desktop/daily-brief/miniconda3"
$Env:_CONDA_EXE = "/Users/macbook/Desktop/daily-brief/miniconda3/bin/conda"
$CondaModuleArgs = @{ChangePs1 = $False}
Import-Module "$Env:_CONDA_ROOT\shell\condabin\Conda.psm1" -ArgumentList $CondaModuleArgs

Remove-Variable CondaModuleArgs