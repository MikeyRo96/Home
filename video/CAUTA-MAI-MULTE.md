# Caută mai multe pe GitHub (când API-ul își revine)

GitHub API dă **rate limit: 60 cereri/oră fără token** (sau 5.000 cu token). La ~130 cereri s-a oprit.
Reset: după 1 oră. Verifici când: `curl -s https://api.github.com/rate_limit`

## Comenzi gata de rulat (Windows PowerShell)

```powershell
$q = @(
 "video+reverse+engineering",
 "video+breakdown",
 "tiktok+video+analysis",
 "shot+list+ai",
 "video+to+edl",
 "viral+video+recreate",
 "video+analysis+skill",
 "edit+blueprint+video",
 "video+remake",
 "premiere+project+parser"
)
foreach ($x in $q) {
  Write-Host "### $x"
  (Invoke-RestMethod "https://api.github.com/search/repositories?q=$x&sort=stars&order=desc&per_page=8").items |
    ForEach-Object { "{0}`t{1}`t{2}`t{3}" -f $_.stargazers_count, $_.full_name, $_.pushed_at.Substring(0,10), $_.description }
}
```

## Topic-uri (cele mai dense)

`github.com/topics/video-remake` · `github.com/topics/video-reverse-engineering` · `github.com/topics/shot-detection` · `github.com/topics/video-editing` · `github.com/topics/scene-detection`

## Reddit — căutări care dau rezultate

- `site:reddit.com/r/editors "recreate" "reference video"`
- `site:reddit.com/r/premiere "how was this made"`
- `site:reddit.com/r/ClaudeCode video analysis plugin`
- `site:reddit.com/r/comfyui video reverse engineering`

## Regulă

Fiecare repo trece în `TOATE-UNELTELE.md` doar cu: ★, licență, ultima actualizare — verificate prin API, nu din memorie.
