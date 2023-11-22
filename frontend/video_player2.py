import vlc

media = vlc.MediaPlayer("/Users/ckrath/Desktop/video.mp4")

media.play()

try:
    while True:
        pass
except KeyboardInterrupt:
    media.stop()