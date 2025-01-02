import csv
from datetime import datetime
from typing import (
    List,
    Optional,
)
from src.metadata import (
    Note,
    NoteMetadata,
    AttachmentMetadata,
)

_DATETIME_FORMAT = r'%Y-%m-%d %H:%M:%S'

_COL_NOTE_ID = 0
_COL_NOTE_NAME = _COL_NOTE_ID + 1
_COL_NOTE_TITLE = _COL_NOTE_NAME + 1
_COL_NOTE_DATE_CREATED = _COL_NOTE_TITLE + 1
_COL_NOTE_DATE_UPDATED = _COL_NOTE_DATE_CREATED + 1
_COL_NOTE_SIZE = _COL_NOTE_DATE_UPDATED + 1
_COL_ATTACHMENT_NAME = _COL_NOTE_SIZE + 1
_COL_ATTACHMENT_SIZE = _COL_ATTACHMENT_NAME + 1


def _format_datetime(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime(_DATETIME_FORMAT) if dt else None


def add_report_csv(
    report_path: str,
    note_metadata: NoteMetadata,
    attachments_metadata: List[AttachmentMetadata],
) -> None:
    """
    Add information on the note to a CSV report.

    Headers:

    - Identifier of the note.
    - Name of the note.
    - Title of the note.
    - Date of creation of the note.
    - Date of update of the note.
    - Size of the note (without the attachments).
    - Name of the attachment.
    - Size of the attachment.

    There are as many lines per note as there are some attachments.  
    There is only one line for notes without attachments.

    Args:
        report_path (str): The path to the CSV report.
        note_metadata (NoteMetadata): The metadata of the note.
        attachments_metadata (List[AttachmentMetadata]): The metadata of the attachments.
    """
    with open(report_path, 'a') as file:
        writer = csv.writer(file)

        if not attachments_metadata:
            writer.writerow(
                (
                    note_metadata.id,
                    note_metadata.name,
                    note_metadata.title,
                    _format_datetime(note_metadata.date_created),
                    _format_datetime(note_metadata.date_updated),
                    note_metadata.size,
                    None,
                    None,
                )
            )
        else:
            for attachment_metadata in attachments_metadata:
                writer.writerow(
                    (
                        note_metadata.id,
                        note_metadata.name,
                        note_metadata.title,
                        _format_datetime(note_metadata.date_created),
                        _format_datetime(note_metadata.date_updated),
                        note_metadata.size,
                        attachment_metadata.name,
                        attachment_metadata.size,
                    )
                )


def _get_note_metadata_from_line(line: List[str]) -> NoteMetadata:
    return NoteMetadata(
        id=line[_COL_NOTE_ID],
        name=line[_COL_NOTE_NAME],
        title=line[_COL_NOTE_TITLE],
        size=int(line[_COL_NOTE_SIZE]),
        url=None,
        date_created=datetime.strptime(line[_COL_NOTE_DATE_CREATED], _DATETIME_FORMAT),
        date_updated=datetime.strptime(line[_COL_NOTE_DATE_UPDATED], _DATETIME_FORMAT),
    )


def _get_attachment_metadata_from_line(line: List[str]) -> Optional[AttachmentMetadata]:
    return AttachmentMetadata(
        line[_COL_ATTACHMENT_NAME],
        int(line[_COL_ATTACHMENT_SIZE]),
    ) if line[_COL_ATTACHMENT_NAME] else None


def read_report_csv(report_path: str) -> List[Note]:
    """
    Read a CSV report.

    Args:
        report_path (str): The path to the CSV report.

    Returns:
        List[Note]: The nodes information.
    """
    notes: List[Note] = []
    note: Optional[Note] = None

    with open(report_path, 'r') as file:
        reader = csv.reader(file)

        for line in reader:
            attachment: Optional[AttachmentMetadata] = _get_attachment_metadata_from_line(line)

            if not note or note.body.name != line[_COL_NOTE_NAME]:
                if note:
                    # Add the completed note
                    notes.append(note)
                # Create a new note
                note = Note(
                    _get_note_metadata_from_line(line),
                    [],
                )

            if attachment:
                note.attachments.append(attachment)

    if note:
        # Add the last completed report item
        notes.append(note)

    return notes
