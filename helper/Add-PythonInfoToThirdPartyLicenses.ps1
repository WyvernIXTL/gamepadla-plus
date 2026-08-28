$content = "
===========================================================================================================

Python License

-----------------------------------------------------------------------------------------------------------
"
$content >> .\THIRD-PARTY-LICENSES.txt
Get-Content (Join-Path (Split-Path (get-command python).Source) "LICENSE.txt") >> .\THIRD-PARTY-LICENSES.txt
