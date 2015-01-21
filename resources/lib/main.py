"""
	Copyright: (c) 2013 William Forde (willforde+xbmc@gmail.com)
	License: GPLv3, see LICENSE for more details
	
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.
	
	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.
	
	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Call Necessary Imports
from xbmcutil import listitem, urlhandler, plugin
import re

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		url = u"http://metalvideo.com/mobile/category.html"
		sourceCode = urlhandler.urlread(url, 604800, headers={"Cookie":"COOKIE_DEVICE=mobile"}, userAgent=2) # TTL = 1 Week
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Add Extra Items
		thumb = (plugin.getIcon(),0)
		self.add_item(label=u"-%s" % plugin.getuni(30103), thumbnail=thumb, url={"action":"PlayVideo", "url":u"http://www.metalvideo.com/randomizer.php"}, isPlayable=True)
		self.add_item(label=u"-%s" % plugin.getuni(30102), thumbnail=thumb, url={"action":"TopVideos", "url":u"http://www.metalvideo.com/topvideos.html"}, isPlayable=False)
		self.add_item(label=u"-%s" % plugin.getuni(32941), thumbnail=("recent.png",2), url={"action":"NewVideos", "url":u"http://www.metalvideo.com/newvideos.html"}, isPlayable=False)
		self.add_search("VideoList", "http://www.metalvideo.com/search.php?keywords=%s")
		
		# Loop and display each Video
		localListitem = listitem.ListItem
		for url, title, count in re.findall('<li class=""><a href="http://metalvideo.com/mobile/(\S+?)date.html">(.+?)</a>\s+<span class="category_count">(\d+)</span></li>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s (%s)" % (title, count))
			item.setParamDict(action="VideoList", url=u"http://metalvideo.com/%s" % url)
			
			# Store Listitem data
			yield item.getListitemTuple(False)

class TopVideos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(self.regex_selector(), 14400) # TTL = 4 Hours
		self.cacheToDisc= True
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_program_count)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_selector(self):
		# Fetch SourceCode
		url = u"http://metalvideo.com/topvideos.html"
		sourceCode = urlhandler.urlread(url, 604800) # TTL = 1 Week
		
		# Fetch list of Top Video Category
		topLists = [part for part in re.findall('<option value="(\S+?)"\s*>\s*(.+?)\s*</option>', sourceCode) if not u"Select one" in part[1]]
		titleList = [part[1] for part in topLists]
		
		# Display list for Selection
		ret = plugin.dialogSelect(plugin.getuni(30101), titleList)
		if ret >= 0: return topLists[ret][0]
		else: raise plugin.ScraperError(0, "User Has Quit the Top Display")
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		intCmd = int
		localListitem = listitem.ListItem
		
		# Iterate the list of videos
		for count, url, img, artist, track, views in re.findall('<tr>\s+<td align="center" class="row\d">(\d+).</td>\s+<td align="center" class="row\d" width="\d+"><a href="(\S+?)"><img src="(\S+?)" alt=".+?" class="tinythumb" width="\d+" height="\d+" align="left" border="1" /></a></td>\s+<td class="row\d">(.+?)</td>\s+<td class="row\d"><a href="\S+?">(.+?)</a></td>\s+<td class="row\d">([\d,]+)</td>\s+</tr>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s. %s - %s" % (count, artist, track))
			item.setThumb(img)
			item.setInfoDict(artist=[artist], count=intCmd(views.replace(u",",u"")))
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class NewVideos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(plugin["url"], 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Add Next Page if Exists   
		nextUrl = re.findall('<a href="(\S+?)">next \xc2\xbb</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":u"http://www.metalvideo.com/%s" % nextUrl[0]})
		
		# Iterate the list of videos
		localListitem = listitem.ListItem
		for url, img, artist, track in re.findall('<tr><td align="center" class="\w+" width="\d+"><a href="(\S+?)"><img src="(\S+?)" alt=".+?"  class="tinythumb" width="\d+" height="\d+" align="left" border="1" /></a></td><td class="\w+" width="\w+">(.+?)<td class="\w+"><a href="\S+?">(.+?)</a></td><td class="\w+">.+?</td></tr>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s - %s" % (artist, track))
			item.setThumb(img)
			item.setInfoDict(artist=[artist])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class Related(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		url = u"http://metalvideo.com/relatedclips.php?vid=%(url)s" % plugin
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.fromstring(sourceObj.read().replace("&","&amp;"))
		sourceObj.close()
		
		# Loop through each Show element
		localListitem = listitem.ListItem
		for node in tree.getiterator(u"video"):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(node.findtext(u"title"))
			item.setThumb(node.findtext(u"thumb"))
			
			# Add url Param
			url = node.findtext(u"url")
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")], updatelisting="true")
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class VideoList(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Sort Method and Crerate New Url
		if u"search.php" in plugin["url"]: url = plugin["url"]
		else:
			urlString = {u"0":u"%sdate.html", u"1":u"%sartist.html", u"2":u"%srating.html", u"3":u"%sviews.html"}[plugin.getSetting("sort")]
			url = urlString % plugin["url"]
		
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(url, 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		localListitem = listitem.ListItem
		import CommonFunctions
		
		# Add Next Page if Exists   
		nextUrl = re.findall('<a href="(\S+?)">next \xbb</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":u"http://www.metalvideo.com/%s" % nextUrl[0]})
		
		# Iterate the list of videos
		searchUrl = re.compile('<a href="(\S+?)">')
		searchImg = re.compile('<img src="(\S+?)"')
		searchSong = re.compile('<span class="song_name">(.+?)</span>')
		searchArtist = re.compile('<span class="artist_name">(.+?)</span>')
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"li", {u"class":u"video"}):
			# Fetch artist and url
			artist = searchArtist.findall(htmlSegment)[0]
			url = searchUrl.findall(htmlSegment)[0]
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s - %s" % (artist, searchSong.findall(htmlSegment)[0]))
			item.setInfoDict(artist=[artist])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Set Thumbnail Image
			image = searchImg.findall(htmlSegment)
			if image: item.setThumb(image[0])
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# When in party mode continuously play random video
		if "partymode" in plugin:
			# Add Current path to playlist
			playlist = plugin.xbmc.PlayList(1)
			playlist.add(plugin.handleThree)
			# Return video url untouched
			return self.find_video(0) # TTL = 1 Week
		
		# When randomizer is selected start partymode
		elif plugin["url"].endswith(u"randomizer.php"):
			# Clear Playlist first
			playlist = plugin.xbmc.PlayList(1)
			playlist.clear()
			# Return Video Player url Twice to start party mode playlist
			return {"url":[self.find_video(0), plugin.handleThree+"partymode=true"]}
		
		# Play Selected Video
		else:
			# Return video url untouched
			return self.find_video(57600) # TTL = 16 Hours
	
	def find_video(self, TTL):
		# Fetch Page Source
		sourceCode = urlhandler.urlread(plugin["url"], TTL, stripEntity=False)
		from xbmcutil import videoResolver
		
		# Look for Youtube Video First
		try: videoId = [part for part in re.findall('src="(http://www.youtube.com/embed/\S+?)"|file:\s+\'(\S+?)\'', sourceCode)[0] if part][0]
		except: return None
		else:
			print 
			if u"metalvideo.com" in videoId: return {"url":videoId}
			elif u"youtube.com" in videoId: return self.sources(videoId, sourcetype="youtube_com")
