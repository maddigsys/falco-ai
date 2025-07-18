#!/bin/bash
# Build script for gRPC protobuf files

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTO_DIR="$PROJECT_ROOT/proto"
OUTPUT_DIR="$PROJECT_ROOT/generated"

echo "🔨 Building gRPC protobuf files for Falco MCP..."

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if protoc is installed
if ! command -v protoc &> /dev/null; then
    echo "❌ protoc is not installed. Please install Protocol Buffers compiler:"
    echo "   macOS: brew install protobuf"
    echo "   Ubuntu: sudo apt install protobuf-compiler"
    echo "   Or download from: https://github.com/protocolbuffers/protobuf/releases"
    exit 1
fi

# Check if grpcio-tools is installed
if ! python3 -c "import grpc_tools" &> /dev/null; then
    echo "❌ grpcio-tools is not installed. Installing..."
    pip3 install grpcio-tools
fi

echo "📁 Proto directory: $PROTO_DIR"
echo "📁 Output directory: $OUTPUT_DIR"

# Generate Python gRPC code
echo "🔧 Generating Python gRPC code..."
python3 -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/falco_mcp.proto"

# Generate Go code (optional)
if command -v protoc-gen-go &> /dev/null && command -v protoc-gen-go-grpc &> /dev/null; then
    echo "🔧 Generating Go gRPC code..."
    mkdir -p "$OUTPUT_DIR/go"
    protoc \
        --proto_path="$PROTO_DIR" \
        --go_out="$OUTPUT_DIR/go" \
        --go-grpc_out="$OUTPUT_DIR/go" \
        "$PROTO_DIR/falco_mcp.proto"
fi

# Generate JavaScript/TypeScript code (optional)
if command -v grpc_tools_node_protoc &> /dev/null; then
    echo "🔧 Generating JavaScript gRPC code..."
    mkdir -p "$OUTPUT_DIR/js"
    grpc_tools_node_protoc \
        --proto_path="$PROTO_DIR" \
        --js_out=import_style=commonjs:"$OUTPUT_DIR/js" \
        --grpc_out=grpc_js:"$OUTPUT_DIR/js" \
        "$PROTO_DIR/falco_mcp.proto"
fi

echo "✅ gRPC code generation complete!"
echo ""
echo "📋 Generated files:"
find "$OUTPUT_DIR" -name "*.py" -o -name "*.go" -o -name "*.js" | head -10

echo ""
echo "🚀 Next steps:"
echo "   1. Install dependencies: pip3 install -r grpc_requirements.txt"
echo "   2. Run gRPC server: python3 grpc_mcp_server.py"
echo "   3. Connect clients to: localhost:50051"

# Make the generated files importable
touch "$OUTPUT_DIR/__init__.py" 