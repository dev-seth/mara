#!/usr/bin/env python3
import os
import sys
from urllib import request
from PIL import Image
from bs4 import BeautifulSoup
from mutagen.id3 import ID3, TPE1, TIT2, TALB, TDRC, TRCK, TCON, APIC


print('MARA\nThe Metal Archives Parser\nVer. 0.1')

# functions

def FixFileName(oldName):
    newName = oldName.replace('/', '-')
    return newName


def imageDownloader():
    imgUrl = input('Please enter the image URL: ')
    imgFilename = imgUrl.split('/')[-1]
    imgFilenameExtension = imgFilename.split('.')[-1]
    if imgFilenameExtension.lower() not in ['jpg', 'jpeg', 'png']:
        print('ERROR: only JPG and PNG are supported')
        return None
    imgNewFilename = 'folder.' + imgFilenameExtension.lower()
    request.urlretrieve(imgUrl, imgNewFilename)
    return imgNewFilename

# images

listOfFiles = sorted(os.listdir('.'))

image = None
for file in listOfFiles:
    if file.lower()[-4:] in ['.jpg', 'jpeg', '.png']:
        image = file
        break

while image is None:
    print('There is no images in the folder!')
    image = imageDownloader()

if image.lower()[-3] == 'png':
    im = Image.open(image)
    im.save('folder.jpg', 'JPEG')
    print('Image converted to JPEG')
    os.remove(image)
    image = 'folder.jpg'

os.rename(image, 'folder.jpg')

im = Image.open('folder.jpg')
size = 600, 600
im.thumbnail(size, Image.ANTIALIAS)
im.save('folder666.jpg', 'JPEG')

# parser

if len(sys.argv) > 1:
    url = sys.argv[1]
else:
    url = input('Enter the URL: ')
# if not url:
#     url = 'http://www.metal-archives.com/albums/Death/The_Sound_of_Perseverance/618'
while not url.startswith('http://www.metal-archives.com/albums/'):
    url = input('Incorrect URL. Enter the album URL: ')

html = request.urlopen(url).read()
soup = BeautifulSoup(html, "html5lib")

artist = soup.find(class_='band_name').get_text().strip()
album = soup.find(class_='album_name').get_text().strip()
type = (soup.find('dl', class_='float_left').find_all('dd')[0]).get_text()
year = (soup.find('dl', class_='float_left').find_all('dd')[1]).get_text()[-4:]

preGenre = input("Enter the genre (1 - Black Metal, 2 - Death Metal, 3 - Dark Ambient, 4 - Other): ")
if preGenre == '1':
    genre = 'Black Metal'
elif preGenre == '2':
    genre = 'Death Metal'
elif preGenre == '3':
    genre = 'Dark Ambient'
else:
    genre = input('Enter other genre: ')

songsTable = soup.find('table', class_='display table_lyrics')


def checkClass(css_class):
    return css_class == 'odd' or css_class == 'even'


songsRows = songsTable.find_all(class_=checkClass)

songs = []

for songUnit in songsRows:
    songParts = songUnit.find_all('td')
    songNum = songParts[0].get_text(strip=True)[:-1]
    if len(songNum) == 1:
        songNum = '0' + songNum
    songTitle = songParts[1].get_text(strip=True)
    rawLyrics = str(songParts[3])

    if 'instrumental' in rawLyrics:
        songId = 'Instrumental'
    elif 'lyrics' not in rawLyrics:
        songId = 'No lyrics'
    else:
        songId = rawLyrics.split("'")[1]

    songs.append({'#': songNum, 'Title': songTitle, 'Lyrics ID': songId})

print('\nArtist:\t', artist)
print('Album:\t', album)
print('Type:\t', type)
print('Year:\t', year)
print('Genre:\t', genre)
print('Tracklist:')
for i in songs:
    print('{0}.\t{1}'.format(i['#'], i['Title']))

# rename files

list_of_mp3s = list(filter(lambda x: x.lower().endswith('mp3'), listOfFiles))

quantityOfMp3s = len(list_of_mp3s)

if quantityOfMp3s != len(songs):
    print('ERROR: The number of files mismatch.')
    quit()

newFileNames = []
for song in songs:
    new_file_name = song['#'] + '-' + FixFileName(song['Title']) + '.mp3'
    newFileNames.append(new_file_name)

for i in range(quantityOfMp3s):
    filename = list_of_mp3s[i]
    audio = ID3(filename)
    audio.delete()
    audio.add(TPE1(encoding=3, text=artist))
    audio.add(TALB(encoding=3, text=album))
    audio.add(TDRC(encoding=3, text=year))
    audio.add(TCON(encoding=3, text=genre))
    audio.add(TRCK(encoding=3, text=str(i + 1)))
    audio.add(TIT2(encoding=3, text=songs[i]['Title']))
    audio.add(
        APIC(encoding=3, mime=u'image/jpg', type=3, desc=u'Front cover', data=open(u'folder666.jpg', 'rb').read()))
    audio.save(filename)
    os.rename(filename, newFileNames[i])

os.remove('folder666.jpg')

print('\nTaged and renamed {0} files.'.format(quantityOfMp3s))

# add lyrics

question0 = input('Add lyrics to the directory? (Y, n): ')
if question0 in ['Y', 'y', '1', '']:
    lyricsCounter = 0
    for song in songs:
        if song['Lyrics ID'] not in ['Instrumental', 'No lyrics']:
            lyricsCounter += 1
            lyricsURL = 'http://www.metal-archives.com/release/ajax-view-lyrics/id/' + song['Lyrics ID']
            lyricsHTML = request.urlopen(lyricsURL).read()
            lyricsSoup = BeautifulSoup(lyricsHTML, "html5lib")
            lyricsText = lyricsSoup.get_text()
            lyricsFilename = song['#'] + '-' + FixFileName(song['Title'])
            with open(lyricsFilename, 'w') as lyricsFile:
                lyricsFile.write(lyricsText)
    print('Added {0} lyrics files'.format(lyricsCounter))
else:
    print('OK. No lyrics for now.')

# rename directory

question1 = input('Move files and rename the album directory? (Y/n): ')

if question1 not in ['Y', 'y', '1', '']:
    print('Quiting without renaming...')
    quit()

print("OK. Let's move and rename...")

newHomeA = "/home/seth/Downloads/"
newHomeB = "/home/seth/Music/"
newHomeC = "/home/seth/TempFiles/"
newHome = None
while True:
    question2 = input("Please choose a new folder for the album (1 - Downloads, 2 - Music, 3 - TempFiles): ")
    if question2 in ['1', '']:
        newHome = newHomeA
        break
    elif question2 == '2':
        newHome = newHomeB
        break
    elif question2 == '3':
        newHome = newHomeC
        break
    else:
        print('WTF?!')
        continue

currentAlbumPath = os.getcwd()

if type != 'Full-length':
    newAlbumDir = artist + '/' + year + '-' + album + ' [' + type + ']'
else:
    newAlbumDir = artist + '/' + year + '-' + album

newAlbumPath = newHome + newAlbumDir

os.chdir('/home/seth/TempFiles')
os.renames(currentAlbumPath, newAlbumPath)

print('Album moved to', newAlbumPath)
print('Done!')
