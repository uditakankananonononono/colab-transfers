"""Fetch Unit 193 manifests through an explicitly read-only Drive scope, then verify."""
from google.colab import auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth import default
import hashlib
import io
import os
import zipfile

FILE_ID = "1O3Y88m8udwfkPM0LSjyqFEzeMY-fJv_N"
ZIP_PATH = "/content/193-manifests-for-colab.zip"
EXPECTED = {
    "all_npy_manifest.tsv": "b7bf1e20234d6254c68a72bbd04f1926ab95a87de9d3f7b8751b9518ed24239f",
    "fold_assignments.csv": "a56e946975aaa98b23a686c3ce762857ce48ded2e3595a4f187beffed22da960",
    "random_assignments.csv": "cc0cedde458ec0ddaad16949774a62a6505cc64e4cd016f4ba8cce5f97d56e58",
}

print("Requesting Google Drive read-only OAuth scope only.", flush=True)
auth.authenticate_user(scopes=["https://www.googleapis.com/auth/drive.readonly"])
creds, _ = default()
service = build("drive", "v3", credentials=creds, cache_discovery=False)
request = service.files().get_media(fileId=FILE_ID)
with io.FileIO(ZIP_PATH, "wb") as output:
    downloader = MediaIoBaseDownload(output, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Downloaded {int(status.progress() * 100)}%", flush=True)
print("Downloaded bytes:", os.path.getsize(ZIP_PATH), flush=True)

try:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = set(archive.namelist())
        missing = set(EXPECTED) - names
        if missing:
            raise RuntimeError(f"Archive missing expected manifests: {sorted(missing)}")
        mismatches = []
        for name, expected in EXPECTED.items():
            payload = archive.read(name)
            actual = hashlib.sha256(payload).hexdigest()
            print(f"{name} sha256={actual}", flush=True)
            if actual != expected:
                mismatches.append((name, actual, expected))
        if mismatches:
            raise RuntimeError(f"LOCKED HASH MISMATCH: {mismatches}")
        for name in EXPECTED:
            with open(f"/content/{name}", "wb") as target:
                target.write(archive.read(name))
except Exception:
    print("MANIFEST HASH VERDICT: FAIL; do not run the gate or fetch dataset members.", flush=True)
    raise
print("MANIFEST HASH VERDICT: PASS (all three locked SHA-256 hashes match).", flush=True)
