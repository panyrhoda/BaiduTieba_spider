'''
Github: panyrhoda
https://github.com/panyrhoda/BaiduTieba_spider
'''
from tkinter import *
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import urllib.request
import re
import urllib.error
import operator
import urllib.parse
import time
import sys
import os
import queue, threading
from tkinter import ttk

class Tool:  

	#替换img标签 
	Img = re.compile('<img.*?>')  
	#删除超链接标签&长空格
	Addr = re.compile('<a.*?>|</a>| {4,7}')  
	
	def replaceImg(self, x):
		x = re.sub(self.Img,"[imgtag]",x)
		return x
	
	def removeAddr(self, x):
		x = re.sub(self.Addr,"",x)
		return x
	
	def replaceall(self, x):
		item = x.group(1)
		item = self.replaceImg(item)  
		item = self.removeAddr(item)
		return item.strip() 
		
	def get_str(self, page_html, regexp):
		pattern = re.compile(regexp, re.S)
		result = re.finditer(pattern, page_html)
		if result:
			findlist = []
			for item in result:
				x = item.group(1)
				findlist.append(x)
			return findlist
		return None		
		
	def get_page_html(self, url):
		try:
			request = urllib.request.Request(url)  
			response = urllib.request.urlopen(request)
			try:
				return response.read().decode()
			except UnicodeDecodeError as e:
				self.handle_error(e, url, "解码失败，请检查输入")
				return None
		except (urllib.error.URLError,ConnectionResetError,TimeoutError) as e:
			self.handle_error(e, url, "连接百度贴吧失败,错误原因:")
			return None
		
	def handle_error(self, e, url, msgtxt):
		if hasattr(e, "reason"):
			print("\nConnect to "+ url +" failed")
			print(msgtxt)
			print(e.reason)

class BDTieba_All:

	# 初始化
	def __init__(self):
		
		# 基础的url
		self.BASE_URL   = "https://tieba.baidu.com/f?ie=utf-8&kw="
		# 问号以前的url
		self.FRONT_URL  = "https://tieba.baidu.com/f"
		# 所有帖子的url不重复
		self.posturls   = set()
		# 引用共通方法
		self.tool       = Tool()  
		
	# 开始入口
	def start(self, keyword):
		# 起始url
		url = self.BASE_URL + urllib.parse.quote(keyword)
		# 查找所有url
		while url != self.FRONT_URL:
			
			page_html = None
			page_html = self.get_page_html(url)
			# 没有page_html则无法继续
			if page_html == None:
				return None
			
			pid_urls = None
			pid_urls = self.get_posturl(page_html)
			# Check None
			if pid_urls != None:
				self.posturls.update(pid_urls)
			
			# 下一页
			tail = None
			tail = self.get_next(page_html)
			url = None
			if tail:
				url = self.FRONT_URL + tail
			else:
				url = self.FRONT_URL
		return None
		
	# 得到页面的html代码
	def get_page_html(self, url):
		page_html = None
		page_html = self.tool.get_page_html(url)
		return page_html
			
	# 获取页面帖子url
	def get_posturl(self, page_html):
		regexp = '''data-field='{&quot;id&quot;:(.*?),&quot;'''
		findlist = self.tool.get_str(page_html, regexp)
		return findlist
		
	# 获取下一页url
	def get_next(self, page_html):
		next_pattern = re.compile('''<a href="//tieba.baidu.com/f(.*?)" class="next pagination-item " >''', re.S)
		result = re.search(next_pattern, page_html)
		# 再处理
		if result:
			all = result.group(0)
			page_pattern = re.compile('''<a href="//tieba.baidu.com/f(.*?)" class=" pagination-item " >''', re.S)
			findlist = re.finditer(page_pattern, all)
			# 删除"pagination-item"，以获得"next pagination-item"
			if findlist:
				trans = all
				for item in findlist:
					x = item.group(0)
					trans = trans.replace(x, '')
				
				result = re.search(next_pattern, trans)
				if result:
					return result.group(1)
		return None
		
class BDTieba(object):

	# 初始化
	def __init__(self):
		
		# 基础的url
		self.BASE_URL   = "https://tieba.baidu.com/p/"
		'''
		# 将要读取的页数
		self.page_index = 1
		'''
		# 楼层
		self.postno     = []
		# 内容
		self.contents   = []
		# 时间
		self.time       = []
		# 用户
		self.user       = []
		# 图片
		self.pic        = None
		# 楼id
		self.pid        = []
		# 引用共通方法
		self.tool       = Tool()  

	# 得到页面的html代码
	# question_num 帖子的编号
	# see_lz       是否只看楼主
	# pn           页数
	def get_page_html(self, question_num, see_lz=1, pn=1):
		page_html = None
		url = self.BASE_URL + str(question_num) + "?see_lz=" + str(see_lz) + "&pn=" + str(pn)
		page_html = self.tool.get_page_html(url)
		return page_html

	# 获取标题
	def get_title(self, page_html):
		title_pattern = re.compile('''<h3.*?title="(.*?)" style=".*?</h3>''', re.S)
		result = re.search(title_pattern, page_html)
		if result:
			return result.group(1)
		return None

	# 获取页数
	def get_page_num(self, page_html):
		page_num_pattern = re.compile('''"total_page":(.*?)};''', re.S)
		result = re.search(page_num_pattern, page_html)
		if result:
			return int(result.group(1))
		return None

	# 从html代码中提取提取需要数据
	def get_data(self, page_html):
		# 楼层
		self.postno = self.get_str_postno(page_html)
		# 内容
		self.contents = self.get_str_contents(page_html)
		# 时间
		self.time = self.get_str_time(page_html)
		# 用户
		self.user = self.get_str_user(page_html)
		# 图片
		self.pic = self.get_pic(page_html)
		# 楼id
		self.pid = self.get_str_pid(page_html)
	
	def get_str_postno(self, page_html):
		# 楼层
		regexp = '''post_no&quot;:(.*?),&quot;'''
		findlist = self.tool.get_str(page_html, regexp)
		return findlist
		
	def get_str_contents(self, page_html):
		# 内容
		pattern = re.compile('''<div id="post_content_.*?>(.*?)</div>''', re.S)
		result = re.finditer(pattern, page_html)
		if result:
			findlist = []
			for item in result:
				# 加工评论内容
				x = self.tool.replaceall(item)
				findlist.append(x)
			return findlist
		return None
		
	def get_str_time(self, page_html):
		# 时间
		regexp = '''(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})'''
		findlist = self.tool.get_str(page_html, regexp)
		return findlist
		
	def get_str_user(self, page_html):
		# 用户
		pattern = re.compile('''&quot;user_name&quot;:&quot;(.*?)&quot;''', re.S)
		result = re.finditer(pattern, page_html)
		if result:
			findlist = []
			for item in result:
				x = item.group(1)
				# 转码获得中文
				x = x.encode()
				findlist.append(x.decode('unicode-escape'))
			return findlist
		return None
		
	def get_pic(self, page_html):
		# 图片
		return None
		
	def get_str_pid(self, page_html):
		# 楼id
		regexp = '''&quot;post_id&quot;:(.*?),&quot;'''
		findlist = self.tool.get_str(page_html, regexp)
		return findlist

class BDTiebaLZL(BDTieba):
	
	# 得到页面的html代码
	def get_page_html(self, tid, pid, pn=1):
		page_html = None
		url = self.BASE_URL + "comment?tid=" + str(tid) + "&pid=" + str(pid) + "&pn=" + str(pn)
		page_html = self.tool.get_page_html(url)
		return page_html

	# 获取页数
	def get_page_num(self, page_html):
		page_num_pattern = re.compile('''total_page&quot;:(.*?)}''', re.S)
		result = re.search(page_num_pattern, page_html)
		if result:
			return int(result.group(1))
		return None

	# 从html代码中提取提取需要数据
	def get_data(self, page_html):
		# 内容
		self.contents = self.get_str_contents(page_html)
		# 时间
		self.time = self.get_str_time(page_html)
		# 用户
		self.user = self.get_str_user(page_html)
		# 图片
		self.pic = self.get_pic(page_html)

	def get_str_contents(self, page_html):
		# 内容
		pattern = re.compile('''<span class="lzl_content_main">(.*?)</span>''', re.S)
		result = re.finditer(pattern, page_html)
		if result:
			findlist = []
			for item in result:
				x = self.tool.replaceall(item)
				findlist.append(x)
			return findlist
		return None

class FileData:

	# 初始化
	def __init__(self):
		# 楼层
		self.postno    = []
		# 楼层
		self.lzlpostno = []
		# 内容
		self.contents  = []
		# 时间
		self.time      = []
		# 用户
		self.user      = []
		
class OutputFile:

	# 初始化
	def __init__(self):
		# 默认文件名
		self.default_title = "百度贴吧"
		# 将读取的内容写入的文件
		self.file          = None
		# 获得文件属性
		self.filedata      = FileData()
		# 楼层
		self.postno        = "0"
		# 楼层
		self.lzlpostno     = "0"
		# 内容
		self.contents      = ""
		# 时间
		self.time          = ""
		# 用户
		self.user          = ""
		
	# 打开txt文件
	def open_file(self, title, mode="w+"):
		if title:
			self.file = open(title + ".txt", mode, encoding='utf-8')
		else:
			self.file = open(self.default_title, mode, encoding='utf-8')
			
	# 写入文件
	def write_file(self, leng, filedata, question_num='0'):
		if leng > 0:
			self.filedata = filedata
			idx = 0
			idxmax = leng
			
			for i in range(leng):
				idx_pre = i
								
				if (self.filedata.postno 
				and self.filedata.lzlpostno 
				and self.filedata.contents 
				and self.filedata.time 
				and self.filedata.user ):
					# 从主楼开始（避免楼中楼重复写入）
					if int(self.filedata.lzlpostno[i]) == 0:
						while(str(idx)):
							try:
								# 查找下一个相同postno的索引
								idx = self.filedata.postno.index(self.filedata.postno[i], idx_pre, idxmax)
							# 没找到则i + 1，跳过备份
							except BaseException:
								break
							# 备份开始
							# 楼层
							self.postno = self.filedata.postno[idx]
							# 楼中楼No
							self.lzlpostno = self.filedata.lzlpostno[idx]
							# 内容
							self.contents = self.filedata.contents[idx]
							# 时间
							self.time = self.filedata.time[idx]
							# 用户
							self.user = self.filedata.user[idx]
							# 写入一条
							if operator.eq(question_num, '0'):
								self.file.write(self.postno    + "\t" +
												self.lzlpostno + "\t" +
												self.contents  + "\t" +
												self.time      + "\t" +
												self.user      + "\n")
							else:
								self.file.write(self.postno    + "\t" +
												self.lzlpostno + "\t" +
												self.contents  + "\t" +
												self.time      + "\t" +
												self.user      + "\t" +
												question_num   + "\n")
											
							idx_pre = idx + 1
							
				else:
					print("错误：未爬取到数据！文件数据为空\n")
		else:
			print("错误：未爬取到数据！\n")
			

#FrontGUI
class Application_ui(Frame):

	def __init__(self, master=None):
		Frame.__init__(self, master)
		self.master.title('百度贴吧爬虫 v1.7')
		self.master.geometry('500x300')
		self.filepath = os.getcwd()
		self.createWidgets()

	def createWidgets(self):
		self.TEXT1 = "贴吧名："
		self.TEXT2 = "帖子ID："
		self.flag_all = 1
		
		#row=0
		#Radiobutton: 全吧备份
		self.radVar = IntVar()
		
		self.rad1 = Radiobutton(self.master, text="全吧备份", variable=self.radVar, value=1, command=self.rad_call)
		self.rad1.grid(column=0, row=0, padx=5, pady=10, sticky=W)
		self.rad1.select()
		
		#Radiobutton: 仅备份一个帖子
		self.rad2 = Radiobutton(self.master, text="仅备份一个帖子", variable=self.radVar, value=2, command=self.rad_call)
		self.rad2.grid(column=1, row=0, padx=5, pady=10, sticky=W)
		
		#row=1
		#keyword
		self.lab_kw = Label(self.master, text=self.TEXT1)
		self.lab_kw.grid(column=0, row=1, padx=5, pady=10, sticky=W)
		
		self.keyVar = StringVar()
		self.wordEnter = Entry(self.master, width=30, textvariable=self.keyVar)
		self.wordEnter.grid(column=1, row=1, padx=5, pady=10, sticky=W)  
		self.wordEnter.focus()
		
		#row=2
		#filepath
		self.lab_file = Label(self.master, text="保存到：")
		self.lab_file.grid(column=0, row=2, padx=5, pady=10, sticky=W)
		
		self.fileVar = StringVar()
		self.fileVar.set(self.filepath)
		self.fileEnter = Entry(self.master, width=45, textvariable=self.fileVar)
		self.fileEnter.grid(column=1, row=2, padx=5, pady=10, sticky=W)
		
		#search help
		self.btn1 = Button(self.master, text='...', command=self.searchhelp)
		self.btn1.grid(column=2, row=2, padx=5, pady=10, sticky=W)
		
		#row=3
		#see_lz
		self.cbVar = IntVar()
		self.cb = Checkbutton(self.master, text='是否只看楼主', variable=self.cbVar, onvalue=1, offvalue=0)
		self.cb.grid(column=0, row=3, padx=5, pady=10, sticky=W)
		
		#Run
		self.btn = Button(self.master, text='Run', command=self.start)
		self.btn.grid(column=1, row=3, padx=5, pady=10, sticky=E)
		
		#row=4
		#Message
		self.lab_msg = Label(self.master, height=5, width=65, wraplength =450, justify = 'left', anchor = 'sw', text="")
		self.lab_msg.grid(column=0, row=4, rowspan=3, columnspan=2, padx=5, pady=10, sticky=W)
		
		#row=4
		#progressbar
		self.progress = IntVar()
		self.progress_max = 100
		self.progressbar = ttk.Progressbar(self.master, mode='determinate', orient=HORIZONTAL, variable=self.progress, maximum=self.progress_max)
		self.progressbar.grid(column=1, row=6, rowspan=3, padx=5, pady=10, sticky=E)
		self.progress.set(0)
		
	def rad_call(self):
		rad_select = self.radVar.get()
		self.flag_all = rad_select
		if rad_select == 1:
			self.lab_kw.config(text=self.TEXT1)
		elif rad_select == 2:
			self.lab_kw.config(text=self.TEXT2)
			
	def searchhelp(self):
		self.filepath = fd.askdirectory()
		self.fileVar.set(self.filepath)
		
	def saveto1(self):
		self.choice_save = False
		if self.flag_all == 1:
			self.choice_save = mb.askyesno('提示', '是否全部保存到1个txt？')
			
	def checkpath(self):
		self.flg_ckpath = True
		if not os.path.isdir(self.filepath):
			self.flg_ckpath = False
			mb.showerror('错误','保存路径不存在，请输入有效路径')
			
	def statecontrol(self, flag):
		if flag:
			self.rad1.config(state='normal')
			self.rad2.config(state='normal')
			self.wordEnter.config(state='normal')
			self.fileEnter.config(state='normal')
			self.btn1.config(state='normal')
			self.cb.config(state='normal')
			self.btn.config(state='normal')
		else:
			self.rad1.config(state='disabled')
			self.rad2.config(state='disabled')
			self.wordEnter.config(state='disabled')
			self.fileEnter.config(state='disabled')
			self.btn1.config(state='disabled')
			self.cb.config(state='disabled')
			self.btn.config(state='disabled')
	
	def start(self):
		
		print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())))
		
		self.msgtext = ""
		self.lab_msg.config(text=self.msgtext)
		self.see_lz = self.cbVar.get()
		self.keyword = self.keyVar.get()
		self.checkpath()
		if self.flg_ckpath == True:
			
			self.statecontrol(False)
			
			if not (mb.askyesno('提示', '是否开始检索？')):
				self.statecontrol(True)
				return
			
			new_thread_1 = threading.Thread(target=self.subthread)
			new_thread_1.start()
			self.runflag_main = True
			self.pgs_value = 0
			self.master.after(100, self.listen_for_result)
		
	def subthread(self):
		
		urls = set()
		
		bdtb_all = BDTieba_All()
		
		# 单贴备份
		if self.flag_all != 1:
			
			urls.add(self.keyword)
			self.flag_tbc = mb.askyesno('提示', '是否开始备份')
			
		# 全吧备份
		else:
			# 进度条
			self.looptxt = "正在获取全部帖子地址，请稍等"
			self.runflag_loop = True
			new_thread_2 = threading.Thread(target=self.run_loop)
			new_thread_2.start()
			
			# 获得所有url，做2次
			for i in range(2):
				bdtb_all.start(self.keyword)
				
				if(bdtb_all.posturls == None):
					continue
				urls.update(bdtb_all.posturls)
				bdtb_all.posturls.clear()
				
			if self.runflag_main == False:
				return
				
			self.runflag_loop = False
			self.flag_tbc = False
			
			if len(urls) == 0:
				self.msgtext = "未获得帖子地址，请重新输入贴吧名"
				self.statecontrol(True)
				return
			else:
				self.msgtext = "已获取" + str(len(urls)) + "个地址"
				self.flag_tbc = mb.askyesno('提示', '是否开始备份')
				
		if self.flag_tbc == False:
			self.msgtext = "Nothing done."
			self.statecontrol(True)
			return
		
		self.saveto1()
		
		self.looptxt = "备份中，已处理0个帖子"
		self.runflag_loop = True
		new_thread_3 = threading.Thread(target=self.run_loop)
		new_thread_3.start()
		
		# 进度条
		max_steps = len(urls)
		step = 0
		
		if self.runflag_main == False:
			return
		
		# 开始备份
		outputfile = OutputFile()
		
		for question_num in urls:
			
			if self.runflag_main == False:
				return
			
			page_index = 1
			bdtb = BDTieba()
			filedata = FileData()
			
			title = None
			page_html = bdtb.get_page_html(question_num, self.see_lz, page_index)
			if page_html == None:
				continue
				
			title = bdtb.get_title(page_html)
			page_num = bdtb.get_page_num(page_html)
			
			if title:
				for i in range(page_num):
					
					bdtb.get_data(page_html)
					
					filedata.postno.extend(bdtb.postno)
					filedata.contents.extend(bdtb.contents)
					filedata.time.extend(bdtb.time)
					filedata.user.extend(bdtb.user)
					filedata.lzlpostno.extend( ['0'] * len(bdtb.postno) )	
						
					for p in range(len(bdtb.postno)):
						#/楼中楼/
						pid = bdtb.pid[p]
						lzl_page_index = 1
						lzlpostno = 1
						bdtblzl = BDTiebaLZL()
						
						lzl_page_num = 0
						lzl_page_html = bdtblzl.get_page_html(question_num, pid, 1)
						
						if lzl_page_html == None:
							continue
							
						lzl_page_num = bdtblzl.get_page_num(lzl_page_html)
						if lzl_page_num != 0:
							for j in range(lzl_page_num):
								bdtblzl.get_data(lzl_page_html)
								
								filedata.contents.extend(bdtblzl.contents)
								filedata.time.extend(bdtblzl.time)
								filedata.user.extend(bdtblzl.user)
								for k in range(len(bdtblzl.time)):
									filedata.postno.append(bdtb.postno[p])
									filedata.lzlpostno.append(str(lzlpostno))
									lzlpostno += 1
									
								# 下一页
								if lzl_page_index != lzl_page_num:
									lzl_page_index += 1
									lzl_page_html = bdtblzl.get_page_html(question_num, pid, lzl_page_index)
						
					# 下一页
					if page_index != page_num:
						page_index += 1
						page_html = bdtb.get_page_html(question_num, self.see_lz, page_index)
				
				# 文件输出
				leng = len(filedata.postno)
				if self.choice_save == False:
					# 分贴保存
					outputfile.open_file(self.filepath+'/'+title)
					outputfile.file.write("楼层No"   + "\t" +
										  "楼中楼No" + "\t" +
										  "内容"     + "\t" +
										  "时间"     + "\t" +
										  "用户"     + "\n")
					outputfile.write_file(leng,filedata)
				else:
					# 保存到1个文件
					outputfile.open_file(self.filepath+'/'+self.keyword, "a+")
					outputfile.file.write("楼层No"   + "\t" +
										  "楼中楼No" + "\t" +
										  "内容"     + "\t" +
										  "时间"     + "\t" +
										  "用户"     + "\t" +
										  "帖子ID"   + "\n")
					outputfile.write_file(leng,filedata,question_num)
			else:
				print("\n" + "错误：备份失败 贴子不存在（ID:" + question_num + "）\n")
				
			step = step + 1 
			self.pgs_value = step / max_steps * 100
			
			self.looptxt = "备份中，已处理" + str(step) + "个帖子"
			
		self.runflag_main = False
		self.runflag_loop = False
	
	def run_loop(self):
		i = 0
		while(self.runflag_loop):
			j = i % 3 + 1
			self.msgtext = self.looptxt + "."*j
			time.sleep(0.5)
			i = i + 1
			
	def listen_for_result(self):
		self.lab_msg.config(text=self.msgtext)
		self.progress.set(self.pgs_value)
		
		if self.runflag_main == True:
			self.master.after(100, self.listen_for_result)
		else:
			self.progress.set(0)
			self.lab_msg.config(text="备份结束")
			self.statecontrol(True)
			print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())))

class Application(Application_ui):

    def __init__(self, master=None):
        Application_ui.__init__(self, master)

if __name__ == "__main__":
	window = Tk()
	app = Application(window)
	app.mainloop()
	app.runflag_main = False
	app.runflag_loop = False