import os
import shutil
from datetime import datetime
from typing import (
    Iterable,
    List,
    Optional,
    cast,
)

from src.constants import ATTACHMENTS_FOLDER
from src.logger import logger
from src.metadata import Note
from src.report import read_report_csv


class MoveDuplicateFileError(Exception):
    """The file to move already exists."""


class EvernoteMove:
    """Evernote Move Class."""

    notebook_path: str
    dest_path: str
    dest_attachments_path: str
    report_path: str
    date_updated: Optional[datetime]
    """Date of update threshold."""

    def __init__(
        self,
        notebook_path: str,
        dest_path: str,
        report_path: str,
        date_updated: Optional[datetime],
    ) -> None:
        """
        Constructor.

        Args:
            notebook_path (str): The path to the notebook to move notes from.
            dest_path (str): The path to the destination folder where to move the notes.
            report_path (str): The path to the report.
            date_updated (Optional[datetime]): The date of update after which the notes should be moved (inclusive).
        """
        self.notebook_path = notebook_path
        self.dest_path = dest_path
        self.dest_attachments_path = os.path.join(self.dest_path, ATTACHMENTS_FOLDER)
        self.report_path = report_path
        self.date_updated = date_updated

    def process(self) -> None:
        """Move some notes of a notebook."""
        notebook_notes = read_report_csv(self.report_path)
        notes: List[Note] = self._filter_notes(notebook_notes)

        # Create the destination folder
        if not os.path.exists(self.dest_path):
            os.mkdir(self.dest_path)

        if not os.path.exists(self.dest_attachments_path):
            os.mkdir(self.dest_attachments_path)

        # Move the notes
        count = 0
        for note in notes:
            if self._move_note(note):
                count += 1

        logger.info(f'Number of notes moved: {count}')

    def _filter_notes(
        self,
        notes: List[Note],
    ) -> List[Note]:
        partition: Iterable[Note] = notes

        if self.date_updated:
            # Keep notes updated after the given date
            partition = filter(
                lambda r: r.body.date_updated and r.body.date_updated >= cast(datetime, self.date_updated),
                partition,
            )

        return list(partition)

    def _move_note(
        self,
        note: Note,
    ) -> bool:
        """
        Move a note.

        Args:
            note (Note): The note to move.

        Returns:
            bool: Whether the note was moved or not.
        """
        if moved := self._move_file(
            os.path.join(self.notebook_path, note.body.name),
            os.path.join(self.dest_path, note.body.name),
        ):
            logger.info(f'Moved note `{note.body.name}`')

        # Even-though no notes were moved, try to move the attachment
        # to continue after an unexpected failure during a previous move operation.
        for attachment in note.attachments:
            if self._move_file(
                os.path.join(self.notebook_path, ATTACHMENTS_FOLDER, attachment.name),
                os.path.join(self.dest_attachments_path, attachment.name),
            ):
                logger.info(f'Moved attachment `{attachment.name}`')

        return moved

    def _move_file(
        self,
        source_path: str,
        dest_path: str,
    ) -> bool:
        """
        Move a file.

        Args:
            source (str): The path to the source file.
            dest (str): The path to the destination file.

        Returns:
            bool: Whether the file was moved or not.
        """
        # Ignore non-existing files,
        # to allow continue from a previous non-completed move,
        # or from a move with an overlapping filter.
        if os.path.exists(source_path):
            if os.path.exists(dest_path):
                raise MoveDuplicateFileError(dest_path)

            shutil.move(source_path, dest_path)

            return True

        return False
