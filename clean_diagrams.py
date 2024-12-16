import os
import re


def remove_patterns_from_files(directory_path):
    """
    Removes specific rule and flow patterns from all files in the given directory.

    Args:
        directory_path (str): Path to the directory containing files to process
    """
    # Patterns to match both single rule and multiple rule formats
    patterns = [
        r'\[ *Rule: *\d+, *Flow: *\d+ *\]',  # Single rule pattern
        r'\[ *(?:Rule: *\d+, *Flow: *\d+ *\| *)+Rule: *\d+, *Flow: *\d+ *\]'  # Multiple rules pattern
    ]

    # Compile patterns for better performance
    compiled_patterns = [re.compile(pattern) for pattern in patterns]

    try:
        # Iterate through all files in the directory
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)

            # Skip if it's not a file
            if not os.path.isfile(file_path):
                continue

            try:
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Apply all patterns
                modified_content = content
                for pattern in compiled_patterns:
                    modified_content = pattern.sub('', modified_content)

                # Only write if content was modified
                if modified_content != content:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(modified_content)
                    print(f"Successfully processed: {filename}")
                else:
                    print(f"No patterns found in: {filename}")

            except Exception as e:
                print(f"Error processing file {filename}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error accessing directory: {str(e)}")
        return


# Example usage
if __name__ == "__main__":
    directory = input("Enter the directory path: ")
    remove_patterns_from_files(directory)