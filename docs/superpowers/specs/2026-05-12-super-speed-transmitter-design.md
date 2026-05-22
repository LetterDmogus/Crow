# Design Spec: Super Speed Transmitter (Crow Transmit)

**Topic:** High-speed folder synchronization using ZIP compression and a temporary PHP bridge for extraction and "Smart Clean".

## 1. Problem Statement
Uploading thousands of small files via FTP is extremely slow due to the overhead of per-file handshakes. Standard sync methods often leave "ghost" files on the server when local files are deleted or renamed.

## 2. Solution: The ZIP-Bridge Pattern
Crow will compress the target directory into a single ZIP file, upload it alongside a temporary PHP script, and trigger the script via HTTP to perform extraction and cleanup.

### 2.1 Workflow
1.  **Pack**: Crow creates a temporary ZIP of the specified local directory.
2.  **Generate**: Crow generates a one-time `crow-bridge.php` with a unique security token.
3.  **Ship**: Both files are uploaded via FTP to the target remote directory.
4.  **Execute**: Crow performs an HTTP GET/POST request to the bridge URL with the token.
5.  **Remote Action (PHP)**:
    - Verifies the token.
    - Scans the target directory for existing files.
    - Extracts the ZIP.
    - **Smart Clean**: Deletes any files in the directory that were NOT present in the ZIP.
    - Returns a JSON status report.
    - **Self-Destruct**: Deletes itself and the ZIP file.
6.  **Report**: Crow displays the results to the user.

## 3. Security
- **One-time Script**: The PHP bridge exists only for the duration of the request.
- **Session Token**: A random 32-character token is hardcoded into the bridge for each session.
- **HTTP/HTTPS**: Uses the site's web URL to trigger the script.

## 4. Components
- `crow/transmitter.py`: Handles local zipping and HTTP orchestration.
- `crow/bridge_template.php`: Template for the server-side worker.
- `crow.transmitter.transmit_folder()`: Main entry point for the command.

## 5. User Interface
Command: `crow transmit <local_dir> [remote_path]`
Example: `crow transmit dist/ /public_html`

## 6. Success Criteria
- [ ] Transfer time for 1000+ files reduced by >80%.
- [ ] No "ghost" files left on server after sync (Smart Clean).
- [ ] PHP bridge and ZIP file are always cleaned up, even on failure.
