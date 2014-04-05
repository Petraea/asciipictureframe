from __future__ import print_function
from blessings import Terminal
from PIL import Image
import random
import operator
from bisect import bisect
import glob
import time
import sys

#Set up the terminal.
t = Terminal()
print (t.hide_cursor)
print (t.enter_fullscreen)

#Config constants. To be shipped to a config file.
imgdir='testimgs/'
sleeptime=20
charrate = 0.001
displaytype = 'columns'

#inbuilt consts
colors = {'black':(0,0,0),'red':(1,0,0),'green':(0,1,0),'yellow':(1,1,0),'blue':(0,0,1),'magenta':(1,0,1),'cyan':(0,1,1),'white':(1,1,1)}
termfg ={'black':t.black,'red':t.red,'green':t.green,'yellow':t.yellow,'blue':t.blue,'magenta':t.magenta,'cyan':t.cyan,'white':t.white}
termbg ={'black':t.on_black,'red':t.on_red,'green':t.on_green,'yellow':t.on_yellow,'blue':t.on_blue,'magenta':t.on_magenta,'cyan':t.on_cyan,'white':t.on_white}
charlist = [' ',".,,'",'i!c_=/|~v\\','gjezU2]/(YL)t[+T7Vf','Pmd*K4ZYGbND5QX','WMKA8','#%@&$']
fg_groups=[16,26,40,55,62,83]

def colorSubtract(v1,v2):
    '''Subtract a 'unit' color from the main color and return the remainder and magnitude.'''
    sum = (v1[0]*v2[0],v1[1]*v2[1],v1[2]*v2[2])
    mag = 0
    for n, x in enumerate(sum):
        if v2[n]!=0:
            if mag==0: mag = x
            else: mag = min(mag,x)
    mag = min(max(mag,0),255)
    return (v1[0]-v2[0]*mag,v1[1]-v2[1]*mag,v1[2]-v2[2]*mag), mag

def renderPixel(colour):
    '''return the string representing a single pixel. This is expecting a 3-tuple (r,g,b), but it will handle an int as well.'''
    if isinstance(colour, int):
        colour = (colour,colour,colour)
    cmag = {}
    colour, cmag['white']=colorSubtract(colour,colors['white']) #Select from most complex to least.
    colour, cmag['yellow']=colorSubtract(colour,colors['yellow'])
    colour, cmag['magenta']=colorSubtract(colour,colors['magenta'])
    colour, cmag['cyan']=colorSubtract(colour,colors['cyan'])
    colour, cmag['red']=colorSubtract(colour,colors['red'])
    colour, cmag['green']=colorSubtract(colour,colors['green'])
    colour, cmag['blue']=colorSubtract(colour,colors['blue'])
    cmag['black']=255-sum(cmag.values())
    #Find out which colour is dominant and which is second (dom = background, 2nd = foreground)
    topcolors=sorted(cmag, key=cmag.get,reverse=True)
    bg = topcolors[0]
    fg = topcolors[1]

    row=bisect(fg_groups,cmag[fg])
    chars=charlist[row]
    return termfg[fg]+termbg[bg]+random.choice(chars)+t.normal

def renderImage(img):
    '''use PIL to render and reduce an image to the screen size.
    It will return a list of tuples of the form (y,x,str) where y is the row, x is the column and the str is the representation of the pixel there.'''
    im=Image.open(img)
    im=im.resize((t.width, t.height),Image.BILINEAR)
    ilist=[]
    for y in range(0,im.size[1]):
        for x in range(0,im.size[0]):
            ilist.append((y,x,renderPixel(im.getpixel((x,y)))))
    return ilist

def testFont():
    '''A testing function to debug colouring functions'''
    ilist = []
    for r in range(0,255,t.width):
        for g in range(0,255,t.height):
            for b in range(0,255,t.height):
                ilist.append((r,g,renderPixel((r,g,b))))
    return ilist

def nPrint(lst,slp=0,disptype='none'):
    '''A print function that is capable of printing to the terminal with different styles.'''
    if disptype == 'random':
        random.shuffle(lst)
    if disptype == 'columns':
        lst.sort(key=operator.itemgetter(1))
    if disptype == 'rows':
        lst.sort(key=operator.itemgetter(0))
    for n, m, x in lst:
        print(t.move(n,m)+x,end='')
        time.sleep(slp)
        sys.stdout.flush()
    print (t.move(0,0))

if imgdir[-1]!='/':imgdir=imgdir+'/'
images = glob.glob(imgdir+'*.[gjp][inp][fg]')

while True:
    for img in images:
        nPrint(renderImage(img),charrate,displaytype)
        time.sleep(sleeptime)
