import os
from dataclasses import dataclass
from datetime import datetime
from typing import (
    List,
    Optional,
)

from src.extractors import (
    REGEX_DATE,
    REGEX_UPDATED_AT,
    extract_date,
    extract_title,
    extract_url,
)


@dataclass
class NoteMetadata:
    """Note metadata."""

    id: Optional[str]
    """Evernote identifier of the note."""
    name: str
    """Physical name of the note."""
    title: Optional[str]
    """Name (title) of the note."""
    size: int
    url: Optional[str]
    date_created: Optional[datetime]
    date_updated: Optional[datetime]


def get_note_metadata(
    name: str,
    content: str,
) -> NoteMetadata:
    """
    Extract the metadata from a note.

    Args:
        name (str): The name of the note.
        content (str): The content of the note.
    """
    return NoteMetadata(
        id=None,
        name=name,
        title=extract_title(content),
        size=len(content),
        url=extract_url(content),
        date_created=extract_date(REGEX_DATE, content),
        date_updated=extract_date(REGEX_UPDATED_AT, content),
    )


@dataclass
class AttachmentMetadata:
    """Attachment metadata."""

    name: str
    size: int


def get_attachment_metadata(
    name: str,
    attachment_path: str,
) -> AttachmentMetadata:
    """
    Extract the metadata from an attachment.

    Args:
        name (str): The name of the attachment.
        attachment_path (str): The path to the attachment.
    """
    return AttachmentMetadata(
        name=name,
        size=os.path.getsize(attachment_path),
    )


@dataclass
class Note:
    """Note."""

    body: NoteMetadata
    attachments: List[AttachmentMetadata]
