from __future__ import print_function
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource
from blessings import Terminal
from PIL import Image
import random
from bisect import bisect
import glob
import time
import sys

colours = {'black':(0,0,0),'red':(1,0,0),'green':(0,1,0),'yellow':(1,1,0),'blue':(0,0,1),'magenta':(1,0,1),'cyan':(0,1,1),'white':(1,1,1)}
colourScale = {'black':0.5,'red':1,'green':1,'yellow':0.707,'blue':1,'magenta':0.707,'cyan':0.707,'white':0.65}
charlist = [' ',".,,'",'i!c_=/|~v\\','gjezU2]/(YL)t[+T7Vf','Pmd*K4ZYGbND5QX','WMKA8','#%@&$']
fg_groups=[16,26,40,55,62,83]
overdrive=True

def colourSubtract(v1,v2,scale):
    '''Subtract a 'unit' colour from the main colour and return the remainder and magnitude.'''
    sum = (float(v1[0])*float(v2[0])*scale,float(v1[1])*float(v2[1])*scale,float(v1[2])*float(v2[2])*scale)
    mag = 0
    for n, x in enumerate(sum):
        if v2[n]!=0:
            if not overdrive: x = x/scale
            if mag==0: mag = x
            else: mag = min(mag,x)
    mag = min(max(mag,0),255)
    return (float(v1[0])-float(v2[0])*mag,float(v1[1])-float(v2[1])*mag,float(v1[2])-float(v2[2])*mag), mag

def renderPixel(colour,t,style='normal'):
    '''return the string representing a single pixel. This is expecting a 3-tuple (r,g,b), but it will handle an int as well.'''
    termfg ={'black':t.black,'red':t.red,'green':t.green,'yellow':t.yellow,'blue':t.blue,'magenta':t.magenta,'cyan':t.cyan,'white':t.white}
    termbg ={'black':t.on_black,'red':t.on_red,'green':t.on_green,'yellow':t.on_yellow,'blue':t.on_blue,'magenta':t.on_magenta,'cyan':t.on_cyan,'white':t.on_white}
    if isinstance(colour, int):
        colour = (colour,colour,colour)
    cmag = {}
    colour, cmag['white']=colourSubtract(colour,colours['white'],colourScale['white']) #Select from most complex to least.
    midcolours = ['magenta','yellow','cyan']
    random.shuffle(midcolours)
    for r in midcolours:
        colour, cmag[r]=colourSubtract(colour,colours[r],colourScale[r])
    lowcolours = ['red','blue','green']
    random.shuffle(lowcolours)
    for r in lowcolours:
        colour, cmag[r]=colourSubtract(colour,colours[r],colourScale[r])
    cmag['black']=255-sum([cmag[x]*colourScale[x] for x in cmag])/colourScale['black']
    #Find out which colour is dominant and which is second (dom = background, 2nd = foreground)
    topcolours=sorted(cmag, key=cmag.get,reverse=True)
    if style.lower()=='normal':
        bg = topcolours[0]
        fg = topcolours[1]
    elif style.lower()=='inverted':
        bg = topcolours[6]
        fg = topcolours[5]
    elif style.lower()=='topbottom':
        bg = topcolours[6]
        fg = topcolours[0]

    #This is a bit of a hack because of not having a true understanding of how the pixels work out
    row=bisect(fg_groups,cmag[fg])
    chars=charlist[row]
    return termfg[fg]+termbg[bg]+random.choice(chars)+t.normal
