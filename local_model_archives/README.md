# Local Model Archive

This folder stores the local model bundle split into GitHub-friendly chunks.

## Restore on Windows PowerShell

```powershell
$parts = Get-ChildItem -Filter 'material_tagging_local_models.zip.part*' | Sort-Object Name
$out = [System.IO.File]::Create('material_tagging_local_models.zip')
foreach ($part in $parts) {
  $bytes = [System.IO.File]::ReadAllBytes($part.FullName)
  $out.Write($bytes, 0, $bytes.Length)
}
$out.Close()
Expand-Archive -LiteralPath material_tagging_local_models.zip -DestinationPath . -Force
```

Included:
- `models/faster-whisper-small/`
- `vosk-model-small-en-us-0.15/`
- `local_dependencies/`
