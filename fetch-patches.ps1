$base = "https://raw.githubusercontent.com/Murphy601/Remo/cursor/holiday-infill-lines-32c6"
Invoke-WebRequest -UseBasicParsing -Uri "$base/infill-tests.md" -OutFile "tests/test.patch"
Invoke-WebRequest -UseBasicParsing -Uri "$base/infill-solution.md" -OutFile "solution/solution.patch"
Write-Host "lines:" (Get-Content tests/test.patch).Count (Get-Content solution/solution.patch).Count
