$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$oldRoot = Join-Path (Split-Path (Split-Path $PSScriptRoot)) 'rebased-25279268'
Add-Type -Path (Resolve-Path ./Mono.Cecil.dll)
Add-Type -Path (Resolve-Path ./CompareIL.dll)
$oldGame = Join-Path $oldRoot 'linux-native/input/build25279268/QuartetLinux_Data/Managed/Assembly-CSharp.dll'
$newGame = (Resolve-Path input/QuartetLinux_Data/Managed/Assembly-CSharp.dll).Path
$candidate = (Resolve-Path managed-work/new/final.dll).Path
$official = [CompareIL]::Diff($oldGame,$newGame)
$oldReplay = [CompareIL]::Diff((Resolve-Path managed-work/l15-reference.dll),(Resolve-Path managed-work/old/final.dll))
$through = [CompareIL]::Diff((Resolve-Path managed-work/old/final.dll),$candidate)
$hooks = [CompareIL]::Diff($newGame,$candidate)
if ($oldReplay.Count -ne 0 -or (Compare-Object $official $through) -or @($official | Where-Object {$_ -cin $hooks}).Count -ne 0) { throw 'Conflicting official IL or localization replay difference' }
Copy-Item $candidate ./stage/QuartetLinux_Data/Managed/Assembly-CSharp.dll -Force
& "$oldRoot/work-revisions/native-gear-l13/stage/Verify.exe" (Resolve-Path stage/QuartetLinux_Data/Managed) "$oldRoot/linux-native/input/build25279268/QuartetLinux_Data/Managed"
if ($LASTEXITCODE -ne 0) { throw 'Runtime and hook verification failed' }
@{old_replay_diff=$oldReplay.Count; official_delta=$official; localized_delta=$hooks; official_vs_hooks_overlap=0; hook_runtime_verified=$true} | ConvertTo-Json -Depth 3 | Set-Content -Encoding utf8 managed-check.json
