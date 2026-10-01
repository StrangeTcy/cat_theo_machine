$ErrorActionPreference = "Stop"
$lines = Get-Content "X:\hyge\snapshots\talk_state.wire"
$l = $lines[1]
$start = $l.IndexOf("C:definition-reading") - 1
$depth = 0; $end = $start
for ($j = $start; $j -lt $l.Length; $j++) {
    $c = $l[$j]
    if ($c -eq '(') { $depth++ }
    elseif ($c -eq ')') { $depth--; if ($depth -eq 0) { $end = $j; break } }
}
$node = $l.Substring($start, $end - $start + 1)

$tok = New-Object System.Collections.ArrayList
$sb = New-Object System.Text.StringBuilder
foreach ($c in $node.ToCharArray()) {
    if ($c -eq '(' -or $c -eq ')') {
        if ($sb.Length -gt 0) { [void]$tok.Add($sb.ToString()); [void]$sb.Clear() }
        [void]$tok.Add([string]$c)
    }
    elseif ($c -eq ' ') {
        if ($sb.Length -gt 0) { [void]$tok.Add($sb.ToString()); [void]$sb.Clear() }
    }
    else { [void]$sb.Append($c) }
}
if ($sb.Length -gt 0) { [void]$tok.Add($sb.ToString()) }

$script:tok = $tok
$script:pos = 0

# ( e1 e2 ... en E )  ->  Pair(e1, Pair(e2, ... Pair(en, Empty)...))
# bare E              ->  EmptyList
function ParseSpine {
    $kids = @()
    while ($script:tok[$script:pos] -ne ')') { $kids += (ParseEl) }
    $script:pos++
    if ($kids.Length -gt 0 -and $kids[$kids.Length - 1] -eq "E") {
        $kids = $kids[0..($kids.Length - 2)]
        $tail = "EMPTY"
    } else { $tail = "NONEMPTY-TAIL" }
    if ($kids.Length -eq 0) { return @{ Spine = @(); Tail = $tail } }
    return @{ Spine = $kids; Tail = $tail }
}
function ParseEl {
    $t = $script:tok[$script:pos]; $script:pos++
    if ($t -eq "E") { return "EMPTY" }
    if ($t -ne '(') { return $t }
    $inner = ParseSpine
    if ($inner.Spine.Length -eq 0) { return "EMPTY" }
    return $inner
}
function IsCompound($x) { return ($x -is [hashtable]) }

function Render($x) {
    if ($x -eq "EMPTY") { return "E" }
    if ($x -is [string]) { return $x }
    $parts = $x.Spine | ForEach-Object { (Render $_) }
    $s = "(" + ($parts -join " ")
    if ($x.Tail -eq "EMPTY") { $s += " E" }
    return $s + ")"
}

$outer = ParseSpine
Write-Output "=== NODE (outer spine) ==="
$outer.Spine | ForEach-Object { Write-Output (Render $_) }
