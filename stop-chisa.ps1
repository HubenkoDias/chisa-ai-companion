# Close the desktop app
Get-Process | Where-Object { $_.ProcessName -like "open-llm-vtuber*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop the server: the port may be listened on twice (IPv4 + IPv6), so kill each unique process
Get-NetTCPConnection -LocalPort 12393 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { taskkill /PID $_ /T /F | Out-Null }