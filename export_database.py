#!/usr/bin/env python3
"""
Database Export Script for Loopync
This exports all collections from MongoDB to JSON files
"""
import os
import json
from pymongo import MongoClient
from bson import json_util
from datetime import datetime

def export_database():
    """Export entire database to JSON files"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client['test_database']
    
    # Create export directory
    export_dir = '/app/database_export'
    os.makedirs(export_dir, exist_ok=True)
    
    print("="*60)
    print("EXPORTING DATABASE")
    print("="*60)
    
    exported_collections = []
    total_documents = 0
    
    # Get all collections
    collections = db.list_collection_names()
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        
        if count > 0:
            print(f"\n📦 Exporting {collection_name}: {count} documents")
            
            # Export to JSON file
            documents = list(collection.find({}, {"_id": 0}))
            
            filename = f"{export_dir}/{collection_name}.json"
            with open(filename, 'w') as f:
                json.dump(documents, f, default=json_util.default, indent=2)
            
            exported_collections.append({
                'name': collection_name,
                'count': count,
                'filename': filename
            })
            total_documents += count
            print(f"   ✅ Saved to {filename}")
    
    # Create manifest file
    manifest = {
        'export_date': datetime.now().isoformat(),
        'database': 'test_database',
        'total_collections': len(exported_collections),
        'total_documents': total_documents,
        'collections': exported_collections
    }
    
    manifest_file = f"{export_dir}/manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("\n" + "="*60)
    print(f"✅ Export complete!")
    print(f"   Collections: {len(exported_collections)}")
    print(f"   Documents: {total_documents}")
    print(f"   Location: {export_dir}")
    print(f"   Manifest: {manifest_file}")
    print("="*60)
    
    return export_dir

if __name__ == "__main__":
    export_database()
