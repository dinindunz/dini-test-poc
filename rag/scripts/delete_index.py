#!/usr/bin/env python
"""
Delete S3 vector index
"""
import sys
sys.path.insert(0, '..')

from core.s3_vector_store import S3VectorStore

# Delete the index
store = S3VectorStore('dini-code-vectors', 'code-embeddings')
store.connect()
store.delete_index()
print("\n✅ Index deleted successfully. You can now run vectorise_s3.sh to recreate it with proper configuration.")
