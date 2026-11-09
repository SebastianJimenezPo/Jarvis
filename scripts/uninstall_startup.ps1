[CmdletBinding(SupportsShouldProcess)]
param()
$ErrorActionPreference = 'Stop'
$taskName = 'JarvisCore-' + [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (!$task) { Write-Output 'El inicio automático no está instalado.'; return }
if ($PSCmdlet.ShouldProcess($taskName, 'Eliminar inicio automático (no borra preferencias ni voz)')) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}
