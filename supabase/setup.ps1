# Supabase Setup Script for Spice Tracker Bot (PowerShell)
# This script automates the initial setup of your Supabase project

param(
    [string]$ProjectRef
)

Write-Host "🚀 Setting up Supabase for Spice Tracker Bot..." -ForegroundColor Green

# Check if Supabase CLI is installed
try {
    $null = Get-Command supabase -ErrorAction Stop
    Write-Host "✅ Supabase CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Supabase CLI not found. Installing..." -ForegroundColor Red
    npm install -g supabase
}

# Check if we're in the right directory
if (-not (Test-Path "supabase/config.toml")) {
    Write-Host "❌ Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Get project reference from user if not provided as parameter
if (-not $ProjectRef) {
    Write-Host "📋 Please enter your Supabase project reference:" -ForegroundColor Yellow
    Write-Host "   (You can find this in your Supabase dashboard URL: https://supabase.com/dashboard/project/[PROJECT-REF])" -ForegroundColor Gray
    $ProjectRef = Read-Host "Project Reference"
}

if (-not $ProjectRef) {
    Write-Host "❌ Project reference is required" -ForegroundColor Red
    exit 1
}

# Initialize Supabase if not already done
if (-not (Test-Path "supabase/.git")) {
    Write-Host "🔧 Initializing Supabase..." -ForegroundColor Yellow
    supabase init
}

# Link to remote project
Write-Host "🔗 Linking to Supabase project: $ProjectRef" -ForegroundColor Yellow
supabase link --project-ref $ProjectRef

# Run migrations
Write-Host "🗄️ Running database migrations..." -ForegroundColor Yellow
supabase db push

# Ask if user wants to seed with sample data
Write-Host "🌱 Would you like to seed the database with sample data? (y/n)" -ForegroundColor Yellow
$SeedDb = Read-Host "Seed database?"

if ($SeedDb -match "^[Yy]$") {
    Write-Host "🌱 Seeding database with sample data..." -ForegroundColor Yellow
    supabase db reset --linked
}

Write-Host "✅ Supabase setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Your database is now ready with:" -ForegroundColor Cyan
Write-Host "   • Users table for tracking players" -ForegroundColor White
Write-Host "   • Deposits table for spice sand harvests" -ForegroundColor White
Write-Host "   • Audit log for tracking changes" -ForegroundColor White
Write-Host "   • Optimized indexes for performance" -ForegroundColor White
Write-Host "   • Row Level Security enabled" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Get your database connection string from Supabase dashboard" -ForegroundColor White
Write-Host "   2. Set the DATABASE_URL environment variable in Fly.io" -ForegroundColor White
Write-Host "   3. Deploy your bot!" -ForegroundColor White
Write-Host ""
Write-Host "📚 Connection string format:" -ForegroundColor Cyan
Write-Host "   postgresql://postgres:[YOUR-PASSWORD]@db.$ProjectRef.supabase.co:5432/postgres" -ForegroundColor White
