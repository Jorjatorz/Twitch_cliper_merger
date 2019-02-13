from os import listdir
from moviepy.editor import concatenate_videoclips, VideoFileClip, TextClip, CompositeVideoClip

VIDEO_DURATION_THRESHOLD = 90 # Unification video threshold duration in seconds

def unify_clips():
        """Reads all the mp4 files inside a folder and merge them into a single video adding the streamer names to them
        """
        # Obtain all file names in clips folders
        clips_files = listdir('./clips/')

        # Unify all clips into one file and add a text with the streamer name
        clip_list = []
        total_duration = 0
        for clip in clips_files:
                video_clip = VideoFileClip('clips/{}'.format(clip))
                text = "twitch.com/{}".format(clip.split('$')[1])
                text_clip = TextClip(text, fontsize=80, color="white", font="Impact").set_duration(video_clip.duration).set_position(("center", "top"))
                clip_list.append(CompositeVideoClip([video_clip,text_clip]))

                total_duration += video_clip.duration
                print("Current total duration: {}".format(total_duration))
                if total_duration > VIDEO_DURATION_THRESHOLD:
                        break

        final_clip = concatenate_videoclips(clip_list, method="compose", padding=0.5)
        final_clip.write_videofile("unification.mp4")