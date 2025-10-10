
#!/usr/bin/env bash
set -e

echo "🔨 Building glmctl Docker image..."

if docker buildx build --platform linux/amd64 -t glmctl-env-amd64 .; then
    echo "✅ Build completed successfully!"
    echo "   Image: glmctl-env-amd64"
else
    echo "❌ Build failed!"
    exit 1
fi
