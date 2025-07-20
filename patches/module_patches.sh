#!/bin/bash

# Get the site-packages directory
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")

# Function to backup original file
backup_file() {
    if [ ! -f "$1.original" ]; then
        cp "$1" "$1.original"
    fi
}

# Function to apply patch
apply_patch() {
    local module_path="$1"
    local patch_file="$2"
    
    if [ -f "$module_path" ]; then
        echo "Applying patch to $module_path"
        backup_file "$module_path"
        cat "$patch_file" > "$module_path"
    else
        echo "Warning: Module file $module_path not found"
    fi
}

# Create patches directory if it doesn't exist
mkdir -p /app/patches/modified_files

# Apply patches for each modified file
for patch_file in /app/patches/modified_files/*; do
    if [ -f "$patch_file" ]; then
        # Get the relative path from the filename (stored in the first line of the patch file)
        relative_path=$(head -n 1 "$patch_file" | grep "##" | sed 's/## //')
        if [ ! -z "$relative_path" ]; then
            module_path="$SITE_PACKAGES/$relative_path"
            apply_patch "$module_path" "$patch_file"
        fi
    fi
done

echo "All patches applied successfully" 