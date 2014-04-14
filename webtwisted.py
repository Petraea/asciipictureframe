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

#Set up the terminal.
t = Terminal()
print (t.hide_cursor)
print (t.enter_fullscreen)

#inbuilt consts
acceptablefiletypes=['jpg','gif','png','jpeg']
colors = {'black':(0,0,0),'red':(1,0,0),'green':(0,1,0),'yellow':(1,1,0),'blue':(0,0,1),'magenta':(1,0,1),'cyan':(0,1,1),'white':(1,1,1)}
termfg ={'black':t.black,'red':t.red,'green':t.green,'yellow':t.yellow,'blue':t.blue,'magenta':t.magenta,'cyan':t.cyan,'white':t.white}
termbg ={'black':t.on_black,'red':t.on_red,'green':t.on_green,'yellow':t.on_yellow,'blue':t.on_blue,'magenta':t.on_magenta,'cyan':t.on_cyan,'white':t.on_white}
charlist = [' ',".,,'",'i!c_=/|~v\\','gjezU2]/(YL)t[+T7Vf','Pmd*K4ZYGbND5QX','WMKA8','#%@&$']
fg_groups=[16,26,40,55,62,83]

class FormPage(Resource):
    '''Make a very simple webpage to control various parameters.'''
    def render_GET(self, request):
        return '<html><body><form method="POST">Interval:<input name="interval" type="number" value="%s"><br>Character Print time:<input name="charspeed" type="number" value="%s"><br>Transitions List:<input name="transitiontype" type="text" value="%s"><input type="submit" value="Submit"></form></body></html>' % (c.sleeptime,c.charrate,','.join(c.displaytype))

    def render_POST(self, request):
        c.sleeptime = float(request.args['interval'][0])
        if eng:
            eng.interval = float(request.args['interval'][0])
            eng._reschedule() #Immediately reschedule the screen refresh.
        c.displaytype = request.args['transitiontype'][0].split(',')
        c.charrate = float(request.args['charspeed'][0])
        return '<html><body>Submitted.</body></html>'

#Spawn this page whenever the reactor gets a request on port 80.
#You might want to use authbind to do this exact thing.
#(Start script with 'authbind python webtwisted.py')
root = Resource()
root.putChild("", FormPage())
factory = Site(root)
reactor.listenTCP(80, factory)

class BlessingsASCII():
    def __init__(self):
        '''Initialise constants.'''
        self.imgdir='testimgs/'
        self.colorscale = {'black':0.5,'red':1,'green':1,'yellow':0.707,'blue':1,'magenta':0.707,'cyan':0.707,'white':0.65} #Colour palette.
        #self.colorscale = {'black':1,'red':1,'green':1,'yellow':1,'blue':1,'magenta':1,'cyan':1,'white':1}
        if self.imgdir[-1]!='/':self.imgdir=self.imgdir+'/'
        self.sleeptime=5 #Delay on each picture
        self.charrate = 0.0000 #Pause time per character.
        self.displaytype = ['left','right','top','bottom','top-left','top-right','bottom-left','bottom-right','random'] #Default transition types.
        self.scalingmax = 0.8 #Maximum difference between screen and image to distort the image. From 0 (always scale) to 1 (always distort).
        self.overdrive=False #Overdrive allows bleeding of colours into thenext tier. I kind of like it, but YMMV.
        self.images = []

    def colorSubtract(self,v1,v2,scale):
        '''Subtract a 'unit' color from the main color and return the remainder and magnitude.'''
        sum = (float(v1[0])*float(v2[0])*scale,float(v1[1])*float(v2[1])*scale,float(v1[2])*float(v2[2])*scale)
        mag = 0
        for n, x in enumerate(sum):
            if v2[n]!=0:
                if not self.overdrive: x = x/scale
                if mag==0: mag = x
                else: mag = min(mag,x)
        mag = min(max(mag,0),255)
        return (float(v1[0])-float(v2[0])*mag,float(v1[1])-float(v2[1])*mag,float(v1[2])-float(v2[2])*mag), mag

    def renderPixel(self,colour):
        '''return the string representing a single pixel. This is expecting a 3-tuple (r,g,b), but it will handle an int as well.'''
        if isinstance(colour, int):
            colour = (colour,colour,colour)
        cmag = {}
        colour, cmag['white']=self.colorSubtract(colour,colors['white'],self.colorscale['white']) #Select from most complex to least.
        midcolors = ['magenta','yellow','cyan']
        random.shuffle(midcolors)
        for r in midcolors:
            colour, cmag[r]=self.colorSubtract(colour,colors[r],self.colorscale[r])
        lowcolors = ['red','blue','green']
        random.shuffle(lowcolors)
        for r in lowcolors:
            colour, cmag[r]=self.colorSubtract(colour,colors[r],self.colorscale[r])
        cmag['black']=255-sum([cmag[x]*self.colorscale[x] for x in cmag])/self.colorscale['black']
        #Find out which colour is dominant and which is second (dom = background, 2nd = foreground)
        topcolors=sorted(cmag, key=cmag.get,reverse=True)
        sys.stderr.write(str(cmag)+'\n')
        bg = topcolors[0]
        fg = topcolors[1]

        row=bisect(fg_groups,cmag[fg])
        chars=charlist[row]
        return termfg[fg]+termbg[bg]+random.choice(chars)+t.normal

    def renderImage(self,img):
        '''use PIL to render and reduce an image to the screen size.
        It will return a list of tuples of the form (y,x,str) where y is the row, x is the column and the str is the representation of the pixel there.'''
        try:
            im=Image.open(img)
            im.load()
            im.convert('RGB')
            scratio = float(t.width)/t.height
            imratio = float(im.size[0])/im.size[1]
            if imratio/scratio<self.scalingmax: #Too dissimilar, image is too wide
                new_w = int(t.width*imratio/scratio)
                new_h = t.height
                fg=im.resize((new_w, new_h),Image.BILINEAR)
                im = Image.new("RGB",(t.width,t.height), (255,255,255))
                im.paste(fg,(int((t.width-new_w)/2),int((t.height-new_h)/2)))
            elif scratio/imratio<self.scalingmax: #Too dissimilar, image is too tall
                new_w = t.width
                new_h = int(t.height*scratio/imratio)
                fg=im.resize((new_w, new_h),Image.BILINEAR)
                im = Image.new("RGB",(t.width,t.height), (255,255,255))
                im.paste(fg,(int((t.width-new_w)/2),int((t.height-new_h)/2)))
            else: #Similar, distort
                new_w = t.width
                new_h = t.height
                im=im.resize((new_w, new_h),Image.BILINEAR)
        except:
            return []
        ilist=[]
        for y in range(0,im.size[1]):
            for x in range(0,im.size[0]):
                ilist.append((y,x,self.renderPixel(im.getpixel((x,y)))))
        return ilist

    def testFont(self):
        '''A testing function to debug colouring functions'''
        ilist = []
        for r in range(0,255,t.width):
            for g in range(0,255,t.height):
                for b in range(0,255,t.height):
                    ilist.append((r,g,self.renderPixel((r,g,b))))
        return ilist

    def nPrint(self,lst,slp=0,disptype='none'):
        '''A print function that is capable of printing to the terminal with different styles.'''
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
        for n, m, x in lst:
            print(t.move(n,m)+x,end='')
            time.sleep(slp)
            if slp>0:
                sys.stdout.flush()
        print (t.move(0,0))

    def output(self):
        if self.images ==[]:
            for type in acceptablefiletypes:
                self.images.extend(glob.glob(self.imgdir+'*.'+type))
        r = random.choice(range(len(self.images)))
        sys.stderr.write(self.images[r]+'\n')
        self.nPrint(self.renderImage(self.images.pop(r)),self.charrate,random.choice(self.displaytype))

#Used to run frontend operations. curses-printing isn't thread-safe!
def callThread():
    reactor.callInThread(c.output)

c = BlessingsASCII()
eng = LoopingCall(callThread)
eng.start(c.sleeptime,True)

reactor.run()
