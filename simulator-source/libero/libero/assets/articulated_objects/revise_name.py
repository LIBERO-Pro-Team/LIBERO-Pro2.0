import os

def rename_items_recursive(root_path):
    # Process subdirectories before files in the current directory to avoid path issues.
    # Collect all subdirectories first.
    subdirectories = []
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            subdirectories.append(item)
    
    # Process subdirectories recursively.
    for subdir in subdirectories:
        subdir_path = os.path.join(root_path, subdir)
        rename_items_recursive(subdir_path)
    
    # Process all items (files and directories) in the current directory.
    for item in os.listdir(root_path):
        old_path = os.path.join(root_path, item)
        
        # Check whether the name contains "wooden".
        if "wooden" in item:
            # Replace "wooden" with "yellow" in the name.
            new_name = item.replace("wooden", "yellow")
            new_path = os.path.join(root_path, new_name)
            
            # Avoid renaming an item to the same name.
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")

if __name__ == "__main__":
    # Set the root directory to process.
    root_folder = "./yellow_cabinet"
    
    # Check whether the root directory exists.
    if not os.path.exists(root_folder):
        print(f"Error: root directory '{root_folder}' does not exist")
    else:
        # Call the recursive rename function.
        rename_items_recursive(root_folder)
        print("All rename operations completed")
