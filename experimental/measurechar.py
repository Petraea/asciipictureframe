from PIL import Image, ImageFont, ImageDraw, ImageChops
ALGORITHM = Image.ANTIALIAS

letters='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()-=_+[]{}\|;:<,>.?/~`'
letters = letters+'"'+"'"+' '

def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((19,19)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 1.0, 0)
    bbox = diff.getbbox()
    if bbox:
        return im.crop((0,0,max(bbox[2],5),max(bbox[3],8)))
    else:
        return im.crop((0,0,5,8))

#font = ImageFont.load('Uni3-Terminus14.psf')
font = ImageFont.load_default()

def measure(char):
    img = Image.new('RGBA',(20,20),'black')
    d = ImageDraw.Draw(img, 'RGBA')
    d.text((0,0),char,font=font)
    img=trim(img) 
    img = img.resize((4,4),ALGORITHM)
    pix = img.load()
    p = []
    for y in range(1,img.size[1]):
        r=[]
        for x in range(1,img.size[0]):
            r.append((pix[x,y][0]+pix[x,y][1]+pix[x,y][2])/3)
        p.append(r)
#    img.save(char+'.png')
    return p

ltrs={}
for l in letters:
    ltrs[l]=measure(l)

order = sorted(ltrs.keys(), reverse=True, key=lambda x: sum([sum(y) for y in ltrs[x]]))
print(''.join(order))
