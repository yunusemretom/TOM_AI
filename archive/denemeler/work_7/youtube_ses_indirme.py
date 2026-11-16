import yt_dlp

def download_audio(url):
    options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

liste = ["https://www.youtube.com/watch?v=TLGrrztZpfM"]
# Kullanım
for i in liste:

    download_audio(i)
