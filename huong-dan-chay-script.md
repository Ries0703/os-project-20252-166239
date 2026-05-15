# Hướng dẫn chạy script

1. Không muốn cài full, chạy bằng Docker: `powershell -ExecutionPolicy Bypass -File .\scripts\build-docker-image.ps1` -> `powershell -ExecutionPolicy Bypass -File .\scripts\run-docker-image.ps1`
2. Muốn cài full để code tiếp: `powershell -ExecutionPolicy Bypass -File .\scripts\setup-python-tooling.ps1` -> `powershell -ExecutionPolicy Bypass -File .\scripts\run-project.ps1`
