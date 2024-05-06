import os
import re
from typing import List


def read_file(file_path: str) -> List[str]:
    """Reads the content of a markdown file and returns it as a list of lines."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.readlines()
    return content


def modify_header(content: List[str], category_id: str) -> List[str]:
    """Modifies the YAML front matter in the markdown content to include the category."""
    in_header = False
    new_content = []
    category_added = False
    end_header_pattern = r"^---$"
    start_header_found = False

    for line in content:
        if re.match(end_header_pattern, line) and start_header_found:
            in_header = False
            if not category_added:
                new_content.append(f"category: {category_id}\n")
            new_content.append(line)
        elif in_header:
            if line.startswith("category:"):
                new_content.append(f"category: {category_id}\n")
                category_added = True
            else:
                new_content.append(line)
        else:
            if line.strip() == "---":
                in_header = True
                start_header_found = True
            new_content.append(line)
    return new_content


def update_markdown_files(directory: str, category_id: str) -> None:
    """Updates all markdown files in a given directory by modifying their headers."""
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            content = read_file(file_path)
            modified_content = modify_header(content, category_id)
            with open(file_path, "w", encoding="utf-8") as file:
                file.writelines(modified_content)


# Example usage
if __name__ == "__main__":
    directory = os.getenv("MARKDOWN_FILES_DIRECTORY", "default_directory")
    category_id = os.getenv("CATEGORY_ID", "default_category_id")
    update_markdown_files(directory, category_id)
