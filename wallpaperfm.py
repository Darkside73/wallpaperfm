#!/usr/bin/python
# Wallpaperfm.py is a python script that generates desktop wallpapers from your last.fm music profile.
# by Koant, http://www.last.fm/user/Koant
# ./wallpaper.py will display the instructions
#
# Requirements:
# . Python Imaging Library (probably already installed, available through synaptic for Ubuntu users)
# . a last.fm account and an active internet connection
#
# v. 02 Aug 2010
# Update on 02 Aug 2010: added filelist.reverse() # changed on 02Aug2010 on l.285

__author__ = 'Koant (http://www.last.fm/user/Koant)'
__version__ = '$02 Aug 2010$'
__date__ = '$Date: 2008/07/17  $'
__copyright__ = 'Copyright (c) 2008 Koant'
__license__ = 'GPL'


from urllib import urlopen
from xml.dom import minidom
import os
import os.path
import sys
from getopt import getopt
import random
import Image
import ImageDraw
import ImageFilter

def usage():
	print "Quick examples"
	print "--------------"
	print "./wallpaperfm.py -m tile -u your_lastfm_username	will generate an image with all your favorite albums tiled up in a random order."
	print "./wallpaperfm.py -m glass -u your_lastfm_username	will generate an image with a small random collection of albums, with a glassy effect."
	print "./wallpaperfm.py -m collage -u your_lastfm_username	will generate a random collage of your favorite albums."	
	
	print "\nGlobal switches:"
	print "-u, --Username: your last.fm username."
	print "-f, --Filename: the filename where the image will be saved. Username by default."
	print "-t, --Past: [overall] how far back should the profile go. One of 3month,6month,12month or overall."
	print "-O, --FinalOpacity: [80] darkness of the final image. from 0 to 100"
	print "-i, --ImageSize: [1280x1024] size of the final image. Format: numberxnumber"
	print "-c, --CanvasSize: size of the canvas. = image size by default."
	print "-e, --Cache: [wpcache] path to the cache."
	print "-x, --ExcludedList: ['http://cdn.last.fm/depth/catalogue/noimage/cover_med.gif'] excluded urls, comma separated." 
	print "-l, --Local: use a local copy of the charts. Ideal for using it offline or being kind to the last.fm servers."	

	print "\nSpecific switches for the 'tile' mode (-m tile):"
	print "-a, --AlbumSize: [130] size of the albums, in pixel."
	print "-s, --Interspace: [5]  space between in tile, in pixel."
	print "-w, --Sort: [no]  whether to sort albums by popularity."

	print "\nSpecific switches for the 'glass' mode (-m glass):"
	print "-n, --AlbumNumber: [7] number of albums to show."
	print "-d, --EndPoint: [75] controls when the shadow ends, in percentage of the album size."	
	print "-r, --Offset: [40] starting value of opacity for the shadow."

	print "\nSpecific switches for the 'collage' mode (-m collage):"	
	print "-a, --AlbumSize: [250] size of the albums, in pixel."
	print "-o, --AlbumOpacity: [90] maximum opacity of each album, from 0 to 100."
	print "-n, --AlbumNumber: [50] number of albums to show."
	print "-g, --GradientSize: [15] portion of the album in the gradient, from 0 to 100"
	print "-p, --Passes: [4] number of iterations of the algorithms."
	sys.exit()

def getSize(s):
	""" Turns '300x400' to (300,400) """
	return tuple([int(item) for item in s.rsplit('x')])

def getParameters():
	""" Get Parameters from the command line or display usage in case of problem """
	# Common Default Parameters
	Filename=''
	mode='tile'

	Profile=dict()
	Profile['Username']='Koant'
	Profile['Past']='overall'
	Profile['cache']='wpcache'
	Profile['ExcludedList']=['http://cdn.last.fm/depth/catalogue/noimage/cover_med.gif','http://cdn.last.fm/flatness/catalogue/noimage/2/default_album_medium.png','http://userserve-ak.last.fm/serve/174s/32868291.png']	
	Profile['Limit']=50	
	Profile['Local']='no'

	Common=dict();	
	Common['ImageSize']=(1280,1024)
	Common['CanvasSize']=''
	Common['FinalOpacity']=80

	## Specific Default Parameters
	# Collage
	Collage=dict();
	Collage['Passes']=4
	Collage['AlbumOpacity']=90
	Collage['GradientSize']=15
	Collage['AlbumSize']=250

	# Tile
	Tile=dict()
	Tile['AlbumSize']=130
	Tile['Interspace']=5
	Tile['Sort']='no'

	# Glass
	Glass=dict()
	Glass['AlbumNumber']=7
	Glass['Offset']=40
	Glass['EndPoint']=75

	try:
		optlist, args=getopt(sys.argv[1:], 'hu:t:n:c:f:a:o:g:O:i:m:p:s:w:e:d:r:x:l',["help", "Mode=", "Username=", "Past=", "Filename=","CanvasSize=", "ImageSize=", "FinalOpacity=", "AlbumSize=","AlbumOpacity=","GradientSize=", "Passes=", "AlbumNumber=", "Interspace=","Sort=","Cache=","Offset=","EndPoint=","ExcludedList=","Local"])
	except Exception, err:
		print "#"*20
		print str(err)
		print "#"*20 
		usage()
	if len(optlist)==0:
		usage()
	for option, value in optlist:
		if option in ('-h','--help'):
			usage()	
		elif option in ('-m','--Mode'):				# m: mode, one of Tile,Glass or Collage
			mode=value.lower()

		elif option in('-e','--Cache'):				# e: cache
			Profile['cache']=value

		elif option in('-l','--Local'):				# l: use a local copy of the charts
			Profile['Local']='yes'

		elif option in ('-u','--Username'):			# u: username (Common)
			Profile['Username']=value

		elif option in ('-t','--Past'):				# t: how far back (Common), either 3month,6month or 12month
			Profile['Past']=value
		
		elif option in ('-x','--ExcludedList'):			# x: excluded url
			Profile['ExcludedList'].extend(value.rsplit(','))

		elif option in ('-f', '--Filename'):			# f: image filename (Common)
			Filename=value

		elif option in ('-c','--CanvasSize'):			# c: canvas size (Common)
			Common['CanvasSize']=getSize(value)

		elif option in ('-i','--ImageSize'):			# i: image size (Common)
			Common['ImageSize']=getSize(value)

		elif option in ('-O', '--FinalOpacity'): 		# O: opacity of final image (Common)
			Common['FinalOpacity']=int(value)

		elif option in ('-a','--AlbumSize'):			# a: album size (Collage,Tile)
			Collage['AlbumSize']=int(value)
			Tile['AlbumSize']=int(value)

		elif option in ('-o','--AlbumOpacity'):			# o: album opacity (Collage)
			Collage['AlbumOpacity']=int(value)

		elif option in ('-g','--GradientSize'):			# g: gradient size (Collage)
			Collage['GradientSize']=int(value)

		elif option in ('-p','--Passes'):			# p: number of passes (Collage)
			Collage['Passes']=int(value)

		elif option in ('-n','--AlbumNumber'):			# n: number of albums (Glass, Collage)
			Glass['AlbumNumber']=int(value)
			Collage['AlbumNumber']=int(value)

		elif option in ('-s','--Interspace'):			# s: interspace (Tile)
			Tile['Interspace']=int(value)
		
		elif option in ('-d','--EndPoint'):			# d: EndPoint (Glass)
			Glass['EndPoint']=int(value)	
		
		elif option in ('-r','--Offset'):			# r: Offset (Glass)
			Glass['Offset']=int(value)
		elif option in ('-w','--Sort'):				# t: Sort (Tile)
			Tile['Sort']=value
	

		else:
			print "I'm not using ", option 

	if Filename=='': # by default, Filename=Username
		Filename=Profile['Username']
	if Common['CanvasSize']=='':	# by default, CanvasSize=ImageName
		Common['CanvasSize']=Common['ImageSize']

	# Add the common parameters
	for k,v in Common.iteritems():
		Collage[k]=v
		Tile[k]=v
		Glass[k]=v

	return {'Filename':Filename, 'Mode':mode, 'Profile':Profile, 'Tile':Tile, 'Glass':Glass, 'Collage':Collage}

##############################
## Parse and download the files
##############################
def makeFilename(url):
	""" Turns the url into a filename by replacing possibly annoying characters by _ """
	url=url[7:] # remove 'http://'	
	for c in ['/', ':', '?', '#', '&','%']:
		url=url.replace(c,'_')
	return url

def download(url,filename):
	""" download the binary file at url """
	instream=urlopen(url)
	outfile=open(filename,'wb')
	for chunk in instream:
		outfile.write(chunk)
	instream.close()
	outfile.close()

def IsImageFile(imfile):
	""" Make sure the file is an image, and not a 404. """
	flag=True
	try:
		i=Image.open(imfile)
	except Exception,err:
		flag=False
	return flag

def getAlbumCovers(Username='Koant',Past='overall',cache='wp_cache',ExcludedList=['http://cdn.last.fm/depth/catalogue/noimage/cover_med.gif','http://cdn.last.fm/flatness/catalogue/noimage/2/default_album_medium.png'],Limit=50,Local='no'):
	""" download album covers if necessary """
	## Preparing the file list.
	if Past in ('3month','6month','12month'):
		tpe='&type='+Past
	else:
		tpe=''

	url='http://ws.audioscrobbler.com/1.0/user/'+Username+'/topalbums.xml?limit='+str(Limit)+tpe
	
	# make cache if doesn't exist
	if not os.path.exists(cache):
		print "cache directory ("+cache+") doesn't exist. I'm creating it."	
		os.mkdir(cache)	
	
	# Make a local copy of the charts
	if Local=='no':	
		try:
			print "Downloading from ",url
			download(url,cache+os.sep+'charts_'+Username+'.xml')
		except Exception,err:
			print "#"*20
			print "I couldn't download the profile or make a local copy of it."
			print "#"*20
	else:
		print "Reading from local copy:  ",cache+os.sep+'charts_'+Username+'.xml'

	# Parse image filenames
	print "Parsing..."
	try:
		data=open(cache+os.sep+'charts_'+Username+'.xml','rb')
		xmldoc=minidom.parse(data)
		data.close()
	except Exception,err:
		print '#'*20
		print "Error while parsing your profile. Your username might be misspelt or your charts empty."
		print '#'*20		
		sys.exit()

	filelist=[imfile.firstChild.data for imfile in xmldoc.getElementsByTagName('large')]



	# Exclude covers from the ExcludedList
	filelist=[item for item in filelist if not item in ExcludedList]

	# Stop if charts are empty
	if len(filelist)==0:
		print '#'*20
		print "Your charts are empty. I can't proceed."
		print '#'*20
		sys.exit()

	# download covers only if not available in the cache
	for imfile in filelist[:]:
		url=imfile
		imfile=makeFilename(imfile)	
		if not os.path.exists(cache+os.sep+imfile):
			print "	Downloading ",url
			download(url,cache+os.sep+imfile)

	filelist=[cache+os.sep+makeFilename(imfile) for imfile in filelist] 

	filelist=[imfile for imfile in filelist if IsImageFile(imfile)] # Checks the file is indeed an image
	filelist.reverse() # changed on 02Aug2010
	return filelist

##############################
## Tile
##############################
def Tile(Profile,ImageSize=(1280,1024),CanvasSize=(1280,1024),AlbumSize=130,FinalOpacity=30,Interspace=5,Sort='no'):
	""" produce a tiling of albums covers """

	imagex,imagey=ImageSize
	canvasx,canvasy=CanvasSize

	offsetx=(imagex-canvasx)/2
	offsety=(imagey-canvasy)/2
	
	#number of albums on rows and columns
	nx=(canvasx-Interspace)/(AlbumSize+Interspace) 
	ny=(canvasy-Interspace)/(AlbumSize+Interspace)
	
	# number of images to download
	Profile['Limit']=ny*nx+len(Profile['ExcludedList'])+5 # some extra in case of 404 , even though there shouldn't be any really.

	# download images
	filelist=getAlbumCovers(**Profile)

	background=Image.new('RGB',(imagex,imagey),0) # background

	filelist2=list()
	posy=-AlbumSize+(canvasy-ny*(AlbumSize+Interspace)-Interspace)/2
	for j in range(0,ny):
		posx,posy=(-AlbumSize+(canvasx-nx*(AlbumSize+Interspace)-Interspace)/2,posy+Interspace+AlbumSize) # location of album in the canvas
		for i in range(0,nx):
			posx=posx+Interspace+AlbumSize
			if len(filelist2)==0: # better than random.choice() (minimises risk of doubles and goes through the whole list) 
				filelist2=list(filelist)
				if Sort=='no':
					random.shuffle(filelist2)
			imfile=filelist2.pop()
			try:
				im=Image.open(imfile).convert('RGB')
			except Exception,err:
				print "#"*20
				print err
				print "I couln't read that file: "+imfile
				print "You might want to exclude its corresponding URL with -x because it probably doesn't point to an image."
				print "#"*20				
				sys.exit()
			im=im.resize((AlbumSize,AlbumSize),2)		
			background.paste(im,(posx+offsetx,posy+offsety))		
		
	# darken the result
	background=background.point(lambda i: FinalOpacity*i/100)
	return background

##############################
## Glassy wallpaper
##############################
def makeGlassMask(ImageSize,Offset=50,EndPoint=75):
	""" Make mask for the glassy wallpaper """
	mask=Image.new('L',ImageSize,0)
	di=ImageDraw.Draw(mask)
	sizex,sizey=ImageSize
		
	stop=min((EndPoint*sizey)/100,sizey)
	E=EndPoint*sizey/100
	O=255*Offset/100
	for i in range(0,stop):
		color=(255*Offset/100*-100*i)/(EndPoint*sizey)+255*Offset/100 #linear gradient		
		#color=((i-E)*(i-E)*O)/(E*E) # quadratic gradient		
		#color=(O*(E*E-i*i))/(E*E)
		di.line((0,i,sizex,i),color)		
	return mask

def Glass(Profile, ImageSize=(1280,1024),CanvasSize=(1280,1024),AlbumNumber=7,FinalOpacity=100,Offset=50,EndPoint=75):
	""" Make a glassy wallpaper from album covers """ 	

	if AlbumNumber>Profile['Limit']:
		Profile['Limit']=AlbumNumber+len(Profile['ExcludedList'])+5
	
	filelist=getAlbumCovers(**Profile)
	imagex,imagey=ImageSize
		
	canvasx,canvasy=CanvasSize

	offsetx=(imagex-canvasx)/2
	offsety=(imagey-canvasy)/2

	background=Image.new('RGB',(imagex,imagey),0) # background

	albumsize=canvasx/AlbumNumber
	mask=makeGlassMask((albumsize,albumsize),Offset,EndPoint)	

	posx=(canvasx-AlbumNumber*albumsize)/2-albumsize
	
	for i in range(0,AlbumNumber):
		imfile=filelist.pop()	# assumes there are enough albums in the filelist
		tmpfile=Image.open(imfile).convert('RGB')
		tmpfile=tmpfile.resize((albumsize,albumsize),2) # make it square, prettier
		posx,posy=(posx+albumsize,canvasy/2-albumsize)
		background.paste(tmpfile,(posx+offsetx,posy+offsety)) # paste the album cover
		tmpfile=tmpfile.transpose(1)				#turn it upside down
		background.paste(tmpfile,(posx+offsetx,canvasy/2+offsety),mask)	# apply mask and paste
	# darken the result
	background=background.point(lambda i: FinalOpacity*i/100)
	return background

############################ 
## Collage
############################
def erfc(x):
	""" approximate erfc with a few splines """
	if x<-2:
		return 2;
	elif (-2<=x) and (x<-1):
		c=[ 0.9040,   -1.5927,   -0.7846,   -0.1305];
	elif (-1<=x) and (x<0):
		c=[1.0000, -1.1284,   -0.1438,    0.1419];
	elif (0<=x) and (x<1):
		c=[1.0000,   -1.1284 ,   0.1438,    0.1419];
	elif (1<=x) and (x<2):
		c=[1.0960,   -1.5927,    0.7846 ,  -0.1305];
	else:
		return 0;
	return c[0]+c[1]*x+c[2]*x*x+c[3]*x*x*x;	

def makeCollageMask(size,transparency,gradientsize):
	mask=Image.new('L',size,0)
	sizex,sizey=size
	l=(gradientsize*sizex)/100
	c=(255*transparency)/100.0
	c=c/4.0 # 4=normalizing constant from convolution
	s2=1/(l*1.4142)
	for i in range(sizex):
		for j in range(sizey):
			v=c*(erfc(s2*(l-i))-erfc(s2*(sizex-l-i)))*(erfc(s2*(l-j))-erfc(s2*(sizex-l-j)))
			mask.putpixel((i,j),int(v))
		
	return mask

def Collage(Profile,ImageSize=(1280,1024),CanvasSize=(1280,1024),AlbumNumber=50,AlbumSize=300,GradientSize=20,AlbumOpacity=70,Passes=4,FinalOpacity=70):
	""" make a collage of album covers """	

	Profile['Limit']=min(200,max(AlbumNumber,Profile['Limit'])) 

	filelist=getAlbumCovers(**Profile)

	imagex,imagey=ImageSize
	canvasx,canvasy=CanvasSize
	
	background=Image.new('RGB',(imagex,imagey),0) # background
	mask=makeCollageMask((AlbumSize,AlbumSize),AlbumOpacity,GradientSize)
	print "Computing the collage..."	
	for p in range(0,Passes):
		print "Pass ",p+1," of ",Passes	
		for imfile in filelist:
				tmpfile=Image.open(imfile).convert('RGB')
				tmpfile=tmpfile.resize((AlbumSize,AlbumSize),1)
				posx=random.randint(0,canvasx-AlbumSize)
				posy=random.randint(0,canvasy-AlbumSize)
				background.paste(tmpfile,(posx+(imagex-canvasx)/2,posy+(imagey-canvasy)/2),mask)

	# darken the result
	background=background.point(lambda i: FinalOpacity*i/100)
	return background

########################
## main
########################
def main():
	print ""
	print "	Wallpaperfm.py is a python script that generates desktop wallpapers from your last.fm musical profile."
	print "	by Koant, http://www.last.fm/user/Koant"
	print ""
	param=getParameters()
	
	print "Mode: "+param['Mode']
	print "	Image will be saved as "+param['Filename']+".jpg"
	if param['Mode']=='tile':
		for k,v in param['Tile'].iteritems():
			print "	"+k+": "+str(v)
		image=Tile(param['Profile'],**param['Tile'])		
	elif param['Mode']=='glass':
		for k,v in param['Glass'].iteritems():
			print "	"+k+": "+str(v)
		image=Glass(param['Profile'],**param['Glass'])
	elif param['Mode']=='collage':
		for k,v in param['Collage'].iteritems():
			print "	"+k+": "+str(v)
		image=Collage(param['Profile'],**param['Collage'])
	else:
		print " I don't know this mode: ", param['Mode']
		sys.exit()

	image.save(param['Filename']+'.jpg')
	print "Image saved as "+param['Filename']+'.jpg'
	
if __name__=="__main__":
	main()
