from os import listdir
from moviepy.editor import concatenate_videoclips, VideoFileClip, TextClip, CompositeVideoClip


def unify_clips():

    # Obtain all file names in clips folders
    clips_files = listdir('./clips/')

    # Unify all clips into one file
    clip_list = []
    total_duration = 0
    for clip in clips_files:
        video_clip = VideoFileClip('clips/{}'.format(clip))
        total_duration += video_clip.duration
        txt = TextClip("twitch.com/{}".format(clip.split('$')[1]), fontsize=80, color="white", font="Impact").set_duration(video_clip.duration).set_position(("center", "top"))
        clip_list.append(CompositeVideoClip([video_clip,txt]))

        print("Current total duration: {}".format(total_duration))
        if total_duration > 90:
            break
    
    final_clip = concatenate_videoclips(clip_list, method="compose", padding=0.5)
    final_clip.write_videofile("unification.mp4")