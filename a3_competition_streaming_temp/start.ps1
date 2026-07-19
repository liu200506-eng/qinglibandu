$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "     青藜伴读 MagicStudy - 一键启动" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

$errorCount = 0

Write-Host "[1/6] 环境检查..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python未安装"
    }
    Write-Host "      Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "      ❌ Python未安装或未添加到PATH" -ForegroundColor Red
    $errorCount++
}

try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Node.js未安装"
    }
    Write-Host "      Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "      ❌ Node.js未安装或未添加到PATH" -ForegroundColor Red
    $errorCount++
}

try {
    $npmVersion = npm --version 2>&1
    Write-Host "      npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "      ⚠️ npm可能未安装" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/6] 检查依赖..." -ForegroundColor Yellow

$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

if (Test-Path (Join-Path $backendDir "requirements.txt")) {
    Write-Host "      ✅ backend/requirements.txt 存在" -ForegroundColor Green
} else {
    Write-Host "      ❌ backend/requirements.txt 不存在" -ForegroundColor Red
    $errorCount++
}

if (Test-Path (Join-Path $frontendDir "package.json")) {
    Write-Host "      ✅ frontend/package.json 存在" -ForegroundColor Green
} else {
    Write-Host "      ❌ frontend/package.json 不存在" -ForegroundColor Red
    $errorCount++
}

Write-Host ""
Write-Host "[3/6] 检查环境配置..." -ForegroundColor Yellow

$envFile = Join-Path $backendDir ".env"
$envExample = Join-Path $backendDir ".env.example"

if (Test-Path $envFile) {
    Write-Host "      ✅ .env 配置文件存在" -ForegroundColor Green
} else {
    Write-Host "      ⚠️ .env 不存在，将使用默认配置" -ForegroundColor Yellow
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile -Force
        Write-Host "      ℹ️ 已从 .env.example 创建 .env" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "[4/6] 清理旧进程..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "[5/6] 启动后端服务 (port 8001)..." -ForegroundColor Yellow
Start-Process python -ArgumentList "main.py" -WorkingDirectory $backendDir -WindowStyle Hidden
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[6/6] 启动前端服务 (port 5175)..." -ForegroundColor Yellow
Start-Process npm.cmd -ArgumentList "run","dev" -WorkingDirectory $frontendDir
Start-Sleep -Seconds 4

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "  启动完成！浏览器打开下面的地址：" -ForegroundColor Green
Write-Host "  前端：http://localhost:5175" -ForegroundColor Green
Write-Host "  后端：http://localhost:8001" -ForegroundColor Green
Write-Host "  API文档：http://localhost:8001/docs" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "如果没自动弹出，请手动在浏览器里 Ctrl+Shift+R 强制刷新" -ForegroundColor Magenta
Write-Host ""
Write-Host "按 Ctrl+C 退出此窗口（前后端后台继续跑）" -ForegroundColor Gray
Write-Host ""

try {
    Start-Sleep -Seconds 10
} catch {}
