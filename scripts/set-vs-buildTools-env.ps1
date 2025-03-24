# Run this using vcvars64.bat location and architecture, e.g.
#   .\set-vs-buildTools-env.ps1 "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" amd64

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
