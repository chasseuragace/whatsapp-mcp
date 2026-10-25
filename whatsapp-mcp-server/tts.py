"""Text-to-speech through a Piper HTTP server (python -m piper.http_server)."""
import os
import tempfile

import requests

# In Docker, host.docker.internal reaches a Piper server running on the Mac's localhost.
PIPER_URL = os.environ.get("PIPER_URL", "http://localhost:5000").rstrip("/")


class PiperError(RuntimeError):
    pass


def synthesize_to_wav(text: str) -> str:
    """Synthesize text with Piper and return the path of a new temporary .wav file.

    The caller is responsible for deleting the file.
    """
    try:
        response = requests.post(f"{PIPER_URL}/synthesize", json={"text": text}, timeout=120)
    except requests.RequestException as e:
        raise PiperError(
            f"Could not reach the Piper TTS server at {PIPER_URL} ({e}). "
            "Start it on the Mac, e.g. by running `say hello`."
        ) from e

    # Piper returns WAV bytes (labelled text/html), so check the bytes rather than the header.
    if response.status_code != 200 or not response.content.startswith(b"RIFF"):
        raise PiperError(
            f"Piper TTS server at {PIPER_URL} did not return audio "
            f"(HTTP {response.status_code}): {response.text[:200]}"
        )

    temp_dir = os.environ.get("WHATSAPP_TMP_DIR") or None
    if temp_dir:
        os.makedirs(temp_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=temp_dir) as f:
        f.write(response.content)
        return f.name
