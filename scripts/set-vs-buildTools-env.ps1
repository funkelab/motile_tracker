function Invoke-BatchEnvironment {
    param (
        [string[]]$BatchFileWithArgs
    )

    $BatchFile = $BatchFileWithArgs[0]
    $BatchArgs = $BatchFileWithArgs[1..($BatchFileWithArgs.Length - 1)]

    cmd /c "`"$BatchFile`" $BatchArgs && set" | ForEach-Object {
        if ($_ -match '^(.*?)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

Invoke-BatchEnvironment $args
