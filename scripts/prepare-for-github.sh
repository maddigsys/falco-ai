#!/bin/bash

# GitHub Preparation Script for Falco Vanguard
# Usage: ./scripts/prepare-for-github.sh

set -e

echo "🚀 GitHub Preparation Script"
echo "============================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check current git status
echo ""
echo "📊 Current git status:"
git status --porcelain

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "❌ Warning: .gitignore file not found"
    echo "   Please create a .gitignore file before committing"
else
    echo "✅ .gitignore file exists"
fi

# Check for sensitive files
echo ""
echo "🔒 Checking for sensitive files..."
SENSITIVE_FILES=(
    ".env"
    "alerts.db"
    "data/"
    "venv/"
    "__pycache__/"
    "*.pyc"
    ".DS_Store"
)

for file in "${SENSITIVE_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo "⚠️  Found sensitive file: $file"
        echo "   This should be in .gitignore"
    fi
done

# Check if README.md exists and is up to date
if [ -f "README.md" ]; then
    echo "✅ README.md exists"
    README_SIZE=$(wc -l < README.md)
    echo "   Lines in README: $README_SIZE"
else
    echo "❌ Warning: README.md not found"
fi

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt exists"
    REQUIREMENTS_COUNT=$(wc -l < requirements.txt)
    echo "   Dependencies: $REQUIREMENTS_COUNT"
else
    echo "❌ Warning: requirements.txt not found"
fi

# Check if Dockerfile exists
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile exists"
else
    echo "❌ Warning: Dockerfile not found"
fi

# Check if docker-compose.yaml exists
if [ -f "docker-compose.yaml" ]; then
    echo "✅ docker-compose.yaml exists"
else
    echo "❌ Warning: docker-compose.yaml not found"
fi

echo ""
echo "📋 Recommended commit commands:"
echo "================================"
echo ""
echo "# Add all files"
echo "git add ."
echo ""
echo "# Create initial commit"
echo "git commit -m \"Initial commit: Production-ready Falco Vanguard"
echo ""
echo "- Complete MCP integration with 15 security tools"
echo "- Cleaned codebase with only essential files"
echo "- Updated documentation and deployment guides"
echo "- Ready for Docker Hub publishing and Kubernetes deployment\""
echo ""
echo "# Add remote repository (replace with your repo URL)"
echo "git remote add origin <your-github-repo-url>"
echo ""
echo "# Push to GitHub"
echo "git push -u origin main"
echo ""

# Check if there are any uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 You have uncommitted changes:"
    git status --short
    echo ""
    echo "💡 Run 'git add .' to stage all changes"
else
    echo "✅ No uncommitted changes found"
fi

echo ""
echo "🎉 Project is ready for GitHub!"
echo ""
echo "📖 Next steps:"
echo "1. Review the files above"
echo "2. Run the commit commands"
echo "3. Push to GitHub"
echo "4. Build and push to Docker Hub"
echo "5. Deploy to Kubernetes"
echo ""
echo "📚 For more information, see DEPLOYMENT_README.md" 