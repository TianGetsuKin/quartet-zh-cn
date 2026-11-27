$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$l16 = Join-Path (Split-Path $PSScriptRoot) 'linux-l16'
Add-Type -Path "$l16/Mono.Cecil.dll"
$rel='QuartetLinux_Data/Managed/Assembly-CSharp.dll'
$official=[Mono.Cecil.ModuleDefinition]::ReadModule("$l16/input/$rel")
$patch=[Mono.Cecil.ModuleDefinition]::ReadModule("$l16/stage/$rel")
$fixes=@()
foreach($t in $official.Types){
    $candidate=$patch.GetType($t.FullName)
    foreach($f in $t.Fields){
        $g=$candidate.Fields.Where({$_.Name -ceq $f.Name})[0]
        if($g.IsPublic -and !$f.IsPublic -and !$f.IsStatic -and !$f.IsInitOnly -and !$f.IsNotSerialized -and !($f.CustomAttributes.AttributeType.FullName -match '^UnityEngine.Serialize(Field|Reference)$')){
            $g.IsNotSerialized=$true
            $fixes+=$t.Name+'.'+$f.Name
        }
    }
}
$expected=@('FieldMenuEquipController.selectedSlot','QuartetLineView.currentLine','QuartetOptionsListView.lastSeenLine')
if($fixes.Count -ne 3 -or (Compare-Object $fixes $expected)){throw 'Unexpected field visibility changes'}
$dest=Join-Path $PSScriptRoot "stage/$rel"
New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
$patch.Write($dest)
$patch.Dispose()
$official.Dispose()
$check=[Mono.Cecil.ModuleDefinition]::ReadModule($dest)
foreach($name in $expected){
    $t,$n=$name.Split('.')
    $field=$check.GetType($t).Fields.Where({$_.Name -ceq $n})[0]
    if(!$field.IsNotSerialized -or !$field.IsPublic){throw $name}
}
$check.Dispose()
Add-Type -Path "$l16/CompareIL.dll"
$differences=[CompareIL]::Diff("$l16/stage/$rel",$dest)
if ($differences.Count -ne 3 -or @($differences | Where-Object {$_ -notlike 'F:*'}).Count){throw 'Unexpected managed changes'}
$differences
