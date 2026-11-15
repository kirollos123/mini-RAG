## 📌 Progress

### Environment Setup

* ✅ Installed **Miniconda**
* ✅ Created a dedicated **Python 3.10** Conda environment (`mini-rag`)
* ✅ Initialized the local Git repository
* ✅ Connected the project to GitHub

### Terminal Commands

```bash
# Install Miniconda (Ubuntu)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Reload shell
source ~/.bashrc

# Verify installation
conda --version

# Create a Python 3.10 environment
conda create -n mini-rag python=3.10

# Activate the environment
conda activate mini-rag
```

**Reference**

* Miniconda Installation Guide: https://www.anaconda.com/docs/getting-started/miniconda/main

# mini-RAG

mini-RAG is a backend service built with FastAPI that provides the foundational file-ingestion layer for a Retrieval-Augmented Generation (RAG) system. In its current state, it allows a client to upload documents (PDF or plain text) into project-scoped storage on disk, and to process an uploaded file into text chunks using LangChain document loaders and a recursive character text splitter. A MongoDB connection is established at application startup, but no read/write operations against MongoDB are currently implemented in the code shown.

---

## Project Status

**Early-stage / work in progress.**

This project currently implements the *ingestion and chunking* stage of a RAG pipeline — it is not yet a functioning RAG system. There is no embedding generation, no vector storage, no retrieval, and no LLM-based question answering. The MongoDB client is initialized on startup, but it is not used anywhere else in the codebase to persist projects or chunks.

In short: the project can accept a file, save it to disk under a project folder, and split its text content into chunks. Everything beyond that (storage of chunks, retrieval, generation) is not yet built.

---

## Features

Only the following are actually implemented in the current codebase:

- FastAPI REST API with versioned routing (`/api/v1`)
- MongoDB client initialization on app startup/shutdown (connection only, no queries)
- Project-based file storage on the local filesystem (`src/assets/files/{project_id}/`)
- File upload endpoint with async, chunked file writing
- File validation (MIME type and file size, against configured limits)
- PDF and TXT loading via LangChain community document loaders
- Text chunking via LangChain's `RecursiveCharacterTextSplitter`
- Configurable chunk size and overlap (per request, with defaults)
- Environment-based configuration via `pydantic-settings`

Not implemented (see [Current Limitations](#current-limitations)): embeddings, vector storage, similarity search, retrieval, RAG query pipeline, LLM-based question answering, chat endpoint, and chunk/project persistence to MongoDB.

---

## Architecture

```
Client
   ↓
FastAPI Routes  (src/routes/base.py, src/routes/data.py)
   ↓
Controllers     (DataController, processController, projectController)
   ↓
File Storage / LangChain Processing  (local disk, TextLoader / PyMuPDFLoader, text splitter)
   ↓
MongoDB connection layer  (AsyncIOMotorClient — connected, but not queried)
```

**Important distinction:** MongoDB is wired up at the application level (`app.mongo_conn`, `app.db_client` are created on startup and closed on shutdown), but no controller or route currently reads from or writes to `app.db_client`. The Pydantic-based Mongo document schemas (`project`, `datachnuk`) exist as model definitions but are not yet used by any endpoint to insert or query documents. Effectively, MongoDB is *configured* but not yet *integrated* into the request-handling flow.

---

## Project Structure

```
mini-RAG/
│
├── Docker/
│   ├── docker-compose.yml        # MongoDB container definition
│   ├── .gitignore
│   └── mongodb/                  # host-side bind mount target for Mongo data
│
├── .env                          # local environment values (not committed)
├── .env.example                  # template for required environment variables
├── requirements.txt              # Python dependencies
├── note.md
├── README.md
│
└── src/
    ├── assets/
    │   └── files/                # uploaded files, organized per project_id
    │
    ├── controllers/
    │   ├── BaseController.py     # shared base: settings, base paths, random string helper
    │   ├── DataController.py     # file validation, unique filepath generation
    │   ├── ProcessController.py  # (class name: processController) file loading & chunking
    │   ├── projectController.py  # project directory resolution/creation
    │   └── __init__.py
    │
    ├── helpers/
    │   └── config.py             # Settings (pydantic-settings) and get_settings()
    │
    ├── models/
    │   ├── db_schemes/
    │   │   ├── data_chunk.py     # Pydantic schema for a chunk (not yet persisted)
    │   │   └── project.py        # Pydantic schema for a project (not yet persisted)
    │   ├── enums/
    │   │   ├── processEnum.py    # supported file extensions (.txt, .pdf)
    │   │   └── ResponseEnums.py  # API response signal strings
    │   └── __init__.py
    │
    ├── routes/
    │   ├── base.py                # root/welcome endpoint
    │   ├── data.py                 # upload and process endpoints
    │   └── schemes/
    │       └── data.py             # ProcessRequest request body schema
    │
    └── main.py                     # FastAPI app instance, startup/shutdown events, routers
```

---

## Technology Stack

| Technology | Purpose in this project |
|---|---|
| **Python** | Core implementation language. |
| **FastAPI** | Web framework used to define the HTTP API and routing. |
| **Uvicorn** | ASGI server used to run the FastAPI application. |
| **MongoDB** | Intended document store for projects and chunks; currently only connected, not queried. |
| **Motor** | Async MongoDB driver, used to create the `AsyncIOMotorClient` at startup. |
| **Pydantic Settings** | Loads and validates configuration from environment variables / `.env`. |
| **aiofiles** | Enables non-blocking, asynchronous writing of uploaded files to disk. |
| **LangChain** | Provides the text-splitting utility (`RecursiveCharacterTextSplitter`). |
| **LangChain Community** | Provides the document loaders (`TextLoader`, `PyMuPDFLoader`) used for TXT/PDF ingestion. |
| **PyMuPDF** | PDF parsing backend used internally by `PyMuPDFLoader`. |
| **Docker / Docker Compose** | Runs a MongoDB instance in a container for local development. |

---

## API Documentation

### `GET /api/v1/`

Returns basic application metadata from configuration.

**Response 200:**
```json
{
  "app_name": "mini-RAG",
  "app_version": "0.1"
}
```

### `POST /api/v1/data/upload/{project_id}`

Uploads a file into a project-scoped folder.

- **Path parameter:** `project_id` — string identifier used to name/create the storage folder under `src/assets/files/{project_id}/`. Not validated against the `project` Pydantic model at request time.
- **Body:** `multipart/form-data` file upload.
- **Supported MIME types:** controlled by `FILE_ALLOWED_TYPES` in configuration (per `.env.example`: `application/pdf`, `text/plain`).
- **Maximum file size:** controlled by `FILE_MAX_SIZE_MB` (default in `.env.example`: 10 MB).
- **File ID:** generated as `{12-char random string}_{sanitized original filename}`.
- **Storage location:** `src/assets/files/{project_id}/{file_id}`.

**Possible responses:**
- `200 OK` — `{"signal": "FILE_UPLOADED_SUCCESS", "file_id": "<generated_id>"}`
- `400 Bad Request` — `{"signal": "FILE_TYPE_NOT_SUPPORTED"}` (returned both for actual unsupported file types and for unrelated exceptions during file writing — see [Current Limitations](#current-limitations))
- `400 Bad Request` — `{"signal": "FILE_SIZE_EXCEEDED"}`

### `POST /api/v1/data/process/{project_id}`

Loads a previously uploaded file and splits it into text chunks.

**Request body (`ProcessRequest`):**
```json
{
  "file_id": "string (required)",
  "chunk_size": 100,
  "overlap_size": 20,
  "do_reset": 0
}
```
- `file_id` — the identifier returned by the upload endpoint.
- `chunk_size` — optional, default `100`.
- `overlap_size` — optional, default `20`.
- `do_reset` — accepted by the schema but not referenced anywhere in the processing logic.

**How the file is read:** the file extension is extracted from `file_id`; `.txt` is routed to `TextLoader`, `.pdf` is routed to `PyMuPDFLoader`. Any other extension causes `get_file_loader()` to return `None`, which is not currently checked before calling `.load()` on it (see [Current Limitations](#current-limitations)).

**How chunking works:** the loaded documents' `page_content` and `metadata` are extracted, then passed to `RecursiveCharacterTextSplitter.create_documents()` with the requested `chunk_size` and `overlap_size`.

**Current response:** the endpoint returns the raw list of LangChain `Document` chunk objects directly as the response body (or a `400` with `PROCESSING_FAILED` if no chunks were produced). The chunks are **not** persisted to MongoDB or anywhere else — this endpoint currently returns processing results without storing them.

---

## Data Flow

### Upload flow
```
Client
  → FastAPI (upload_data)
  → DataController.validate_uploaded_file (MIME type + size check)
  → projectController.get_project_path (creates project folder if missing)
  → DataController.generate_unique_filepath (random ID + sanitized filename)
  → aiofiles async chunked write to disk
  → JSON response with file_id
```

### Processing flow
```
Client
  → FastAPI (process_endpoint)
  → processController (identifies file extension)
  → TextLoader (.txt) or PyMuPDFLoader (.pdf)
  → LangChain Document objects (page_content + metadata)
  → RecursiveCharacterTextSplitter.create_documents
  → list of chunk Documents
  → returned directly in the HTTP response (no persistence)
```

---

## Configuration

Environment variables read by `src/helpers/config.py`:

| Variable | Purpose | In `.env.example`? |
|---|---|---|
| `APP_NAME` | Application name, returned by the root endpoint. | Yes |
| `APP_VERSION` | Application version, returned by the root endpoint. | Yes |
| `OPENAI_API_KEY` | Declared in settings; not referenced anywhere else in the current code. | Yes |
| `FILE_ALLOWED_TYPES` | List of accepted MIME types for uploads. | Yes |
| `FILE_MAX_SIZE_MB` | Maximum allowed upload size in megabytes. | Yes |
| `FILE_DEFAULT_CHUNK_SIZE` | Byte size used when streaming uploaded file content to disk (this is a *file I/O* chunk size, not the text-splitting `chunk_size`). | Yes |
| `MONGODB_URL` | Connection string used by `AsyncIOMotorClient` at startup. | **No — missing from `.env.example`** |
| `MONGODB_DATABASE` | Database name selected from the Mongo client at startup. | **No — missing from `.env.example`** |

A developer cloning this repository and copying `.env.example` to `.env` will be missing `MONGODB_URL` and `MONGODB_DATABASE`, which are required fields on the `Settings` class — the application will fail to start without manually adding them.

---

## Installation

Tested command sequence for Ubuntu/Linux:

```bash
python -m venv mini-rag
source mini-rag/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins the following core dependencies: `fastapi`, `uvicorn[standard]`, `python-multipart` (required by FastAPI for handling file uploads), `python-dotenv`, `pydantic-settings`, `aiofiles`, `langchain`, `langchain-community`, `PyMuPDF`, and `motor`.

---

## Environment Setup

Copy the example environment file and fill in real values:

```bash
cp .env.example .env
```

Then edit `.env` and add, at minimum, the two Mongo-related variables that are missing from `.env.example`:

```
MONGODB_URL=mongodb://localhost:27007
MONGODB_DATABASE=mini_rag
```

`.env` should never be committed to version control — it is expected to hold secrets such as `OPENAI_API_KEY` and connection strings. Confirm it is listed in `.gitignore` before committing changes.

---

## MongoDB with Docker

Start the MongoDB container defined in `Docker/docker-compose.yml`:

```bash
docker compose -f Docker/docker-compose.yml up -d
```

Configuration details from the compose file:
- **Image:** `mongo:8.0`
- **Container name:** `mongodb`
- **Exposed port:** host `27007` mapped to container `27017` — the client-side `MONGODB_URL` must use `27007`, not the default `27017`, when connecting from the host.
- **Volume:** `./mongodb:/data/bd`
- **Network:** custom bridge network `backend`

**Issue to note:** the standard MongoDB data directory inside the container is `/data/db`, not `/data/bd`. As written, this volume mount does not target MongoDB's actual data directory, so data may not be persisted to the intended location, or MongoDB may fall back to writing inside the container's writable layer (lost on container removal). This should be corrected to `/data/db` for the volume to reliably persist data.

---

## Running the API

From the project root, with the virtual environment activated and `.env` configured:

```bash
uvicorn src.main:app --reload
```

Once running (default port 8000):
- **API root:** `http://localhost:8000/api/v1/`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Example API Usage

**Root endpoint:**
```bash
curl http://localhost:8000/api/v1/
```

**Upload a PDF:**
```bash
curl -X POST "http://localhost:8000/api/v1/data/upload/1" \
  -F "file=@/path/to/document.pdf;type=application/pdf"
```

**Upload a TXT file:**
```bash
curl -X POST "http://localhost:8000/api/v1/data/upload/1" \
  -F "file=@/path/to/notes.txt;type=text/plain"
```

**Process an uploaded file:**
```bash
curl -X POST "http://localhost:8000/api/v1/data/process/1" \
  -H "Content-Type: application/json" \
  -d '{
        "file_id": "abcdef123456_document.pdf",
        "chunk_size": 200,
        "overlap_size": 30
      }'
```

---

## File Storage

Uploaded files are stored at:

```
src/assets/files/{project_id}/{random_id}_{clean_filename}
```

- `project_id` is used as-is to name (and create, if missing) a folder under `src/assets/files/`.
- `random_id` is a 12-character random lowercase-alphanumeric string generated by `BaseController.generate_random_string`.
- `clean_filename` is the original filename with any character that is not a word character or a period stripped out (via regex), and spaces replaced with underscores.
- The code checks for filename collisions and regenerates the random prefix if the target path already exists, though note that on collision it reassigns to a misspelled variable (`rondom_key`) and does not actually use the newly generated key when building the final path in that branch (see [Current Limitations](#current-limitations)).

---

## Processing Pipeline

1. **Extension detection** — `get_file_extenstion()` extracts the extension from the file ID using `os.path.splitext`.
2. **Loader selection** — `.txt` → `TextLoader` (UTF-8), `.pdf` → `PyMuPDFLoader`. Any other extension results in `None` being returned, with no explicit handling downstream.
3. **Document loading** — the selected loader's `.load()` method returns a list of LangChain `Document` objects, each with `page_content` and `metadata`.
4. **Splitting** — `RecursiveCharacterTextSplitter` is configured with the requested `chunk_size` and `chunk_overlap` (named `overlap_size` in the API) and `length_function=len`, then `create_documents()` is called with the collected texts and metadata to produce the final chunk list.

---

## Current Limitations

The following RAG-pipeline capabilities are **not implemented** in the current codebase:

- No embedding generation
- No vector database integration
- No vector similarity search
- No retrieval logic
- No RAG query pipeline
- No LLM-based question answering
- No chat endpoint
- No persistence of chunks (or projects) to MongoDB

### Known code issues / inconsistencies

- **MongoDB settings are incorrectly declared.** In `Settings`, `MONGODB_URL = str` and `MONGODB_DATABASE = str` use `=` instead of `:` for type annotation — this assigns the `str` type itself as a class-level default rather than declaring a typed, required field, which does not behave like the other fields in the same class.
- `MONGODB_URL` and `MONGODB_DATABASE` are used in `src/main.py` but are **not present in `.env.example`**.
- The MongoDB connection (`app.mongo_conn`, `app.db_client`) is created on startup and closed on shutdown, but no controller or route currently performs a read or write against it.
- **Docker volume path issue:** `./mongodb:/data/bd` should almost certainly be `/data/db`, the standard MongoDB data directory.
- `src/helpers/config.py` imports `INT` from `click` but never uses it — an unused/incorrect import.
- `ProcessController.py` imports `from src.models import processingEnum`, but `processingEnum` is defined in `src/models/enums/processEnum.py`; depending on what `src/models/__init__.py` actually exports, this import may not resolve as written.
- The Mongo document schema classes use inconsistent casing (`datachnuk`, `project`) relative to standard Python `PascalCase` class naming.
- `bson.objectid` is imported as `objectid` (lowercase) in the schema files; the standard class name is `ObjectId`. As written, this import will fail or reference the wrong symbol.
- `min_lenght` in `data_chunk.py` is a misspelling of `min_length`, so this validation constraint is not actually applied by Pydantic.
- `arbitraty_types_allowed` in both schema files' inner `config` class is a misspelling of `arbitrary_types_allowed`, and the inner class is named `config` (lowercase) rather than Pydantic's expected `Config`, so this setting likely has no effect.
- `processController` and `projectController` are named in lowerCamelCase rather than the conventional PascalCase used for Python classes (compare to `DataController`, `BaseController`).
- `get_file_extenstion` in `ProcessController.py` is a misspelling of `get_file_extension`.
- In `DataController.generate_unique_filepath`, the retry loop reassigns to `rondom_key` (typo) instead of `random_key`, so the loop condition and final returned filename do not actually use a newly generated random string on collision — the same `random_key` from before the loop is reused in the returned value.
- The exception handler in `upload_data` returns `ResponseSignal.FILE_TYPE_NOT_SUPPORTED` for **any** exception raised while writing the file (e.g., disk I/O errors), not only for file type problems — this is a misleading error signal.
- `process_endpoint` calls `process_controller.get_file_content(file_id=file_id)`, which calls `get_file_loader()` and then unconditionally calls `.load()` on the result. If the file extension is unsupported, `get_file_loader()` returns `None`, and calling `.load()` on `None` will raise an unhandled `AttributeError` rather than a graceful error response.
- `do_reset` is defined on `ProcessRequest` but is never read or used in `process_endpoint` or `ProcessController`.
- `OPENAI_API_KEY` is declared as a required setting but is not referenced anywhere in the current implementation.
- There is no logic anywhere in the codebase that writes project or chunk records to MongoDB, despite both Pydantic schemas existing for that purpose.

---

## Security Considerations

- `.env` must not be committed to version control; it is expected to hold `OPENAI_API_KEY` and MongoDB connection details.
- File uploads are checked against an allow-list of MIME types and a maximum size, but MIME type as reported by the client is not authoritative — deeper content validation would be needed before trusting uploaded files in a production setting.
- Filenames are sanitized (non-word characters stripped, spaces replaced) before being used to build a filesystem path, which mitigates basic path-traversal risk from the filename itself, but `project_id` is used directly to build a directory path without similar validation.
- There is currently no authentication or authorization on any endpoint — any client can upload to, or trigger processing for, any `project_id`.
- There is no rate limiting; the upload and processing endpoints could be abused for resource exhaustion (large numbers of uploads, or expensive processing calls).
- As with any file-ingestion service, uploaded file contents should not be blindly trusted by downstream processing (e.g., PDF parsing) without awareness of parser-level vulnerabilities.

---

## Future Roadmap

**The following items are NOT implemented. They describe possible future direction only.**

1. Persist projects in MongoDB
2. Persist chunks in MongoDB
3. Generate embeddings for chunks
4. Integrate a vector database
5. Implement retrieval over stored embeddings
6. Implement a full RAG query pipeline
7. Integrate OpenAI (or another LLM provider) for generation
8. Add a chat/question-answering endpoint
9. Add authentication and authorization
10. Add background/async processing (e.g., Celery) for large files
11. Add automated tests
12. Add a production-oriented Docker setup (multi-stage build, non-root user, etc.)

---

## Development Notes

- Use a Python virtual environment (`python -m venv`) to isolate dependencies.
- Keep all secrets and environment-specific values in `.env`, never hardcoded.
- Run MongoDB locally via the provided Docker Compose file rather than installing it directly on the host.
- Use the Swagger UI (`/docs`) or `curl`/Postman to exercise the upload and process endpoints during development.
- The codebase currently uses `print()` statements for debug output in `DataController.validate_uploaded_file` and a partially configured `logging` logger (`uvicron.error` — note the typo, should likely be `uvicorn.error`) in `data.py`; logging is inconsistent across modules.
- Review the [Current Limitations](#current-limitations) section before extending the codebase, since several naming and import issues could cause runtime errors on currently untested code paths (e.g., processing a file with an unsupported extension, or any code path relying on `bson.objectid.objectid`).

---

## License

No license is currently specified in this repository.
