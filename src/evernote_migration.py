import os
import shutil
import uuid
from functools import reduce
from glob import glob
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
)

from src.constants import (
    ATTACHMENTS_FOLDER,
    NOTE_EXTENSION,
)
from src.converters import (
    standardize_note_name,
    standardize_tags,
)
from src.evernote_db import EvernoteDB
from src.extractors import (
    REGEX_FILE,
    REGEX_IMAGE,
    REGEXES_NOTE_LINK,
    extract_notes_links,
)
from src.logger import logger
from src.metadata import (
    AttachmentMetadata,
    NoteMetadata,
    get_attachment_metadata,
    get_note_metadata,
)
from src.persist import (
    load_note_content,
    save_note_content,
)
from src.report import add_report_csv

_NOTE_FILENAME = 'README.md'


class EvernoteMigration:
    """Evernote Migration Class."""

    notebook_path: str
    evernote_db: EvernoteDB
    report_path: Optional[str]
    report_only: bool
    keep: bool
    overwrite: bool

    def __init__(
        self,
        notebook_path: str,
        evernote_db: EvernoteDB,
        report_path: Optional[str] = None,
        report_only: bool = False,
        keep: bool = False,
        overwrite: bool = False,
    ) -> None:
        """
        Constructor.

        Args:
            notebook_path (str): The path to the notebook containing the notes.
            evernote_db (EvernoteDB): The Evernote local database.
            report_path (Optional[str]): The path to the report.
            report_only (bool): Whether a report should be generated without the notes or not.
            keep (bool): Whether the original notes should be kept or deleted.
            overwrite (bool): Whether the notes with duplicate names should be overwritten or created with a new name.
        """
        self.notebook_path = notebook_path
        self.evernote_db = evernote_db
        self.report_path = report_path
        self.report_only = report_only
        self.keep = keep
        self.overwrite = overwrite

    def _get_note_filename(
        self,
        note_folder: str,
    ) -> str:
        """
        Get the path of a single note file.

        Args:
            note_folder (str): The folder of the note.
        """
        note_name = standardize_note_name(note_folder)
        count = 0
        while os.path.exists(
            note_path := os.path.join(
                self.notebook_path,
                note_name,
            )
            + NOTE_EXTENSION
        ):
            if self.overwrite:
                break

            count += 1
            note_name += f'-{count}'

        return note_path

    def _standardize_note(
        self,
        note_folder: str,
    ) -> Tuple[NoteMetadata, List[AttachmentMetadata]]:
        """
        Standardize a note.

        - Convert the names of the assets to UUIDs.
        - Copy the assets to the attachments folder.
        - Copy the converted note under the notebook folder.

        Args:
            note_folder (str): The folder of the note.

        Returns:
            Tuple[NoteMetadata, List[AttachmentMetadata]]
        """
        # Read the content of the original note
        note_path = os.path.join(self.notebook_path, note_folder)

        content = load_note_content(os.path.join(note_path, _NOTE_FILENAME))

        attachments_metadata: List[AttachmentMetadata] = []

        # Scan the content of the note for local assets
        for regex in [REGEX_FILE, REGEX_IMAGE]:
            attachments: Dict[str, str] = {}

            matches = list(regex.finditer(content))

            # Process the matches in reverse order to prevent position shift when replacing the name of the assets
            for match in matches[::-1]:
                asset_path = match['path']

                if not (asset_path_new := attachments.get(asset_path)):
                    # First-time attachment reference
                    # Set the name of the attachment to a UUID format
                    _, ext = os.path.splitext(os.path.basename(asset_path))
                    asset_name = f'{uuid.uuid4()}{ext}'
                    asset_path_new = os.path.join(ATTACHMENTS_FOLDER, asset_name)

                    if not self.report_only:
                        # Copy the attachment to the new place
                        shutil.copy(
                            os.path.join(note_path, asset_path),
                            os.path.join(self.notebook_path, asset_path_new),
                        )

                    # Keep the migrated attachment details for later reuse
                    attachments[asset_path] = asset_path_new

                    attachments_metadata.append(
                        get_attachment_metadata(
                            asset_name,
                            os.path.join(note_path, asset_path),
                        ),
                    )

                # Update the reference to the attachment
                pos_begin, pos_end = match.span('path')
                content = content[:pos_begin] + asset_path_new + content[pos_end:]

        content = standardize_tags(content)

        # Set the new name of the note
        single_note_path = self._get_note_filename(note_folder)
        if not self.report_only:
            # Copy the note to the new place
            save_note_content(
                single_note_path,
                content,
            )

        note_metadata = get_note_metadata(
            os.path.basename(single_note_path),
            content,
        )
        if self.evernote_db.is_connected:
            note_metadata.id = self.evernote_db.get_id_from_note(
                note_metadata.title,
                note_metadata.date_created,
            )
            container = os.path.basename(single_note_path)
            if note_metadata.id:
                # Register the ID of the migrated note filename (i.e. container)
                self.evernote_db.add_container_id(
                    container,
                    note_metadata.id,
                )
            else:
                logger.warning(f'Note ID not found for container `{container}`')

        return (note_metadata, attachments_metadata)

    def process(self) -> None:
        """Standardize a notebook."""
        # Create the folder for attachments
        attachments_path = os.path.join(self.notebook_path, ATTACHMENTS_FOLDER)
        if not self.report_only and not os.path.exists(attachments_path):
            os.mkdir(attachments_path)

        # Start from a fresh report
        if self.report_path and os.path.exists(self.report_path):
            os.remove(self.report_path)

        # Scan the notes (one note per folder) and convert them
        folders = {d for d in next(os.walk(self.notebook_path))[1]} - {ATTACHMENTS_FOLDER}
        for folder in folders:
            # Process the note
            logger.info(f'Migrate note `{folder}`')

            (
                note_metadata,
                attachments_metadata,
            ) = self._standardize_note(folder)

            if self.report_path:
                add_report_csv(
                    self.report_path,
                    note_metadata,
                    attachments_metadata,
                )

            if not self.report_only and not self.keep:
                # Remove the original (processed) notes
                logger.info(f'Delete folder `{folder}`')

                shutil.rmtree(
                    os.path.join(self.notebook_path, folder),
                    ignore_errors=True,
                )

        if not self.report_only:
            # Scan the converted notes (one note per file)
            self._process_note_links()
            self._process_backlinks()

    def _process_note_links(self) -> None:
        if not self.evernote_db.is_connected:
            return

        logger.info('Process notes links')

        note_files = glob(os.path.join(self.notebook_path, '*.md'))
        for note_path in note_files:
            is_dirty = False
            content = load_note_content(note_path)

            for regex in REGEXES_NOTE_LINK:
                matches = list(regex.finditer(content))

                # Process the matches in reverse order to prevent position shift when replacing the note link
                for match in matches[::-1]:
                    id = match['id']
                    if not (single_note_path := self.evernote_db.get_container_from_id(id)):
                        logger.warning(
                            f'Container of `{match["label"]}` not found'
                            f' for note ID `{id}` ({os.path.basename(note_path)})'
                        )
                        continue

                    # Update the reference to the note
                    pos_begin, pos_end = match.span('url')
                    content = content[:pos_begin] + './' + single_note_path + content[pos_end:]
                    is_dirty = True

            if is_dirty and not self.report_only:
                save_note_content(
                    note_path,
                    content,
                )

    def _process_backlinks(self) -> None:
        if not self.evernote_db.is_connected:
            return

        logger.info('Process backlinks')

        # Backlinks to add (notes -> [backlink])
        map_backlinks: Dict[str, List[str]] = {}

        note_files = glob(os.path.join(self.notebook_path, '*.md'))
        for note_path in note_files:
            content = load_note_content(note_path)
            containers = [os.path.basename(c) for c in extract_notes_links(content)]

            for container in containers:
                note_name = os.path.basename(note_path)

                if linked_notes := map_backlinks.get(container):
                    linked_notes.append(note_name)
                else:
                    map_backlinks[container] = [note_name]

        for container, backlinks in map_backlinks.items():
            note_path = os.path.join(self.notebook_path, container)
            content = load_note_content(note_path)
            content = self._inject_backlinks(backlinks, content)
            save_note_content(note_path, content)

        backlinks_count = reduce(
            lambda x, y: x + len(y),
            map_backlinks.values(),
            0,
        )
        logger.info(f'Created {backlinks_count} backlinks from {len(map_backlinks)} links')

    def _inject_backlinks(
        self,
        backlinks: List[str],
        content: str,
    ) -> str:
        content += '\n---\n\n'
        content += '## Backlinks\n\n'

        backlinks_md = [f'- [{os.path.splitext(backlink)[0]}](./{backlink})\n' for backlink in backlinks]
        content += ''.join(backlinks_md)

        return content
