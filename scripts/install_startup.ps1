[CmdletBinding(SupportsShouldProcess)]
param([switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv\Scripts\pythonw.exe'
$launcherPath = Join-Path $PSScriptRoot 'run_resident.pyw'
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Falta el entorno .venv; ejecuta la instalación primero.' }
if (!(Test-Path -LiteralPath $launcherPath)) { throw 'Falta el lanzador residente.' }
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$taskName = 'JarvisCore-' + $identity.User.Value
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument ('"' + $launcherPath + '"') -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity.Name
$principal = New-ScheduledTaskPrincipal -UserId $identity.Name -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings
Write-Output "Tarea por usuario: $taskName. Ejecutará pythonw al iniciar sesión, sin privilegios elevados."
if ($ValidateOnly) {
    [pscustomobject]@{ TaskName=$taskName; User=$identity.Name; Execute=$pythonPath; Arguments=$action.Arguments;
        WorkingDirectory=$projectRoot; LogonType='Interactive'; RunLevel='Limited'; Trigger='AtLogOn' } | ConvertTo-Json
    return
}
if ($PSCmdlet.ShouldProcess($taskName, 'Registrar o actualizar inicio automático de Jarvis')) {
    Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
    Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
}
