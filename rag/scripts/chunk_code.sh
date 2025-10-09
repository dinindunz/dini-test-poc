# 1. Run the chunker
python ../chunk/multi_module_chunker.py ../../container/java17

# 2. Review output
cat ../data/chunks_sample.json | jq '.[0]'  # View first chunk

# 3. Verify statistics
# Should show something like:
# ============================================================
# Processing module: 01_dini_java17-quickstart-helloworld
# ============================================================

# Found 5 Java files
# Found 1 Swagger/API files
# Found 1 Markdown files
# Found 1 Gradle files

# ============================================================
# CHUNKING STATISTICS
# ============================================================

# 📦 Chunks per module:
#   01_dini_java17-quickstart-helloworld: 29

# 📄 Chunks per file type:
#   gradle: 2
#   java: 4
#   markdown: 19
#   swagger: 4

# 🏷️  Chunks per type:
#   api_endpoint: 1
#   api_info: 1
#   api_schema: 2
#   build_config_full: 1
#   class: 4
#   dependencies: 1
#   documentation: 19

# 📊 Total chunks: 29

# ✅ Saved 29 chunks to chunks_output.json
# ✅ Saved 10 sample chunks to chunks_sample.json