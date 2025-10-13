"""
Clear Python cache to force reload of updated code
"""

import os
import shutil

print("=" * 60)
print("CLEARING PYTHON CACHE")
print("=" * 60)

# Remove __pycache__ directories
removed_count = 0
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_dir = os.path.join(root, '__pycache__')
        print(f"Removing: {cache_dir}")
        shutil.rmtree(cache_dir)
        removed_count += 1

# Remove .pyc files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pyc'):
            pyc_file = os.path.join(root, file)
            print(f"Removing: {pyc_file}")
            os.remove(pyc_file)
            removed_count += 1

print(f"\n✅ Cleaned {removed_count} cache item(s)")
print("=" * 60)
print("\nNow restart your app: python integrated_app.py")