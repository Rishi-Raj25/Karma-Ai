"""Quick test to verify Sarvam AI API connectivity."""

import os

from dotenv import load_dotenv

load_dotenv()


def test_chat():
    """Test Sarvam chat completion."""
    from sarvam_service import chat_completion

    messages = [
        {"role": "system", "content": "You are a helpful assistant. Reply in Hinglish."},
        {"role": "user", "content": "Hello, mera naam scammer hai, aapko lottery mili hai!"},
    ]

    print("Testing Chat API...")
    response = chat_completion(messages)
    print(f"Response: {response}\n")
    return response


def test_tts(text: str):
    """Test Sarvam text-to-speech."""
    from sarvam_service import text_to_speech

    print("Testing TTS API...")
    audio_bytes = text_to_speech(text, language_code="hi-IN", speaker="shubh")

    output_path = "test_output.wav"
    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    print(f"Audio saved to {output_path} ({len(audio_bytes)} bytes)\n")


def test_stt():
    """Test Sarvam speech-to-text (requires test_output.wav from TTS test)."""
    from sarvam_service import speech_to_text

    if not os.path.exists("test_output.wav"):
        print("Skipping STT test - run TTS test first to generate test_output.wav\n")
        return

    print("Testing STT API...")
    with open("test_output.wav", "rb") as f:
        audio_bytes = f.read()

    transcript = speech_to_text(audio_bytes, language_code="hi-IN")
    print(f"Transcript: {transcript}\n")


if __name__ == "__main__":
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key or api_key == "your_sarvam_api_key_here":
        print("ERROR: Set your SARVAM_API_KEY in .env first!")
        exit(1)

    print("=" * 50)
    print("  Sarvam AI API Test Suite")
    print("=" * 50 + "\n")

    response = test_chat()
    test_tts(response)
    test_stt()

    print("All tests complete!")
