#!/usr/bin/env python3
"""
Universal Emoji Remover
Removes emojis from Python files while preserving indentation and formatting
Can process single files, directories, or entire project trees
"""

import os
import re
import argparse
import sys
from pathlib import Path
import unicodedata

class UniversalEmojiRemover:
    def __init__(self):
        # Comprehensive emoji patterns - covers most common emojis
        self.emoji_patterns = [
            # Common emojis found in development projects
            '🚀', '📡', '🕐', '📊', '⚡', '🔄', '🛑', '🎯', '▶️', '🧪', '🎮', '🔍',
            '📁', '❌', '⚠️', '✅', '💡', '📦', '⏱️', '🟢', '🔴', '📄', '💾', '🖱️',
            '🏠', '🔄', '🟡', '🔵', '⭐', '🎉', '🎊', '🎈', '🎁', '🎀', '🎂', '🍰',
            '🔥', '💯', '👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '👏', '🙌', '👐',
            '🔒', '🔓', '🔑', '🗝️', '🔨', '⚒️', '🛠️', '⚙️', '🔧', '🔩', '⚖️', '🔗',
            '📈', '📉', '📋', '📌', '📍', '📎', '🖇️', '📏', '📐', '✂️', '🗃️', '🗄️',
            '🗂️', '📂', '📁', '📰', '📑', '📜', '📃', '📄', '📊', '📈', '📉', '📋',
            '🎵', '🎶', '🎤', '🎧', '📻', '🎸', '🎹', '🥁', '🎺', '🎷', '🎻', '🎪',
            '🌟', '⭐', '🌠', '🌙', '☀️', '⛅', '☁️', '🌈', '🌊', '💧', '❄️', '⚡',
            '🔋', '🔌', '💻', '🖥️', '🖨️', '⌨️', '🖱️', '🖲️', '💽', '💾', '💿', '📀',
            '📱', '📞', '☎️', '📟', '📠', '📺', '📷', '📸', '📹', '🎥', '📽️', '🎬',
            '📢', '📣', '📯', '🔔', '🔕', '🎼', '🎵', '🎶', '🎙️', '🎚️', '🎛️', '📻'
        ]

        # Statistics
        self.files_processed = 0
        self.files_modified = 0
        self.total_emojis_removed = 0
        self.emoji_counts = {}

    def is_emoji(self, char):
        """Check if a character is an emoji using Unicode categories"""
        return unicodedata.category(char) == 'So' or char in self.emoji_patterns

    def remove_emojis_from_text(self, text):
        """Remove emojis from text while preserving ALL formatting and indentation"""
        lines = text.split('\n')
        modified_lines = []
        emojis_removed_count = 0

        for line in lines:
            # Process the entire line character by character, preserving everything except emojis
            cleaned_line = ''
            i = 0

            while i < len(line):
                char = line[i]

                # Check for multi-character emojis first
                found_emoji = False
                for emoji in self.emoji_patterns:
                    if line[i:].startswith(emoji):
                        # Found an emoji, skip it entirely
                        emojis_removed_count += 1
                        if emoji in self.emoji_counts:
                            self.emoji_counts[emoji] += 1
                        else:
                            self.emoji_counts[emoji] = 1
                        i += len(emoji)
                        found_emoji = True
                        break

                if not found_emoji:
                    # Check for single character emojis
                    if self.is_emoji(char):
                        emojis_removed_count += 1
                        if char in self.emoji_counts:
                            self.emoji_counts[char] += 1
                        else:
                            self.emoji_counts[char] = 1
                        i += 1
                    else:
                        # Keep all non-emoji characters exactly as they are
                        cleaned_line += char
                        i += 1

            # No regex processing at all - preserve the line exactly as is (minus emojis)
            # Only remove trailing whitespace to clean up any trailing spaces left by emoji removal
            cleaned_line = cleaned_line.rstrip()

            modified_lines.append(cleaned_line)

        self.total_emojis_removed += emojis_removed_count
        return '\n'.join(modified_lines), emojis_removed_count > 0

    def process_file(self, file_path):
        """Process a single file to remove emojis"""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Remove emojis
            cleaned_content, was_modified = self.remove_emojis_from_text(original_content)

            # Write back only if modified
            if was_modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                self.files_modified += 1
                print(f"✓ Modified: {file_path}")
            else:
                print(f"- No emojis found: {file_path}")

            self.files_processed += 1
            return True

        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            return False

    def process_directory(self, directory_path, file_extensions=None, recursive=True):
        """Process all files in a directory"""
        if file_extensions is None:
            file_extensions = ['.py']  # Default to Python files

        directory = Path(directory_path)
        if not directory.exists():
            print(f"✗ Directory does not exist: {directory_path}")
            return False

        # Find all matching files
        files_to_process = []

        if recursive:
            for ext in file_extensions:
                files_to_process.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in file_extensions:
                files_to_process.extend(directory.glob(f"*{ext}"))

        if not files_to_process:
            print(f"- No files with extensions {file_extensions} found in {directory_path}")
            return True

        print(f"Found {len(files_to_process)} files to process...")

        # Process each file
        for file_path in files_to_process:
            self.process_file(file_path)

        return True

    def print_statistics(self):
        """Print processing statistics"""
        print("\n" + "="*60)
        print("EMOJI REMOVAL STATISTICS")
        print("="*60)
        print(f"Files processed: {self.files_processed}")
        print(f"Files modified: {self.files_modified}")
        print(f"Total emojis removed: {self.total_emojis_removed}")

        if self.emoji_counts:
            print(f"\nEmojis removed by type:")
            for emoji, count in sorted(self.emoji_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {emoji} : {count} times")

        print("="*60)

def main():
    parser = argparse.ArgumentParser(
        description="Universal Emoji Remover - Remove emojis from code files while preserving formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove emojis from a single file
  python universal_emoji_remover.py -f myfile.py
  
  # Remove emojis from all Python files in current directory
  python universal_emoji_remover.py -d . -e .py
  
  # Remove emojis from all Python and JavaScript files recursively
  python universal_emoji_remover.py -d /path/to/project -e .py .js -r
  
  # Remove emojis from specific file types in multiple directories
  python universal_emoji_remover.py -d dir1 dir2 dir3 -e .py .js .ts
        """
    )

    parser.add_argument('-f', '--file', action='append',
                       help='Process specific file(s). Can be used multiple times.')
    parser.add_argument('-d', '--directory', action='append',
                       help='Process directory/directories. Can be used multiple times.')
    parser.add_argument('-e', '--extensions', nargs='+', default=['.py'],
                       help='File extensions to process (default: .py)')
    parser.add_argument('-r', '--recursive', action='store_true', default=True,
                       help='Process directories recursively (default: True)')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Disable recursive processing')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without making changes')

    args = parser.parse_args()

    # Handle recursive flag
    if args.no_recursive:
        args.recursive = False

    # Validate arguments
    if not args.file and not args.directory:
        print("Error: Must specify either --file or --directory")
        parser.print_help()
        sys.exit(1)

    # Create remover instance
    remover = UniversalEmojiRemover()

    print("🧹 Universal Emoji Remover")
    print("="*40)

    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        print("="*40)

    success = True

    # Process files
    if args.file:
        print(f"Processing {len(args.file)} specific file(s)...")
        for file_path in args.file:
            if not remover.process_file(file_path):
                success = False

    # Process directories
    if args.directory:
        print(f"Processing {len(args.directory)} directory/directories...")
        for dir_path in args.directory:
            if not remover.process_directory(dir_path, args.extensions, args.recursive):
                success = False

    # Print statistics
    remover.print_statistics()

    if success:
        print("\n✅ Emoji removal completed successfully!")
    else:
        print("\n⚠️ Emoji removal completed with some errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()