# Evernote Migration

A tool to migrate Evernote notes to a Git repository.

<details>
<summary>Table of contents</summary>

- [Abstract](#abstract)
- [Setup](#setup)
  - [Python Environment](#python-environment)
  - [Evernote2MD](#evernote2md)
  - [GitHub CLI](#github-cli)
- [Usage](#usage)
- [Annexes](#annexes)
  - [Split Strategy](#split-strategy)
  - [Migration Report Analysis](#migration-report-analysis)
  - [Evernote Backup](#evernote-backup)
  - [NotesHub](#noteshub)
  - [Motivations For Leaving Evernote](#motivations-for-leaving-evernote)

</details>

## Abstract

As a long time [^2] [Evernote](https://www.evernote.com/) subscribed user, came the moment where I wanted to [escape](#motivations-for-leaving-evernote) from the [vendor lock-in](https://en.wikipedia.org/wiki/Vendor_lock-in), by having all my notes in Markdown format, stored on a standard repository such as [GitHub](https://github.com/).

The ultimate plan is to replace the Evernote client by [NotesHub](https://about.noteshub.app/), which has a clear separation between the application and the storage (meaning that I can manipulate my notes even with a simple Git client).

This project relies on existing tools, such as [evernote2md](https://github.com/wormi4ok/evernote2md) to convert the Evernote notes to the Markdown format.

A [Python script](./src/) has been created to reorganize the notes, and deal with issues such as:

- Valid name of the notes.
- Valid name of the tags.
- Duplicate note names.
- Duplicate attachments (i.e. different notes with an attachment having the same name).
- Recycled attachments (i.e. notes referencing multiple times the same attachment).
- Attachments located in multiple places (i.e. images and files).

It was used to migrate more than 2900 notes dispatched in multiple notebooks (for an `.enex` export file size of 883 MB), from a MacOS environment.

**Disclaimer**: this project was done for my personal needs. As this is a "run once" tool, **I do not plan to maintain it**. Please feel free to improve it by forking it.

[^2]: My first note was created on 2009-11-15, and was about [Semiotics](https://en.wikipedia.org/wiki/Semiotics).

## Setup

### Python Environment

Create a Python virtual environment using [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

### Evernote2MD

Download the latest release of [evernote2md](https://github.com/wormi4ok/evernote2md) from <https://github.com/wormi4ok/evernote2md/releases> and place it under the folder [./bin](./bin/).

Tested version: `0.21.0`.

### GitHub CLI

Download the latest release of [GitHub CLI](https://cli.github.com/) from <https://github.com/cli/cli/releases> and place it under the folder [bin](./bin/).

Tested version: `2.64.0 (2024-12-20)`.

## Usage

For **each** notebook:

1. Export the notebook from the Evernote client and place it under the folder [exports](./exports/).  
   *The [online backup](#evernote-backup) of the Evernote notebooks was considered, and abandoned due to various limitations such as stability and rate limits.*
2. Go to this project root folder.
3. Create a local folder for the notebook:

    ```bash
    NOTEBOOKS_FOLDER=notebooks
    # Name of the notebook folder / repository
    NOTEBOOK_FOLDER=notes-inbox

    mkdir -p "${NOTEBOOKS_FOLDER}/${NOTEBOOK_FOLDER}"
    ```

4. Convert the exported notebook to Markdown notes:

    ```bash
    # Name of the notebook export file
    NOTEBOOK_EXPORT="Inbox.enex"

    ./bin/evernote2md \
        --folders \
        --tagTemplate "#{{tag}}" \
        --addFrontMatter \
        --outputDir "${NOTEBOOKS_FOLDER}/${NOTEBOOK_FOLDER}" \
        "./exports/${NOTEBOOK_EXPORT}"
    ```

    *It takes around 3 minutes to convert 2832 notes from an `.enex` export file of 558 MB on a MacBook Pro 2013.*

    - A dedicated folder will be created for each note (argument `--folders`).
    - The tags will be added with a leading hash under the title of the notes (argument `--tagTemplate "#{{tag}}"`).
    - The metadata will be added at the top of the notes, enclosed in markers `---` (argument `--addFrontMatter`, see <https://jekyllrb.com/docs/front-matter/>).
    - Each exported note will be placed under the notebook folder (argument `--outputDir`) in a Markdown file named `README.md`.

5. Migrate the notes:

    ```bash
    PYTHONPATH=. python src/main.py \
        migrate \
        --folder "${NOTEBOOKS_FOLDER}/${NOTEBOOK_FOLDER}" \
        --evernote-db "${EVERNOTE_DB}" \
        --report "${NOTEBOOK_FOLDER}.csv"
    ```

    - Each converted note will be copied under the notebook folder (argument `--folder`) in a Markdown file.
    - The renamed attachments will be copied under the folder `.attachments`.
    - The [note links](https://help.evernote.com/hc/en-us/articles/208313588-Note-links) will be migrated and backlinks will be generated if the argument `--evernote-db` with the path to the Evernote local database is provided.  
        The local database (which is a [SQLite](https://www.sqlite.org/) one) is available on machines where the Evernote client has been installed (Windows or MacOS):

        - On MacOS: `/Users/${USERNAME}/Library/Application Support/Evernote/conduit-storage/https%3A%2F%2Fwww.evernote.com/UDB-User${EVERNOTE_USER_ID}+RemoteGraph.sql`.
        - On Windows: `C:\Users\${USERNAME}\AppData\Roaming\Evernote\conduit-storage\https%3A%2F%2Fwww.evernote.com\UDB-User${EVERNOTE_USER_ID}+RemoteGraph.sql`.

        The local database is required to convert the notes identifiers to the migrated notes filenames.

        Reasons of note links migration failure:

        - Link to a note located in another notebook.
        - Link to a note having a duplicate name (this would require Evernote to include the identifiers in the `.enex` export).

    - The CSV report (argument `--report`) contains the details of the migrated notes and attachments:  
        It can be used to [split](#split-strategy) one notebook into multiple ones (command `move`).

        Structure (headers):

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

    - Use the argument:
      - `--keep` to prevent deleting the original notes folders (essentially for post-migration check).
      - `--overwrite` to ignore duplicate single note file names, and overwrite them.
      - `--report-only` to generate a report without migrating notes (dry-run).  
        **Attention!** In this mode, the generated report will not be useable for the `move` operations, as the generated attachments names will be fictitious.

6. Create the **remote** notebook repository:

    ```bash
    # https://cli.github.com/manual/gh_auth_login
    ./bin/gh auth login --with-token < .token.txt
    # https://cli.github.com/manual/gh_repo_create
    ./bin/gh repo create "${NOTEBOOK_FOLDER}" --private
    ```

    The file `.token.txt` must contain the GitHub token with the required credentials to create a repository.

7. Go to the notebook folder:

    ```bash
    cd "${NOTEBOOKS_FOLDER}/${NOTEBOOK_FOLDER}"
    ```

8. Create the **local** notebook repository:

    ```bash
    git init --initial-branch=main
    ```

9. **Configure** the notebook repository:

    ```bash
    git remote add origin https://${ACCESS_TOKEN_REPO}@github.com/${GITHUB_USER}/${NOTEBOOK_FOLDER}.git
    ```

    **Attention!**

    - The environment variables must be replaced by their values before executing the command.  
        Example:

        ```bash
        git remote add origin https://41391B3F-13B8-46DC-8B75-F5814FB1BECF@github.com/michelcaradec/notes-inbox.git
        ```

        Where:

        - `41391B3F-13B8-46DC-8B75-F5814FB1BECF` is the GitHub token.
        - `michelcaradec` is the name of the GitHub account.
        - `notes-inbox` is the name of the notebook repository.

    - Add a space character before the command to prevent storing it in the history.

10. Add all files **at once**:

    ```bash
    git add .
    git commit -m "Initial commit"
    git push -u origin main
    ```

    As an alternative (in case of rate limits issues with GitHub), add the files by **batches**:

    ```bash
    bash ../../scripts/git-add-batch.sh
    ```

11. Go back to the project root folder:

    ```bash
    cd -
    ```

## Annexes

### Split Strategy

A migrated notebook can be split in multiple ones to allow smaller notebook repositories [^1], by using the argument `--date-updated` of the operation `move`.

Let's consider a notebook named "notes-all" that we want to split in three notebooks:

- "notes-hot": notes updated after 2025-01-01.
- "notes-warm": notes updated after 2024-01-01.
- "notes-cold": the rest of the notes.

Workflow:

**Attention!**

- Before proceeding, the notebook must have been migrated with the operation `migrate`.
- If the notes were migrated with the argument `--evernote-db`, the migrated note links and generated backlinks will **break** for links between notes dispatched over different notebooks.

1. Move the notes to the notebook "notes-hot":

    ```bash
    PYTHONPATH=. python src/main.py \
        move \
        --folder "${NOTEBOOKS_FOLDER}/notes-all" \
        --dest "${NOTEBOOKS_FOLDER}/notes-hot" \
        --report "notes-all.csv" \
        --date-updated "2025-01-01"
    ```

    The notes updated **after** 2025-01-01 (argument `--date-updated`, inclusive) will be **moved** from the source notebook folder (argument `--folder`) to the destination folder `notes-hot` (argument `--folder`).  
    The CSV report (argument `--report`) contains the details of the notes and attachments to move.

2. Move the notes to the notebook "notes-warm":

    ```bash
    PYTHONPATH=. python src/main.py \
        move \
        --folder "${NOTEBOOKS_FOLDER}/notes-all" \
        --dest "${NOTEBOOKS_FOLDER}/notes-warm" \
        --report "notes-all.csv" \
        --date-updated "2024-01-01"
    ```

    The notes updated **after** 2024-01-01 (inclusive) will be **moved** to the folder `notes-warm`.  
    This theoretically includes the notes updated after 2025-01-01, but since they were moved during the previous step, they will not be present in the folder `notes-all`, and as a consequence will be **ignored**.

3. Move the notes to the notebook "notes-cold":

    ```bash
    PYTHONPATH=. python src/main.py \
        move \
        --folder "${NOTEBOOKS_FOLDER}/notes-all" \
        --dest "${NOTEBOOKS_FOLDER}/notes-cold" \
        --report "notes-all.csv"
    ```

    The remaining notes (i.e. the ones not moved during the previous steps) will be **moved** to the folder `notes-cold`.  
    Note no argument `--date-updated` was specified.

Such strategy can be defined from insights taken from the [migration report analysis](#migration-report-analysis).

[^1]: See the remarks on large notebook repository in [NotesHub](#noteshub).

### Migration Report Analysis

The CSV report generated at migration time (using the argument `--report`) contains metrics which can be analyzed.

One way is by using [DuckDB](https://duckdb.org/):

1. Go to the DuckDB Shell by navigating to the URL <https://shell.duckdb.org/>.
2. Upload the CSV report with the command:

    ```shell
    .files add
    ```

    A file picker will open, from which you can select the local CSV report file.

    *The list of uploaded files can be displayed with the command `.files list`.*

3. Create a table:  
    *Assuming that the file added was named `notes.csv`.*

    ```sql
    CREATE TABLE notes AS
    SELECT
    *
    FROM
    read_csv(
      'notes.csv',
      header = false,
      columns = {
        'id': 'VARCHAR',
        'note': 'VARCHAR',
        'title': 'VARCHAR',
        'date_created': 'DATETIME',
        'date_updated': 'DATETIME',
        'size': 'INTEGER',
        'attach_name': 'VARCHAR',
        'attach_size': 'INTEGER',
      }
    );
    ```

    *The table can be removed with the command `DROP TABLE IF EXISTS notes;`.*

4. Get the top-10 attachments:

    ```sql
    SELECT
      note,
      attach_name,
      (attach_size / 1024 / 1024)::INTEGER AS attach_size_mb
    FROM notes
    ORDER BY attach_size DESC
    LIMIT 10;
    ```

5. Get the types of attachments:

    ```sql
    SELECT
        DISTINCT lower(string_split(attach_name, '.')[2]) AS ext,
    FROM notes;
    ```

6. Get the top-5 attachments per type of attachment (3 biggest groups):

    ```sql
    SELECT
        ext,
        (attach_size / 1024)::INTEGER AS attach_size_kb
    FROM (
        SELECT
            lower(string_split(attach_name, '.')[2]) AS ext,
            unnest(arg_max(columns('attach_name|attach_size'), attach_size, 5)),
        FROM notes
        WHERE attach_name IS NOT NULL
        GROUP BY ext
        LIMIT 5 * 3
    );
    ```

7. Get the top-5 attachments per type of images (5 biggest groups):

    ```sql
    SELECT
        ext,
        (attach_size / 1024)::INTEGER AS attach_size_kb
    FROM (
        SELECT
            lower(string_split(attach_name, '.')[2]) AS ext,
            unnest(arg_max(columns('attach_name|attach_size'), attach_size, 5)),
        FROM notes
        WHERE
        attach_name IS NOT NULL
        AND ext IN ('jpg', 'jpeg', 'gif', 'png', 'bmp')
        GROUP BY ext
        LIMIT 5 * 5
    );
    ```

8. Get the size of the partitions to create for the [split strategy](#split-strategy):

    ```sql
    SELECT
      'hot' AS notebook,
      ((SUM(size) + SUM(attach_size)) / 1024 / 1024)::INTEGER AS attach_size_mb,
    FROM notes
    WHERE date_updated >= '2025-01-01'
    UNION ALL
    SELECT
      'warm' AS notebook,
      ((SUM(size) + SUM(attach_size)) / 1024 / 1024)::INTEGER AS attach_size_mb,
    FROM notes
    WHERE date_updated BETWEEN '2024-01-01' AND '2025-01-01'
    UNION ALL
    SELECT
      'cold' AS notebook,
      ((SUM(size) + SUM(attach_size)) / 1024 / 1024)::INTEGER AS attach_size_mb,
    FROM notes
    WHERE date_updated < '2024-01-01';
    ```

To know more about DuckDB, check the repository [awesome-duckdb](https://github.com/davidgasquez/awesome-duckdb).

### Evernote Backup

- [evernote-backup: Backup & export all Evernote notes and notebooks](https://github.com/vzhd1701/evernote-backup).

Best practice: prefer the notebook export feature (using [evernote2md](https://github.com/wormi4ok/evernote2md)), as the provided Python script deals with its exported notes.

```bash
uv pip install evernote-backup

evernote-backup init-db --oauth
evernote-backup --verbose sync

# Refresh expired token `evernote-backup reauth`

mkdir ./notes
evernote-backup export --single-notes ./notes/
```

### NotesHub

- [Frequently Asked Questions](https://about.noteshub.app/#faq).

> With the web version of NotesHub due to some limitations of GitHub, we have to proxy all network requests through our CORS proxy servers. In addition, device-auth flow can't be used in the browser and standard web application flow is used instead, which will make a call to our backend to generate the auth token. Taking into account those facts, if you have any concerns regarding this matter, we recommend using native NotesHub application for the maximum protection of your data.
>
> With the native application, you will get more platform-specific features like iCloud Drive support and better integration with the system. Moreover, the web version has a limitation on the size of Git/GitHub notebooks, which is not the case for the native application.

- [Feature Comparison](https://about.noteshub.app/#feature-comparison).

> Large notebooks are considered with a size of more than 5MB.

### Motivations For Leaving Evernote

Beside the [vendor lock-in](https://en.wikipedia.org/wiki/Vendor_lock-in) argument mentioned in the [abstract](#abstract), the main reasons to taking my notes out of Evernote are:

- Lack of Markdown support for writing notes.
- Proprietary storage.
- Many features that I don't use.
- The client on my old MacBook Pro 2013 became incredibly slow over time, as features were added.
- My feature usage coverage compared to the subscription cost is questionable.

I really enjoyed Evernote, and I will definitely miss some of its features, such as tag management, but the benefits are too limited to stop me from replacing it by an alternate (and possibly less sophisticated) solution.

Doing this exercise was also a personal challenge to evaluate the effort required to migrate from a commercial solution. This experiment leads me to think that this is nearly impossible for a non-developer. Even a person with the required skills will have to find the motivation and the time.

I hope this project will be of any help.
