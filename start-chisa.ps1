$ProjectDir = $PSScriptRoot
$Port = 12393
$LogDir = "$ProjectDir\logs"

function Test-Server {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("127.0.0.1", $Port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

# 1. Start the server hidden, with output written to log files
if (-not (Test-Server)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    # Update long-term memory from previous conversations before the server starts
    Start-Process "uv" -ArgumentList "run", "update_memory.py" -WorkingDirectory $ProjectDir `
        -WindowStyle Hidden -Wait `
        -RedirectStandardOutput "$LogDir\memory.log" `
        -RedirectStandardError "$LogDir\memory-error.log"
    Start-Process "uv" -ArgumentList "run", "run_server.py" -WorkingDirectory $ProjectDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput "$LogDir\server.log" `
        -RedirectStandardError "$LogDir\server-error.log"

    # 2. Wait until the server accepts connections (max 3 minutes)
    $deadline = (Get-Date).AddMinutes(3)
    while (-not (Test-Server)) {
        if ((Get-Date) -gt $deadline) {
            Add-Type -AssemblyName PresentationFramework
            [System.Windows.MessageBox]::Show("Server did not start. See .\logs") | Out-Null
            exit 1
        }
        Start-Sleep -Seconds 1
    }
}

# 3. Launch the desktop app
$searchRoots = @("$env:LOCALAPPDATA\Programs", "$env:ProgramFiles")
$app = Get-ChildItem $searchRoots -Recurse -Filter "open-llm-vtuber*.exe" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch "uninstall" } |
    Select-Object -First 1

if ($app) {
    Start-Process $app.FullName
} else {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("Desktop app not found.") | Out-Null
}