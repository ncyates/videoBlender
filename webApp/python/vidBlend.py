#imports

'''

#TODO:
-- Implment check if vid has already been blended
--Argparse
	--re-work?
	--implement required functionality

--default intelligently handle multiprocesing?
	--(if number of images is more than 2x core count)?
	--what about reserving 1 processor?

implement youtube-dl, not just pafy ?
fix UTF-8 naming (weird characters crash)

TESTING:
    hash images, find deltas for versions made both with shuffling off and on to determine if it should be included functionality
Defensive:
    Exceptions or bad input



#globals:
source_dir
source_url
source_vid
destination
output_name
reference_dims


#functions
gui
init_paths
DONE get_video 
DONE video_to_frames
make_image_list
strip_exif
detect_near_dupes
denoise
detect_letterbox
crop_letterbox
DONE color-balance
DONE start
DONE reducer
DONE blender
DONE wrap_up
delete_frames
delete_vid
delete_blends


'''
import os
import sys
import argparse
import multiprocessing
import math
import shutil
import time

import cv2
import pafy
import numpy as np

def videoToFrames(stream, framesDir, start, end):
    try:
        vid = cv2.VideoCapture(stream)
    except:
        print('problem opening file')
        sys.exit(1)

    if not vid.isOpened():
        print('file not opened')
        sys.exit(1)

    success, image = vid.read()  # get the first frame of the video
    frameRate = int(math.ceil(vid.get(cv2.CAP_PROP_FPS)))
    numFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    vid.set(cv2.CAP_PROP_POS_FRAMES,start)
    while success and vid.get(cv2.CAP_PROP_POS_FRAMES) <= end:
        success, image = vid.read()
        if int((vid.get(cv2.CAP_PROP_POS_FRAMES)-1)) % frameRate == 0:
            outFilename = framesDir + '/frame_' + str(int(vid.get(cv2.CAP_PROP_POS_FRAMES))-1).zfill(6) + '.jpg'
            cv2.imwrite(outFilename, image)
        # exit if Escape is hit
        if cv2.waitKey(1) == 27:
            vid.release()
            break

def getVid(url):
    #start_time = time.time()
    #print(url)
    video = pafy.new(url)
    global linkId
    linkId = video.videoid

    premade = 'home/ubuntu/videoBlender/server/static/'
    #print(os.listdir(premade))
    checkId = linkId + '.jpg'
    #print(checkId)    
    if checkId in os.listdir(premade):
        #print("file exists")
        return True
        #print(premade + checkId)
        #sys.stdout.flush()
        #time.sleep(5)
        #exit()
    #title = video.title.replace(" ","_")
    #title = video.title.encode('utf-8')
    #title = title.translate(None, '/\?:"<>|*')  # ERROR on certain characters?
    #print(title)
    global framesDir
    global dest
    dest = str(hash(url))
    #print("In getVid, " + url + " hashes to " + dest)
    framesDir = 'home/ubuntu/videoBlender/server/processing/frames/'  + linkId
    #framesDir = 'C:/_Software/copypy/blend/intermediate/' + title
    #print(framesDir)

    #make the output directory
    try:
        os.mkdir(framesDir)
    except OSError as e:
        if e.errno == 17:
            # if tkMessageBox.askokcancel('Folder already exists', 'The output folder already exists, proceeding may overwrite the files it contains.'):
            pass
        else:
            print('Error: Exiting')
            sys.exit(1)
    best = video.getbestvideo()
    stream = str(best.url)

    #open the video stream
    try:
        vid = cv2.VideoCapture(stream)
    except:
        print('problem opening file')
        sys.exit(1)

    if not vid.isOpened():
        print('file not opened')
        sys.exit(1)

    numFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    vid.release()
    #print("\nTook %s seconds" % (time.time() - start_time) + " to get video")
    numCores = multiprocessing.cpu_count()
    framesChunks = []
    chunkLength = numFrames / numCores
    chunkStart = 0
    chunkEnd = chunkStart + chunkLength
    partialChunk = numFrames % numCores

    start_time = time.time()
    for i in range(numCores):
        framesChunks.append(multiprocessing.Process(target=videoToFrames, args=(stream, framesDir, chunkStart, chunkEnd)))
        chunkStart = chunkEnd
        chunkEnd = chunkStart + chunkLength

    if partialChunk > 0:
        framesChunks.append(multiprocessing.Process(target=videoToFrames, args=(stream, framesDir, chunkStart, numFrames)))

    for i in range(len(framesChunks)):
        framesChunks[i].start()

    for i in range(len(framesChunks)):
        framesChunks[i].join()

    #print("\nTook %s seconds" % (time.time() - start_time) + " to get frames from video")
    return False

def reducer(process, q, chunk, dstDir, zeroPad, stdDim):
    count = 0
    while len(chunk) > 1:
        fileNameA = chunk.pop()
        fileNameB = chunk.pop()
        blendName = dstDir + '/' + 'blend_' + process + '_' + str(count).zfill(zeroPad) + '.jpg'
        if blender(fileNameA,fileNameB,blendName,stdDim):
            chunk.insert(0, blendName)
        else:
            sys.stdout.write('Problem with blending ' + fileNameA + ' & ' + fileNameB)
        count += 1
    q.put(chunk[0])

def blender(fileNameA, fileNameB, blendName, stdDim):
    imageA = cv2.imread(fileNameA, 1)
    imageB = cv2.imread(fileNameB, 1)
    if imageA.shape != stdDim:
        imageA = cv2.resize(imageA, (stdDim[1], stdDim[0]))
    if imageB.shape != stdDim:
        imageB = cv2.resize(imageB, (stdDim[1], stdDim[0]))
    blend = cv2.addWeighted(imageA, .5, imageB, .5, 0)
    return cv2.imwrite(blendName, blend)

def colorBal(blendName):
    unbalanced = cv2.imread(blendName,1)
    colorChannels = cv2.split(unbalanced)
    normChannels = []
    for channel in colorChannels:
        sortFlat = np.sort(channel.flatten())
        flatLen = len(sortFlat)
        lowThresh = sortFlat[int(math.floor(flatLen * .005))]
        highThresh = sortFlat[int(math.ceil(flatLen * .995))]
        maskLow = channel < lowThresh
        maskHigh = channel > highThresh
        channel = np.ma.array(channel, mask=maskLow, fill_value=lowThresh)
        channel = channel.filled()
        channel = np.ma.array(channel, mask=maskHigh, fill_value=highThresh)
        channel = channel.filled()
        cv2.normalize(channel, channel, 0, 255, cv2.NORM_MINMAX)
        normChannels.append(channel)
    return cv2.merge(normChannels)

def blend(id):
    #print("in blend, id = " + id)
    hashedId = str(hash(id))
    #print("in blend, id hashes to = " + str(hash(id)))
    global blendDir
    blendDir = 'home/ubuntu/videoBlender/server/processing/blends/' + linkId
    try:
        os.mkdir(blendDir)
    except OSError as e:
        if e.errno == 17:

            pass
        else:
            print('Exiting ImageBlender')
            sys.exit(1)
    fileNames = [framesDir + '/' + str(f) for f in os.listdir(framesDir) if f.endswith('.JPG') or f.endswith('.jpg')] #FIX THIS LINE NOT CHEKCING JUST JPG
    sampleImage = cv2.imread(fileNames[0], 1)
    stdDim = sampleImage.shape  # standard dimensions based on one image. H x W
    # TODO: what about many different image dimensions? Possibly scan for all and set standard as most common dim.
    numCores = multiprocessing.cpu_count()
    #random.shuffle(fileNames)  # possibly gives better end result blend
    numFiles = len(fileNames)
    filesChunks = []
    chunkLength = numFiles // numCores
    zeroPad = int(math.ceil(math.log(chunkLength + 1, 10))) + 1  # of zeros to pad file names for output ordering
    chunkStart = 0
    chunkEnd = chunkStart + chunkLength

    partialChunk = numFiles % numCores
    for i in range(numCores):
        filesChunks.append(fileNames[chunkStart:chunkEnd])
        chunkStart = chunkEnd
        chunkEnd = chunkStart + chunkLength

    while partialChunk > 0:
        filesChunks[len(filesChunks) - 1].append(fileNames[(len(fileNames)) - partialChunk])
        partialChunk -= 1

    reducingQ = multiprocessing.Queue()
    blendProcesses = []

    for i in range(len(filesChunks)):
        blendProcesses.append(multiprocessing.Process(target=reducer, args=(
        'p' + str(i), reducingQ, filesChunks[i], blendDir, zeroPad, stdDim)))

    for i in range(len(blendProcesses)):
        blendProcesses[i].start()

    for i in range(len(blendProcesses)):
        blendProcesses[i].join()

    wrapCount = 1
    while reducingQ.qsize() > 1:
        wrapUpA = reducingQ.get()
        wrapUpB = reducingQ.get()
        if reducingQ.qsize() == 2:
            wrapUpB = reducingQ.get()
            outName = blendDir + '/' + '_Final.jpg'
        else:
            outName = blendDir + '/' + '_wrapUp' + str(wrapCount) + '.jpg'
        if blender(wrapUpA, wrapUpB, outName, stdDim):
            reducingQ.put(outName)
        else:
            print('Problem blending ' + wrapUpA + ' & ' + wrapUpB)
        wrapCount += 1
    #finalFilename = blendDir + '/' + '_Final_Balanced.jpg'
    #finalFilename = 'C:/_sw/fooSimpleAng/simpleApp/src/assets/Final_Balanced.jpg'
    #finalFilename = 'C:/_sw/fooNode/static/Final_Balanced.jpg' #works
    finalFilename = 'home/ubuntu/videoBlender/server/static/' + linkId + '.jpg'

    cv2.imwrite(finalFilename, colorBal(outName))
    #return finalFilename
    return linkId


if __name__=="__main__":
    #TODO: how add argparse support for local videos and directories of images
    #parser = argparse.ArgumentParser(description="Creates a blended image from a directory of images or from frames of a video.")
    parser = argparse.ArgumentParser(description="Creates a blended image from a video.")
    #group = parser.add_mutually_exclusive_group(required=True)
    #group.add_argument("-U","--URL" , help="the URL of the video to blend")
    #group.add_argument("-v", "--video",  help="the local file path of the video to blend",action="store")
    #group.add_argument("-i", "--images_dir",  help="the path of the directory that contains the images to blend",action="store")
    #parser.add_argument('blend-target', help='the URL, local video file, or local directory of images to blend')
    parser.add_argument("blend-target", help="the URL of the video to blend")
    parser.add_argument("-G","--GUI", help="Use a GUI to select the directory where video frames and blended images will be saved",action="store_true")
    parser.add_argument("-df","--delete_frames", help="Delete frames grabbed from video",action="store_true")
    parser.add_argument("-db","--delete_blends", help="Delete intermediate blended images",action="store_true")
    parser.add_argument("-s", "--sample_rate", type=int, help="(Positive) number of frames per second of video to save. Default is 1 frame per second. Any value greater than the actual number of FPS will be interpreted as the highest sample rate possible (i.e. all frames will be saved)", action="store")
    parser.add_argument("-f", "--file_type", help="Specify image file type that frames should be saved as, e.g. .jpeg, .tif, .png.",action="store")
    parser.add_argument("-nc", "--no_color_balance", help="Don't perform automatic color balancing",action="store_true")
    parser.add_argument("-nm", "--no_multiprocessing", help="Don't multiprocess",action="store_true")
    parser.add_argument("-c", "--crop_border",help="Crop images to remove black borders e.g. in letterboxed videos (black borders interfere with color-balancing algorithm)", action="store_true")
    parser.add_argument("-ce", "--clear_EXIF",help="Strip EXIF data from images (may help with image rotation issues when blending sets of images not pulled from video)", action="store_true")
    parser.add_argument("-r","--resize", help="Resize images. Specify HEIGHT WIDTH e.g. 1080 1920", nargs=2, type=int, action="store")
    parser.add_argument("-sh", "--shuffle_images",help="Shuffle images before blending (may give better result?)",action="store_true")
    parser.add_argument("-st", "--similarity_threshold",help="Threshold of similarity past which too-similar images will be skipped during blending", type=float, action="store")
    parser.add_argument("-d", "--denoise_images",help="Denoise images before blending (should probably only use in conjunction with --similarity_threshold to help reduce false-positive near duplicates)",action="store_true")

    args = parser.parse_args()
    id = str(sys.argv[1])    
    #url = 'https://www.youtube.com/watch?v=' + id    
    #getVid(url)
    if not getVid(id):
        outMessage = blend(id)
        print(outMessage)
        shutil.rmtree(framesDir)
        shutil.rmtree(blendDir)
    else:
        #print('yes file exists')
        print(linkId)
    sys.stdout.flush()

    
    #answer = args.x**args.y

    #if args.quiet:
    #    print(answer)
    #elif args.verbose:
    #    print ("{} to the power {} equals {}".format(args.x, args.y, answer))
    #else:
    #    print ("{}^{} == {}".format(args.x, args.y, answer))






