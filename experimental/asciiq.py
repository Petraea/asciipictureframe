from __future__ import print_function
from blessings import Terminal
from PIL import Image
from Queue import Queue
from threading import Thread
from renderPixel import renderPixel
import random, sys, os, time, glob

#Set up the terminal.
t = Terminal()
print (t.hide_cursor)
print (t.enter_fullscreen)

acceptablefiletypes=['jpg','gif','png','jpeg']
imgdir='testimgs'
q = Queue(t.width*t.height)
cacheDims=(t.width*t.height)
scaledImages={}
slp=0
charratio=5./8 #static for now
scalingmax=0.8

def scaleImage(path):
    global t, scaledImages, cacheDims
    if (t.width,t.height) != cacheDims: #FLUSH CACHE
        cacheDims = (t.width,t.height)
        scaledImages={}
    if path in scaledImages:
        sys.stderr.write('Recalling from memory.\n')
        return scaledImages[path]
    else:
        pixellist=[]
        img=Image.open(path)
        img.convert('RGB')
        scratio = float(t.width)/t.height
        imratio = float(img.size[0])/img.size[1]/charratio
        if imratio/scratio<scalingmax: #Too dissimilar, image is too wide
            new_w = int(t.width*imratio/scratio)
            new_h = t.height
        elif scratio/imratio<scalingmax: #Too dissimilar, image is too tall
            new_w = t.width
            new_h = int(t.height*scratio/imratio)
        else: #Similar, distort
            new_w = t.width
            new_h = t.height
        sys.stderr.write('Path: '+str(path)+'\n')
        sys.stderr.write('Screen dims: '+str(t.width)+' '+str(t.height)+'\n')
        sys.stderr.write('Dims: '+str(new_w)+' '+str(new_h)+'\n')
        img=img.resize((new_w, new_h),Image.BILINEAR)
        pixels = img.load() #Calculate the background colour
        edge = (0,0,0,0)
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                if x == 0 or x == img.size[0]-1 or y == 0 or y == img.size[1]-1:
                    c = pixels[x,y]
                    if len(c)==1:
                        c = (c,c,c)
                    edge = edge[0]+1,edge[1]+c[0],edge[2]+c[1],edge[3]+c[2]
        edgecol = (int(float(edge[1])/edge[0]),
                   int(float(edge[2])/edge[0]),
                   int(float(edge[3])/edge[0]))
        bgimg = Image.new("RGB",(t.width,t.height), edgecol)
        bgimg.paste(img,(int((t.width-new_w)/2),int((t.height-new_h)/2)))
        img = bgimg
        spixels = bgimg.load()
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                pixellist.append((x,y,spixels[x,y]))
        scaledImages[path]=pixellist
        return pixellist

def chooseSweep(lst,disptype=None):
    if disptype is None:
        disptype=random.choice(['random','left','right','top','bottom',
    'top-left','top-right','bottom-left','bottom-right'])
    if isinstance(disptype,list):
        disptype=random.choice(disptype)
    if disptype == 'random':
        random.shuffle(lst)
    if disptype == 'left':
        lst.sort(key=lambda x: x[1])
    if disptype == 'right':
        lst.sort(key=lambda x: x[1],reverse=True)
    if disptype == 'top':
        lst.sort(key=lambda x: x[0])
    if disptype == 'bottom':
        lst.sort(key=lambda x: x[0],reverse=True)
    if disptype == 'top-left':
        lst.sort(key=lambda x: x[0]+x[1])
    if disptype == 'top-right':
        lst.sort(key=lambda x: x[0]-x[1])
    if disptype == 'bottom-right':
        lst.sort(key=lambda x: x[0]+x[1],reverse=True)
    if disptype == 'bottom-left':
        lst.sort(key=lambda x: x[0]-x[1],reverse=True)
    return lst

def renderImage(path):
    global t, q
    if path is None: return
    pixellist = chooseSweep(scaleImage(path),'random')
    for pixel in pixellist:
        q.put((pixel[0],pixel[1],renderPixel(pixel[2],t)))
    q.put((0,0,t.move(0,0)))

def get():
    paths=[]
    while True:
        if len(paths)<1:
            for type in acceptablefiletypes:
                paths.extend(glob.glob(imgdir+os.sep+'*.'+type))
        r = random.choice(range(len(paths)))
        renderImage(paths.pop(r))
        sys.stderr.write(str(len(paths))+'\n')

def draw():
    global q
    while True:
        a = q.get()
        print(t.move(a[1],a[0])+a[2],end='')
        time.sleep(slp)
        sys.stdout.flush()

th = Thread(target=get)
th.daemon=True
th.start()
time.sleep(0.5)
draw()
