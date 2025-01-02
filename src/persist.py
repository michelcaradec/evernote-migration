def load_note_content(note_path: str) -> str:
    """
    Load the content of a note.

    Args:
        note_path (str): The path to the note.
    """
    with open(
        note_path,
        'r',
        errors='surrogateescape',
    ) as file:
        content = file.read()

    return content


def save_note_content(
    note_path: str,
    content: str,
) -> None:
    """
    Save the content of a note.

    Args:
        note_path (str): The path to the note.
        content (str): The content of the note.
    """
    with open(
        note_path,
        'w',
        errors='surrogateescape',
    ) as file:
        file.write(content)
