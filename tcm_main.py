import clips_downloader
import clip_editor

def tcm():
    clips_downloader.download_clips()
    clip_editor.unify_clips()


if __name__ == "__main__":
    tcm()