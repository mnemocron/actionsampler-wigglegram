import cv2
import numpy as np
import os

USE_RELATIVE_COMPARE_CROP = False
CUSTOM_COMPARE_CROP_PX = 160
SEARCH_RADIUS_PX = 80
EXTRA_BORDER_PERCENT_OUTPUT = 20

EXTRA_BORDER_PERCENT = 0  # DO NOT USE

IMGFILE = 'imm/imm000_0.jpg'

targetdir = IMGFILE.split('.')[0]

original = cv2.imread(IMGFILE)
original = cv2.cvtColor(original, cv2.COLOR_BGR2HSV) # allignment error works better in HSV space
origh,origw,c = original.shape

# add black border on each side to have more freedom to align the image
# todo: remove, this is done at the end when placing images on each other
border_scale = 1+(EXTRA_BORDER_PERCENT/100*2)
scale_w = int(origw*border_scale)
extra_pixels = scale_w - origw
if(extra_pixels%2):
    extra_pixels += 1
bigpic = np.zeros(shape=(origh+extra_pixels,origw+extra_pixels,3)).astype('uint8')

black_h = int( extra_pixels / 2 ) # offset from black border
black_w = int( extra_pixels / 2 ) # offset from black border
bigpic[black_h:black_h+origh, black_w:black_w+origw] = original
h,w,c = bigpic.shape

## verify correct import
# cv2.imshow('testimage', bigpic)
# cv2.waitKey(3000)
# cv2.destroyAllWindows()

half_h = int(origh/2)
half_w = int(origw/2)
quart_h = int(half_h/2)
quart_w = int(half_w/2)

sub_1 = bigpic[0:half_h+black_h, 0:half_w+black_w]  # reference image
sub_2 = bigpic[0:half_h+black_h, black_w+half_w:black_w+w]
sub_3 = bigpic[black_h+half_h:black_h+h, black_w+half_w:black_w+w]
sub_4 = bigpic[black_h+half_h:black_h+h, 0:half_w+black_w]

## verify correct crop
# cv2.imshow('testimage', sub_3)
# cv2.waitKey(2000)
# cv2.destroyAllWindows()

cmp_sz = CUSTOM_COMPARE_CROP_PX
if(USE_RELATIVE_COMPARE_CROP):
    cmp_sz = int(half_h/4)

if(cmp_sz%2):
    cmp_sz += 1

cmp_sz_half = int(cmp_sz/2)

crp_1 = sub_1[black_h+quart_h-cmp_sz_half:black_h+quart_h+cmp_sz_half, black_w+quart_w-cmp_sz_half:black_w+quart_w+cmp_sz_half]
crp_2 = sub_2[black_h+quart_h-cmp_sz_half:black_h+quart_h+cmp_sz_half, quart_w-cmp_sz_half:quart_w+cmp_sz_half]
crp_3 = sub_3[quart_h-cmp_sz_half:quart_h+cmp_sz_half, quart_w-cmp_sz_half:quart_w+cmp_sz_half]
crp_4 = sub_4[quart_h-cmp_sz_half:quart_h+cmp_sz_half, black_w+quart_w-cmp_sz_half:black_w+quart_w+cmp_sz_half]

## verify correct crop
# cv2.imshow('testimage', crp_4)
# cv2.waitKey(2000)
# cv2.destroyAllWindows()

imgparts = [sub_2, sub_3, sub_4]
crpparts = [crp_2, crp_3, crp_4]

cent_h = black_h + int((half_h - black_h) / 2)
cent_w = black_w + int((half_w - black_w) / 2)

tmp = sub_1.copy()
tmp[cent_h:cent_h+10, cent_w:cent_w+10] = [255,255,0]

print(f'[ done ] opened: {IMGFILE}')

#%%
print('starting alignment ...')
offsets = [[0,0],[0,0],[0,0]]

# this is the center of the first sub picture WITH the black border
cent_h = black_h + int(half_h / 2)
cent_w = black_w + int(half_w / 2)
searchradius = SEARCH_RADIUS_PX

beg_h = cent_h - cmp_sz_half - searchradius
end_h = cent_h - cmp_sz_half + searchradius
beg_w = cent_w - cmp_sz_half - searchradius
end_w = cent_w - cmp_sz_half + searchradius

# number of commputations required
computations = (end_h-beg_h) * (end_w-beg_w)
maxerr = 3*255*cmp_sz*cmp_sz # 3 colors * max 8-bit value * square size = max error

# use 1. sub picture as reference and compare all cropped squares to the center of that one
for i in range(3):
    partimg = imgparts[i]
    lowerr = maxerr
    loww = 0
    lowh = 0
    itr = 0
    for ww in range(beg_w, end_w):
        for hh in range(beg_h, end_h):
            # croped sub image is compared against this sliding window of the reference image
            ref = sub_1[hh:hh+cmp_sz, ww:ww+cmp_sz] 
            cmp = ref - crpparts[i]
            err = np.sqrt(np.sum(np.power(cmp,2))) # L-2 norm (RMS) works better than simple difference
            if(err<lowerr):
                lowerr = err
                loww = ww
                lowh = hh
            itr += 1
        if( ww%100 == 1):
            print(f'{(itr/computations*100):.0f}% margin: {(lowerr/maxerr*100):.1f}% [{lowh},{loww}]')
    
    print(f'[ {i+1} done ]: margin: {(lowerr/maxerr*100):.1f}% [{lowh},{loww}]')
    offsets[i] = [lowh,loww]

print('offsets = ', end='')
print(offsets)

#%%

# manually correct alignment errors here:
# offsets = [[179, 225], [116, 224], [114, 319]]

# convert colorspace back to RGB
rgb_1 = cv2.cvtColor(sub_1, cv2.COLOR_HSV2BGR)
rgb_2 = cv2.cvtColor(sub_2, cv2.COLOR_HSV2BGR)
rgb_3 = cv2.cvtColor(sub_3, cv2.COLOR_HSV2BGR)
rgb_4 = cv2.cvtColor(sub_4, cv2.COLOR_HSV2BGR)
imgparts = [rgb_2, rgb_3, rgb_4]
crpp_1 = cv2.cvtColor(crp_1, cv2.COLOR_HSV2BGR)
crpp_2 = cv2.cvtColor(crp_2, cv2.COLOR_HSV2BGR)
crpp_3 = cv2.cvtColor(crp_3, cv2.COLOR_HSV2BGR)
crpp_4 = cv2.cvtColor(crp_4, cv2.COLOR_HSV2BGR)
crpparts = [crpp_2, crpp_3, crpp_4]

tmp = np.array(rgb_1 * 0.25).astype('uint8')
for i in range(3):
    lowh = offsets[i][0]
    loww = offsets[i][1]
    
    ref = sub_1[lowh:lowh+cmp_sz, loww:loww+cmp_sz] 
    cmp = np.abs(ref - crpparts[i])
    err = np.sqrt(np.sum(np.power(cmp,2)))
    print(err)
    # tmp[lowh:lowh+cmp_sz, loww:loww+cmp_sz] = np.array(cmp * 0.25).astype('uint8')
    tmp[lowh:lowh+cmp_sz, loww:loww+cmp_sz] += np.array(crpparts[i] * 0.25).astype('uint8')

cv2.imshow('testimage', tmp)
cv2.waitKey(3000)
cv2.destroyAllWindows()

#%%
# offset transformation [h, w]
# subtract the previously added offset when creating the cropped squares 
otrf = offsets.copy()
for i in range(3):
    otrf[i] = [ offsets[i][0] - (quart_h-cmp_sz_half), offsets[i][1] - (quart_w-cmp_sz_half)]
# now some of the offsets may have become negative in reference to the sub_1 reference image
# therefore sub_1 muste be moved accordingly, so that all offsets land in positive space again
# furthermote, the new image plane must grow to accomodate all offsets (avoid array index overflow)

ofsh,ofsw = np.min(otrf, 0) # smallest (most negative offsets)
grwh,grww = np.max(otrf, 0) # largest offsets
groh = 0 # grow by this amount of extra pixels
grow = 0 
# remove negative offsets by moving the reference image (sub_1)
if(ofsh < 0):
    groh = -ofsh
if(ofsw < 0):
    grow = -ofsw
# accound for positive offsets by enlarging the new image plane
if(grwh > 0 and grwh > groh):
    groh += grwh
if(grww > 0 and grww > grow):
    grow += grww

# correct all offsets for the new offset of the reference image
for i in range(3):
    otrf[i][0] += -ofsh
    otrf[i][1] += -ofsw    

# idk. why this is necessary (some extra extra pixels) so that the plane isn't too small
groh += 20
grow += 20

# flip the offset for 
if(ofsh < 0):
    ofsh *= -1
else:
    ofsh = 0 # reference plane only requires moving if offset is negative todo. is this a bug?
if(ofsw < 0):
    ofsw *= -1
else:
    ofsw = 0 # todo

# create new (larger) image to overlay all sub parts
h,w,k = rgb_1.shape
h += ofsh + groh
w += ofsw + grow
tmp = np.zeros(shape=(h,w,3)).astype('uint8')

h,w,k = rgb_1.shape

tmp[ofsh:ofsh+h, ofsw:ofsw+w] += np.array(rgb_1 * 0.25).astype('uint8')
for i in range(3):
    lowh = otrf[i][0]
    loww = otrf[i][1]
    tmp[lowh:lowh+h, loww:loww+w] += np.array(imgparts[i] * 0.25).astype('uint8')

# i = 2
# tmp[ofsh:ofsh+h, ofsw:ofsw+w] += np.array(rgb_1 * 0.5).astype('uint8')
# lowh = otrf[i][0]
# loww = otrf[i][1]
# tmp[lowh:lowh+h, loww:loww+w] += np.array(imgparts[i] * 0.5).astype('uint8')

cv2.imshow('testimage', tmp)
cv2.waitKey(3000)
cv2.destroyAllWindows()

#%%
h,w,k = rgb_1.shape
h += ofsh + groh
w += ofsw + grow

# add extra black border to allow custom cropping of the video later
border_scale = 1+(EXTRA_BORDER_PERCENT_OUTPUT/100*2)
scale_w = int(w*border_scale)
extra_pixels = scale_w - w
if(extra_pixels%2):
    extra_pixels += 1
half_pixels = int(extra_pixels/2)
    
h,w,k = rgb_1.shape

tmp = np.zeros(shape=(h+extra_pixels,w+extra_pixels,3)).astype('uint8')
for i in range(4):
    if(i == 0):
        lowh = ofsh + half_pixels
        loww = ofsw + half_pixels
        tmp[lowh:lowh+h, loww:loww+w] += np.array(rgb_1 * 0.25).astype('uint8')
    else:
        lowh = otrf[i-1][0] + half_pixels
        loww = otrf[i-1][1] + half_pixels
        tmp[lowh:lowh+h, loww:loww+w] += np.array(imgparts[i-1] * 0.25).astype('uint8')

cv2.imshow('testimage', tmp)
cv2.waitKey(3000)
cv2.destroyAllWindows()

#%%
outdir = f'./{targetdir}'
# if(os.path.isdir(outdir)):
#     os.remove(outdir)
os.mkdir(outdir)

for i in range(4):
    tmp = np.zeros(shape=(h+extra_pixels,w+extra_pixels,3)).astype('uint8')
    if(i == 0):
        lowh = ofsh + half_pixels
        loww = ofsw + half_pixels
        tmp[lowh:lowh+h, loww:loww+w] = np.array(rgb_1 * 1.0).astype('uint8')
    else:
        lowh = otrf[i-1][0] + half_pixels
        loww = otrf[i-1][1] + half_pixels
        tmp[lowh:lowh+h, loww:loww+w] = np.array(imgparts[i-1] * 1.0).astype('uint8')
    fname = f'{outdir}/{targetdir}_{i}.jpg'
    cv2.imwrite(fname, tmp)
    
