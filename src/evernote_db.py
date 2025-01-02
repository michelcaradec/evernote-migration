import sqlite3
from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

from src.converters import normalize_string
from src.logger import logger

# For use with https://typing.python.org/en/latest/guides/writing_stubs.html#the-any-trick
MaybeNone = Any


@dataclass
class NoteID:
    """Evernote Note Identifier Class."""

    id: str
    """Identifier of the note."""
    date_created: Optional[datetime]
    """Date of creation of the note."""


class EvernoteDB:
    """Evernote Database Class."""

    __conn: Union[sqlite3.Connection, MaybeNone] = None
    __is_finalized: bool = False
    """Whether the Evernote database has been scanned or not."""
    _map_title_2_id: Dict[str, List[NoteID]] = {}
    """[Note title => Evernote ID]"""
    __map_id_2_container: Dict[str, str] = {}
    """[Evernote ID => Note container]"""

    def __init__(
        self,
        database: str = '',
    ) -> None:
        """
        Constructor.

        Args:
            database (str): The path to the Evernote local database.
        """
        if database:
            self.__conn = sqlite3.connect(
                database,
                # No transaction isolation
                isolation_level=None,
                # Open database as read-only
                uri=True,
            )
            self.__conn.row_factory = sqlite3.Row

    def __del__(self) -> None:
        """Destructor."""
        if self.__conn:
            self.__conn.close()
            self.__conn = None

    @property
    def is_connected(self) -> bool:
        """Whether a connection to the database is established or not."""
        return True if self.__conn else False

    def __finalize(self) -> None:
        if not self.is_connected:
            raise ConnectionError()

        if self.__is_finalized:
            return

        cursor: sqlite3.Cursor = self.__conn.execute('SELECT id, label, created FROM Nodes_Note where deleted IS NULL')
        rows: List[sqlite3.Row] = cursor.fetchall()
        for row in rows:
            title = normalize_string(row['label'])
            note_id = NoteID(
                row['id'],
                datetime.fromtimestamp(
                    int(row['created']) // 1_000,
                    timezone.utc,
                ),
            )

            if ids := self._map_title_2_id.get(title):
                # There may be notes with duplicate names
                ids.append(note_id)
            else:
                self._map_title_2_id[title] = [note_id]

        cursor.close()

        self.__is_finalized = True

    def get_id_from_note(
        self,
        title: Optional[str],
        date_created: Optional[datetime],
    ) -> Optional[str]:
        """
        Get the Evernote identifier of a note.

        Args:
            title (Optional[str]): The title of the note.
            date_created (Optional[datetime]): The date of creation of the note.
                Used to disambiguate notes with duplicate names.

        Returns:
            Optional[str]: The Evernote identifier of a note.
        """
        if not title:
            return None

        self.__finalize()

        if note_ids := self._map_title_2_id.get(title):
            if len(note_ids) == 1:
                return note_ids[0].id
            elif date_created:
                # Disambiguate notes with duplicate names with the date of creation
                candidates = [n for n in note_ids if n.date_created and n.date_created == date_created]
                if len(candidates) == 1:
                    return candidates[0].id

                logger.warning(f'Ambiguous not title `{title}`')
            else:
                logger.warning(f"Note ID not found for `{title}` (can't disambiguate)")
        else:
            logger.warning(f'Note ID not found for `{title}`')

        return None

    def add_container_id(
        self,
        container: str,
        id: str,
    ) -> None:
        """
        Reference a container.

        Args:
            container (str): The name of the container (i.e. the note filename).
            id (str): The Evernote identifier of the container.
        """
        self.__map_id_2_container[id] = container

    def get_container_from_id(
        self,
        id: str,
    ) -> Optional[str]:
        """
        Get the container from an Evernote identifier.

        Args:
            id (str): The Evernote identifier.
        """
        return self.__map_id_2_container.get(id)
