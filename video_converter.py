"""Video to audio converter script.

Functions to extract audio tracks from video files and save them as MP3.
"""

from pathlib import Path

from moviepy import VideoFileClip


def convert_video_to_audio(video_path: str | Path, output_path: str | Path | None = None) -> Path:
    """Convert a video file to an MP3 audio file.

    Reads the video file from the specified path, extracts the audio track,
    and saves it to an MP3 file. If no output path is provided, it uses the
    same directory and base name as the video file.

    Args:
        video_path: Path to the input video file (e.g., .mp4, .mkv).
        output_path: Optional path for the output MP3 file. If None, saves
            with the same name as the input file but with a .mp3 extension.

    Returns:
        Path to the generated MP3 file.

    Raises:
        FileNotFoundError: If the input video file does not exist.
        ValueError: If the video format is unsupported or the audio cannot be extracted.

    Example:
        >>> output = convert_video_to_audio("sample_video.mp4")
        >>> print(f"Audio saved to: {output}")
    """
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"The input video file does not exist: {video_file}")

    audio_file = video_file.with_suffix(".mp3") if output_path is None else Path(output_path)

    # Initialize the video clip
    clip = VideoFileClip(str(video_file))

    # Check if the video has an audio track
    if clip.audio is None:
        clip.close()
        raise ValueError(f"The video file {video_file} does not contain an audio track.")

    try:
        # Write the audio track to an MP3 file
        clip.audio.write_audiofile(str(audio_file), logger=None)
    finally:
        # Properly close the clip to free resources
        clip.close()

    return audio_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract audio from a video file and save it as MP3.")
    parser.add_argument("video_path", type=str, help="Path to the input video file.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Optional path for the output MP3 file.",
    )

    args = parser.parse_args()

    try:
        print(f"Converting '{args.video_path}'...")
        result_path = convert_video_to_audio(args.video_path, args.output)
        print(f"Success! Audio saved to: {result_path}")
    except Exception as error:
        print(f"Error: {error}")
