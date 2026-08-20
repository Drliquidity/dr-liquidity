#!/bin/bash
# Quick start script for DR Liquidity
set -e

cd "$(dirname "$0")"

# Activate parent venv if it exists
if [ -f "../venv/bin/activate" ]; then
  source ../venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

# Seed if database doesn't exist
if [ ! -f "instance/drliquidity.db" ]; then
  echo "Seeding database..."
  python seed.py
fi

# Start server
echo ""
echo "🚀 DR Liquidity starting at http://localhost:5001"
echo "   Admin:   admin@drliquidity.com / admin123"
echo "   Trader:  trader@example.com / trader123"
echo ""
python app.py
