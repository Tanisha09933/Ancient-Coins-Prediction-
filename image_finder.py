import os
import unicodedata


def normalize_string(s):
    """
    A helper function to remove special characters and make a string lowercase
    for reliable comparison.
    """
    if not s:
        return ""
    # This handles special characters like the 'ȳ' in 'Dȳnasty'
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.lower().strip()


def find_image_path(coin_data_dict):
    """
    Constructs and verifies the path for a coin image by searching for folders
    that match, ignoring minor whitespace or character differences.
    """
    dynasty = coin_data_dict.get('dynasty')
    king_name = coin_data_dict.get('king_name')
    code = coin_data_dict.get('code')

    if not all([dynasty, king_name, code]):
        return None

    time_period = "Ancient India"

    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # --- NEW ROBUST PATH FINDING ---

        # 1. Start at the 'asset' folder
        asset_path = os.path.join(base_dir, 'static', 'asset')
        if not os.path.isdir(asset_path):
            return None

        # 2. Find the 'coin image' folder, ignoring leading/trailing spaces
        coin_image_folder_name = None
        for folder in os.listdir(asset_path):
            if folder.strip() == 'coin image':
                coin_image_folder_name = folder
                break

        if not coin_image_folder_name:
            return None  # Could not find the main 'coin image' directory

        # 3. Build the path to the Time Period folder
        time_period_path = os.path.join(asset_path, coin_image_folder_name, time_period)
        if not os.path.isdir(time_period_path):
            return None

        # 4. Find the correct dynasty folder by comparing normalized names
        dynasty_folder_name = None
        normalized_db_dynasty = normalize_string(dynasty)
        for folder in os.listdir(time_period_path):
            if normalize_string(folder) == normalized_db_dynasty:
                dynasty_folder_name = folder
                break

        if not dynasty_folder_name:
            return None

        # 5. Find the king's folder inside the found dynasty folder
        dynasty_path = os.path.join(time_period_path, dynasty_folder_name)
        king_folder_name = None
        normalized_db_king = normalize_string(king_name)
        for folder in os.listdir(dynasty_path):
            if normalize_string(folder).startswith(normalized_db_king):
                king_folder_name = folder
                break

        if not king_folder_name:
            return None

        # 6. Construct and check the final path
        image_filesystem_path = os.path.join(dynasty_path, king_folder_name, f"{code}.jpg")

        if os.path.exists(image_filesystem_path):
            # Use the actual folder names we found for the URL
            image_url_path = f"/static/asset/{coin_image_folder_name}/{time_period}/{dynasty_folder_name}/{king_folder_name}/{code}.jpg"
            return image_url_path
        else:
            return None

    except Exception as e:
        print(f"[Image Finder] An unexpected error occurred: {e}")
        return None

    