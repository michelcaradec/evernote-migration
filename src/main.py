from argparse import (
    Action,
    ArgumentParser,
    Namespace,
)
from datetime import datetime
from typing import Optional

from src.evernote_db import EvernoteDB
from src.evernote_migration import EvernoteMigration
from src.evernote_move import EvernoteMove

_ACTION_MIGRATE = 'migrate'
_ACTION_MOVE = 'move'

class StandaloneArgumentError(Exception):
    """Some arguments can't be used alone."""

    pass


class DateParseAction(Action):
    """DateParseAction class."""

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str,
        option_string: Optional[str] = None,
    ) -> None:
        """Parse an argument representing a date."""
        try:
            dt = datetime.strptime(values, r'%Y-%m-%d')
        except ValueError:
            parser.error(f'Failed to parse {values}' + (f' ({option_string})' if {option_string} else ''))

        setattr(namespace, self.dest, dt)


def _parse_arguments() -> Namespace:
    """Command line arguments parsing."""
    parser = ArgumentParser(description='Evernote Exports Migration.')
    parser.add_argument(
        'action',
        type=str,
        choices=[
            _ACTION_MIGRATE,
            _ACTION_MOVE,
        ],
    )

    migrate_group = parser.add_argument_group('migrate')
    migrate_group.add_argument(
        '--keep',
        action='store_true',
        required=False,
        default=False,
        help='keep the original notes folders',
    )
    migrate_group.add_argument(
        '--overwrite',
        action='store_true',
        required=False,
        default=False,
        help='ignore duplicate single note names (will overwrite existing notes)',
    )
    migrate_group.add_argument(
        '--report-only',
        action='store_true',
        required=False,
        default=False,
        help='generate a report without migrating notes (to be used with --report)',
    )
    
    move_group = parser.add_argument_group('move')
    move_group.add_argument(
        '--dest',
        type=str,
        required=False,
        help='destination folder where to move the notes',
    )
    move_group.add_argument(
        '--date-updated',
        required=False,
        action=DateParseAction,
        help='date of update (YYYY-MM-DD) after which the notes should be moved (inclusive)',
    )

    parser.add_argument(
        '--folder',
        type=str,
        required=True,
        help='folder where the notes are located',
    )
    parser.add_argument(
        '--report',
        type=str,
        required=False,
        help='name of the migration report',
    )
    parser.add_argument(
        '--evernote-db',
        type=str,
        required=False,
        help='path to the Evernote local database',
    )

    return parser.parse_args()


def _check_arguments(args: Namespace) -> None:
    if args.action == _ACTION_MIGRATE:
        if args.report_only and not args.report:
            raise StandaloneArgumentError('--report_only must be used with --report')
    elif args.action == _ACTION_MOVE:
        if not args.report:
            raise ValueError('--report is required')
        if not args.dest:
            raise ValueError('--dest is required')


if __name__ == '__main__':
    args = _parse_arguments()
    _check_arguments(args)

    if args.action == _ACTION_MIGRATE:
        instance = EvernoteMigration(
            args.folder,
            EvernoteDB(args.evernote_db),
            report_path=args.report,
            report_only=args.report_only,
            keep=args.keep,
            overwrite=args.overwrite,
        )
        instance.process()
    elif args.action == _ACTION_MOVE:
        instance = EvernoteMove(
            args.folder,
            args.dest,
            args.report,
            args.date_updated,
        )
        instance.process()
