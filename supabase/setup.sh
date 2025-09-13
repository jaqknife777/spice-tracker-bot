#!/bin/bash

# Supabase Setup Script for Spice Tracker Bot
# This script automates the initial setup of your Supabase project

set -e

echo "🚀 Setting up Supabase for Spice Tracker Bot..."

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Installing..."
    npm install -g supabase
fi

# Check if we're in the right directory
if [ ! -f "supabase/config.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Get project reference from user
echo "📋 Please enter your Supabase project reference:"
echo "   (You can find this in your Supabase dashboard URL: https://supabase.com/dashboard/project/[PROJECT-REF])"
read -p "Project Reference: " PROJECT_REF

if [ -z "$PROJECT_REF" ]; then
    echo "❌ Project reference is required"
    exit 1
fi

# Initialize Supabase if not already done
if [ ! -d "supabase/.git" ]; then
    echo "🔧 Initializing Supabase..."
    supabase init
fi

# Link to remote project
echo "🔗 Linking to Supabase project: $PROJECT_REF"
supabase link --project-ref "$PROJECT_REF"

# Run migrations
echo "🗄️ Running database migrations..."
supabase db push

# Ask if user wants to seed with sample data
echo "🌱 Would you like to seed the database with sample data? (y/n)"
read -p "Seed database? " SEED_DB

if [[ $SEED_DB =~ ^[Yy]$ ]]; then
    echo "🌱 Seeding database with sample data..."
    supabase db reset --linked
fi

echo "✅ Supabase setup complete!"
echo ""
echo "📊 Your database is now ready with:"
echo "   • Users table for tracking players"
echo "   • Deposits table for spice sand harvests"
echo "   • Audit log for tracking changes"
echo "   • Optimized indexes for performance"
echo "   • Row Level Security enabled"
echo ""
echo "🔑 Next steps:"
echo "   1. Get your database connection string from Supabase dashboard"
echo "   2. Set the DATABASE_URL environment variable in Fly.io"
echo "   3. Deploy your bot!"
echo ""
echo "📚 Connection string format:"
echo "   postgresql://postgres:[YOUR-PASSWORD]@db.$PROJECT_REF.supabase.co:5432/postgres"
