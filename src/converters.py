import re
import unicodedata

_PATTERN_LEADING_DASH = r'^-*(?P<name>.+)$'
_REGEX_LEADING_DASH: re.Pattern[str] = re.compile(_PATTERN_LEADING_DASH)

_PATTERN_TAGS = r'^tags:\s*\[(?P<tags>[^\]]+)\]$'
_REGEX_TAGS: re.Pattern[str] = re.compile(_PATTERN_TAGS, re.MULTILINE)


def standardize_note_name(name: str) -> str:
    """Fix the name of a note."""
    return (
        _REGEX_LEADING_DASH.sub(r'\g<name>', name)  # Strip leading dash
        .replace('"', '')  # Strip double-quotes
        .replace("'", '')  # Strip single-quotes
        .replace('/', '-')  # Replace slashes by dashes
        .replace('?', '')  # Strip question marks
        .replace('!', '')  # Strip exclamation marks
    )


def _standardize_tag(tag: str) -> str:
    """Standardize a tag."""
    return (
        tag.replace('-', '')  # Strip dashes
        .replace('_', '')  # Strip underscores
        .lower()  # Lower case
    )


def standardize_tags(content: str) -> str:
    """
    Standardize the list of tags of a note.

    Args:
        content (str): The content of the note.

    Returns:
        str: The updated content of the note.
    """
    if match := _REGEX_TAGS.search(content):
        tags = map(
            lambda t: t.strip().strip("'"),
            match['tags'].split(','),
        )
        for tag in tags:
            if (tag_new := _standardize_tag(tag)) != tag:
                content = content.replace(f'#{tag}', f'#{tag_new}')

    return content


def normalize_string(text: str) -> str:
    """
    Normalize a string.

    - Replacement of accented characters by their non-accented equivalent.
    - Conversion of Unicode escaped characters.

    Args:
        text (str): The string to normalize.

    Returns:
        str: The normalized string.
    """
    # Normalize the string
    normalized = ''.join([c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)])
    # Convert Unicode escapes
    unescaped = normalized.encode('utf-8').decode('unicode_escape')

    return unescaped
