import fontTools 
import glob
from fontTools.ttLib import TTFont
from pathlib import Path
from fontTools.ttLib.tables._g_l_y_f import Glyph
import subprocess
import shutil
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
import dehinter

SOURCE = Path("sources/ttf")
Path("build").mkdir(parents=True, exist_ok=True) 
BUILD = Path("build")

Path("fonts/ttc").mkdir(parents=True, exist_ok=True) 
Path("fonts/ttf/bitmap").mkdir(parents=True, exist_ok=True) 
Path("fonts/ttf/hinted").mkdir(parents=True, exist_ok=True) 
Path("fonts/ttf/unhinted").mkdir(parents=True, exist_ok=True) 

# Processing the static files

def prepareStatic():

	removeGID = []
	for ttf in SOURCE.glob("*.ttf"):	#this identifies the GIDs for the control characters in all fonts that'll be merged together
		font = TTFont(ttf)
		for glyph in ["uni0001", "uni0002", "uni0003", "uni0004", "uni0005", "uni0006", "uni0007", "uni0008", "uni0009", "uni000A", "uni000B", "uni000C", "uni000D", "uni000E", "uni000F", "uni0010", "uni0011", "uni0012", "uni0013", "uni0014", "uni0015", "uni0016", "uni0017", "uni0018", "uni0019", "uni001A", "uni001B", "uni001C", "uni001D", "uni001E", "uni001F"]:
			removeGID.append(font.getGlyphID(glyph))

	for ttf in SOURCE.glob("*.ttf"):
		print ("Processing "+str(ttf).split("/")[2])
		font = TTFont(ttf)
		OUTPUT = str(ttf)[:-4].replace("sources/ttf","build").lower()+"-Regular.ttf"

		for id in removeGID:
			font["glyf"][font.getGlyphName(id)] = Glyph() #blanks the control characters in each of the fonts
			font["hmtx"][font.getGlyphName(id)] = (0,0)

		font["hmtx"][font.getGlyphName(166)] = (341,0) #aligns the nbspace to space

		font["head"].fontRevision = 2.210

		cmap = font.getBestCmap()
		for glyph in ["uni0001", "uni0002", "uni0003", "uni0004", "uni0005", "uni0006", "uni0007", "uni0008", "uni0009", "uni000A", "uni000B", "uni000C", "uni000E", "uni000F", "uni0010", "uni0011", "uni0012", "uni0013", "uni0014", "uni0015", "uni0016", "uni0017", "uni0018", "uni0019", "uni001A", "uni001B", "uni001C", "uni001D", "uni001E", "uni001F"]:
			del cmap[list(cmap.keys())[list(cmap.values()).index(glyph)]]
		cmap4_3_1 = CmapSubtable.newSubtable(4) #creating a new cmap table to replace the existing and remove the unwanted control characters
		cmap4_3_1.platformID = 3
		cmap4_3_1.platEncID = 1
		cmap4_3_1.language = 0
		cmap4_3_1.cmap = cmap
		font["cmap"].tables = [cmap4_3_1]

		font["name"].removeNames(platformID=1) #no more Mac names
		font["name"].removeNames(langID=1042) #no localized names
		font["name"].removeNames(nameID=7) #no trademark

		if "Gulim" in str(ttf) or "Dotum" in str(ttf):
			font["name"].setName("Copyright 2024 The Gulim and Dotum Project Authors (https://github.com/googlefonts/gulim)",0,3,1,1033)
		else:
			font["name"].setName("Copyright 2024 The Batang and Gungsuh Project Authors (https://github.com/googlefonts/batang)",0,3,1,1033)

		font["name"].setName("This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",13,3,1,1033)
		font["name"].setName("https://openfontlicense.org",14,3,1,1033)

		font.save(OUTPUT)

		subprocess.check_call(
			[
				"gftools",
				"fix-hinting",
				OUTPUT
			]
		)

		shutil.move(OUTPUT+".fix",OUTPUT)

def makeTTC():
	# Creating TTC from static TTFs
	subprocess.check_call(
		[
			"fonttools",
			"ttLib",
			"build/batang-Regular.ttf",
			"build/batangChe-Regular.ttf",
			"build/gungsuh-Regular.ttf",
			"build/gungsuhChe-Regular.ttf",
			"-o",
			"fonts/ttc/batang-Regular.ttc"
		]
	)

# Subsetting the static instances for individual use
def subsetStatic():

	for ttf in BUILD.glob("*Regular.ttf"):
		fontName = str(ttf).split("/")[1]
		font = TTFont(ttf)
		cmapDict = font.getBestCmap()

		unicodes = []
		for entry in list(cmapDict.keys()):
			unicodes.append(hex(entry))

		unicodelist = str(unicodes)[1:-1].replace("', '",",")

		with open('build/glyphlist.txt', 'w') as f:
			for item in unicodes:
				f.write(item+",")

		subprocess.check_call(
		[
			"pyftsubset",
			ttf,
			"--unicodes-file=build/glyphlist.txt",
			"--glyph-names",
			"--drop-tables-=EBLC,EBDT",
			"--output-file=fonts/ttf/bitmap/"+fontName
		]
		)
		subprocess.check_call(
		[
			"pyftsubset",
			ttf,
			"--unicodes-file=build/glyphlist.txt",
			"--glyph-names",
			"--output-file=fonts/ttf/hinted/"+fontName
		]
		)
		subprocess.check_call(
		[
			"dehinter",
			"fonts/ttf/hinted/"+fontName,
			"-o",
			"fonts/ttf/unhinted/"+fontName
		]
		)

prepareStatic()
makeTTC()
subsetStatic()

shutil.rmtree("build")