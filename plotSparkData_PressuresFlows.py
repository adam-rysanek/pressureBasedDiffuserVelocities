__author__ = 'adamrysanek'

import csv
import Tkinter as Tk
import tkFont
import requests
import datetime
import eventlet

from tkFileDialog import asksaveasfilename
from tkFileDialog import askopenfilename
global UpstreamFlow
global StaticFlowWidget
global Titles
global measuredPressures
global access_token
global WidgetInfo
global variableFromCore
global StartStop
global pressureList
global WindowConfiguration

eventlet.monkey_patch()
WindowConfiguration = []
WidgetInfo = []
Titles = []
UpstreamFlow = 0

# USER INPUT - Provide Spark Core access token and variable to pull from sensors as named by REST API
# ---------------------------------------------------------------------------------------------------
StartStop=0
access_token = '5703d71eab3d5437b38bfa5c5be75ee5c0e86e3b'
variableFromCore = 'deltap'

# USER INPUT - Describe list of SparkCore sensors
# ----------------------------------------------------------------------

# Name = Name of SparkCore sensor or otherwise the window title name for custom estimated values
# PlCf = Configuration of plenum box, as per user input below
# SubName = Name of any SparkCore sensor who's value is used for a calculation
# CalcNam = Name of any custom calculation formula, as per user input below
# UnitMa = Units of main variable to display in window
# UnitSub = Units of sub variable to display in window (optional, set to null to omit)

# KEY ---------------------[ Name	   ,PlCf , SubName    ,CalcNme,UnMa ,UnSub]
#WindowConfiguration.append(['GAGARIN' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['GANZHI' ,  1  , ''         ,''     ,'L/s','Pa' ])
WindowConfiguration.append(['GRIZZLY' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['STARBUCK' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['TEKANAN' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['CLETUS' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['PEACHES' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['APOLLO' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['NAPOLEON' ,  1  , ''         ,''     ,'L/s','Pa' ])
WindowConfiguration.append(['OLDYELLER' ,  1  , ''         ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['MORTIMER' ,  1  , ''         ,''     ,'L/s','Pa' ])

#WindowConfiguration.append(['OLDYELLER'   ,  2  ,'MORTIMER'  ,''     ,'L/s','Pa' ])
#WindowConfiguration.append(['ESTIMATED',  0  ,''          ,'diff1','L/s',''   ])

# Template list of SparkCores if needed for above:
#WindowConfiguration.append(['MORTIMER,....])
#WindowConfiguration.append(['CLETUS,....])
#WindowConfiguration.append(['GAGARIN,....])
#WindowConfiguration.append(['PEACHES,....])
#WindowConfiguration.append(['GRIZZLY,....])
#WindowConfiguration.append(['KIANWEE,....])
#WindowConfiguration.append(['APOLLO,....])
#WindowConfiguration.append(['STARBUCK,....])
#WindowConfiguration.append(['GANZHI,....])
#WindowConfiguration.append(['NAPOLEON,....])


# USER INPUT - Customized equations for estimating a parameter based on other sensor
# or static values
# --------------------------------------------------------------------------------
def SumsAndDiffs(variable,i,valueList,UpFlow):
	# valueList is a list of all previously calculated air flows, with each row, x,
	# equivalent to each row in WindowConfiguration

	# Equation 1:
	#StaticFlow=145
	if variable == 'diff1':
		Flow = UpFlow - valueList[0]
		return Flow
	## Equation 2:
	#if variable == 'diff2':
	#	... do something
	#	... return something
	## Equation 3:.. and so on

class calculateValues():
	def __init__(self,UpFlow):
		ratios = grabRatios()
		API = APIcall(variableFromCore,access_token)
		valueList = []
		pressureList = []
		length = len(WindowConfiguration)
		for i in range(0,length):
			if WindowConfiguration[i][1]==0:
				calculatedValue = SumsAndDiffs(WindowConfiguration[i][3],i,valueList,UpFlow)
				valueList.append(calculatedValue)
				setattr(self,WindowConfiguration[i][0]+'flow',calculatedValue)
			elif WindowConfiguration[i][1]==1:
				NPorts = WindowConfiguration[i][1]
				DownstreamFlow = WindowConfiguration[i][2]
				pressureCalc = GrabSensorData(getattr(API,WindowConfiguration[i][0]),WindowConfiguration[i][0])
				if hasattr(pressureCalc, 'Value'):
					deltaP = pressureCalc.Value
					pressureList.append([WindowConfiguration[i][0],deltaP])
					OpenRatio = getattr(ratios,WindowConfiguration[i][0])
					calculatedValue = FlowEstimateFromPressure(NPorts,OpenRatio,deltaP,DownstreamFlow)
					valueList.append(calculatedValue)
					setattr(self,WindowConfiguration[i][0]+'pressure',deltaP)
					setattr(self,WindowConfiguration[i][0]+'flow',calculatedValue)
				else:
					setattr(self,WindowConfiguration[i][0]+'pressure',-999)
					setattr(self,WindowConfiguration[i][0]+'flow',-999)
			elif WindowConfiguration[i][1]==2:
				NPorts = WindowConfiguration[i][1]
				DownstreamFlow = WindowConfiguration[i][2]
				pressureCalc = GrabSensorData(getattr(API,WindowConfiguration[i][0]))
				if hasattr(pressureCalc, 'Value'):
					deltaP = pressureCalc.Value
					pressureList.append([WindowConfiguration[i][0],deltaP])
					OpenRatio = getattr(ratios,WindowConfiguration[i][0])
					DownstreamFlowValue = getattr(self,DownstreamFlow+'flow')
				calculatedValue = FlowEstimateFromPressure(NPorts,OpenRatio,deltaP,DownstreamFlowValue)
				valueList.append(calculatedValue)
				setattr(self,WindowConfiguration[i][0]+'pressure',deltaP)
			else:
				setattr(self,WindowConfiguration[i][0]+'pressure',-999)
				setattr(self,WindowConfiguration[i][0]+'flow',-999)

# Pressure-estimated flowrate
# -------------------------------------------------------------------
def FlowEstimateFromPressure(NPorts,OpenRatio,deltaP,DownstreamFlow):
	if NPorts==1:
		Flow = 1*(1-float(OpenRatio))*float(deltaP)
		return Flow
	elif NPorts==2:
		Flow = 1*(1-float(OpenRatio))*float(deltaP)*float(DownstreamFlow)
		return Flow

# Generate API call string for retrieving variable data from sensor
# --------------------------------------------------------------------
class APIcall:
	def __init__(self, variable,accesstoken):
		self.MORTIMER = 'https://api.spark.io/v1/devices/54ff72066672524847340167/'+variable+'?access_token='+accesstoken
		self.CLETUS = 'https://api.spark.io/v1/devices/54ff6f066672524834591267/'+variable+'?access_token='+accesstoken
		self.OLDYELLER = 'https://api.spark.io/v1/devices/54ff6d066678574915210267/'+variable+'?access_token='+accesstoken
		self.GAGARIN = 'https://api.spark.io/v1/devices/54ff6e066678574930451067/'+variable+'?access_token='+accesstoken
		self.GANZHI = 'https://api.spark.io/v1/devices/54ff6c066672524838271267/'+variable+'?access_token='+accesstoken
		self.GRIZZLY = 'https://api.spark.io/v1/devices/54ff6c066672524817141167/'+variable+'?access_token='+accesstoken
		self.STARBUCK = 'https://api.spark.io/v1/devices/54ff69066672524819131167/'+variable+'?access_token='+accesstoken
		self.APOLLO = 'https://api.spark.io/v1/devices/54ff6b066672524829391167/'+variable+'?access_token='+accesstoken
		self.TEKANAN = 'https://api.spark.io/v1/devices/54ff6a066672524834581267/'+variable+'?access_token='+accesstoken
		self.NAPOLEON = 'https://api.spark.io/v1/devices/54ff6a066672524834411267/'+variable+'?access_token='+accesstoken
		self.PEACHES = 'https://api.spark.io/v1/devices/54ff6a066672524824141167/'+variable+'?access_token='+accesstoken


class grabRatios():
	def __init__(self):
		length=len(WidgetInfo)
		for i in range(0,length):
			if WidgetInfo[i][3]=='configLabel':
				if WidgetInfo[i][4] == "":
					setattr(self,WidgetInfo[i][1],0.0)
				else:
					setattr(self,WidgetInfo[i][1],float(WidgetInfo[i][4]))

# Get Timestamp and value from REST API call to sensor
# --------------------------------------------------------------------
class GrabSensorData:
	def __init__(self,APIstring,SensorName):
		print "Pulling data from: " + SensorName
		try:
			coreData=requests.get(APIstring,timeout=10)
			print "... retrieved successfully."
			self.Value = coreData.json()['result']
			timestamp = coreData.json()['coreInfo']['last_heard']
			ts_year = int(timestamp[0:4])
			ts_month = int(timestamp[5:7])
			ts_day = int(timestamp[8:10])
			ts_hour = int(timestamp[11:13])
			ts_min = int(timestamp[14:16])
			ts_sec = int(timestamp[17:19])
			self.TimeStamp = datetime.datetime.strftime(datetime.datetime(ts_year,ts_month,ts_day,ts_hour,ts_min,ts_sec), '%Y-%m-%d %H:%M:%S')
		except requests.exceptions.ReadTimeout as e:
			print "... not received (WiFi connection dropout?)"
		except requests.exceptions.ConnectTimeout as e:
			print "... not received (WiFi connection dropout?)"

class DraggableWindow(object):
	def __init__(self, disable_dragging =False, release_command = None):
		if disable_dragging == False:
			self.bind('<Button-1>', self.initiate_motion)
			self.bind('<ButtonRelease-1>', self.release_dragging)

		self.release_command = release_command


	def initiate_motion(self, event) :
		mouse_x, mouse_y = self.winfo_pointerxy()
		self.deltaX = mouse_x - self.winfo_x()
		self.deltaY = mouse_y - self.winfo_y()
		self.bind('<Motion>', self.drag_window)


	def drag_window (self, event) :
		mouse_x, mouse_y = self.winfo_pointerxy()
		new_x = mouse_x - self.deltaX
		new_y = mouse_y - self.deltaY

		if new_x < 0 :
			new_x = 0

		if new_y < 0 :
			new_y = 0

		self.wm_geometry("+%s+%s" % (new_x, new_y))

	def release_dragging(self, event):
		self.unbind('<Motion>')
		if self.release_command != None :
			self.release_command()

	def disable_dragging(self) :
		self.unbind('<Button-1>')
		self.unbind('<ButtonRelease-1>')
		self.unbind('<Motion>')

	def enable_dragging(self):
		self.bind('<Button-1>', self.initiate_motion)
		self.bind('<ButtonRelease-1>', self.release_dragging)

class DesktopNote(Tk.Toplevel, DraggableWindow):
	def __init__(self, parent, config):
		title = config[0]
		if config[1]==0:
			self.BG_HEADER = "#B26B00"
			self.FG_HEADER = "#ffffff"
			self.BG_NOTE = "#FFF0E0"
			self.FG_NOTE = "#000000"
		else:
			self.BG_HEADER = "#000000"
			self.FG_HEADER = "#ffffff"
			self.BG_NOTE = "#ffffff"
			self.FG_NOTE = "#000000"
			self.BG_DIFFUSER = "#777777"
			self.FG_DIFFUSER = "#ffffff"

		# Initialize note window
		Tk.Toplevel.__init__(self, parent)
		DraggableWindow.__init__(self)
		self.overrideredirect(True)
		self.wm_geometry("%sx%s" % (95, 72))

		# Create title frame, with name (e.g., MORITMER)
		frameNote = Tk.Frame(self,bg=self.BG_NOTE, bd=1, highlightbackground='black',highlightcolor='black',highlightthickness=1)
		frameNote.pack(expand=Tk.YES,fill=Tk.BOTH)
		setattr(self,title,Tk.Frame(frameNote))
		wNote = getattr(self,title)
		wNote.pack(expand=Tk.YES,fill=Tk.BOTH)
		Header = Tk.Frame(wNote, bg=self.BG_HEADER)
		Header.pack(expand=Tk.YES,fill=Tk.X)
		titleLabel = Tk.Label(Header, text = title, fg=self.FG_HEADER,bg=self.BG_HEADER,font=tkFont.Font(family='Courier',size=9,weight='bold'))
		titleLabel.pack(expand=Tk.YES,side=Tk.TOP)

		# Create frame for main value to display
		MainValue = Tk.Frame(wNote, bg=self.BG_NOTE)
		MainValue.pack(expand=Tk.YES, fill=Tk.BOTH)
		valueLabel = Tk.Label(MainValue, text = '10 L/s',bg=self.BG_NOTE,font=tkFont.Font(family='Helvetica',size=18, weight='bold'))
		valueLabel.pack(expand=Tk.YES,side=Tk.TOP)

		SubValue = Tk.Frame(wNote, bg=self.BG_NOTE)
		SubValue.pack(expand=Tk.YES, fill=Tk.BOTH)
		subvalueLabel = Tk.Label(SubValue,anchor=Tk.S,text = '24 Pa',height=1,bg=self.BG_NOTE,font=tkFont.Font(family='Helvetica',size=9))
		subvalueLabel.pack(side=Tk.TOP)
		wNote.update_idletasks()

		if config[1]!=0:
			ConfigurableVariable = Tk.Frame(wNote, bg=self.BG_DIFFUSER)
			ConfigurableVariable.pack(expand=Tk.YES, fill=Tk.BOTH)
			configHeader = Tk.Label(ConfigurableVariable,anchor=Tk.CENTER,text = 'Dif.Pos.:',height=1,fg=self.FG_DIFFUSER,justify=Tk.CENTER,bg=self.BG_DIFFUSER,font=tkFont.Font(family='Courier',size=9,weight='bold'))
			configHeader.pack(expand=Tk.YES,side=Tk.LEFT)
			configLabel = Tk.Entry(ConfigurableVariable,bd=0,fg=self.FG_DIFFUSER,bg=self.BG_DIFFUSER,highlightthickness=0,justify=Tk.CENTER,font=tkFont.Font(family='Courier',size=9,weight='bold'))
			configLabel.pack(expand=Tk.YES,side=Tk.LEFT)
			wNote.update_idletasks()
			WidgetInfo.append([str(configLabel),title,subvalueLabel.winfo_geometry(),'configLabel',''])

		WidgetInfo.append([str(self),title,self.winfo_geometry(),'window',''])
		WidgetInfo.append([str(valueLabel),title,valueLabel.winfo_geometry(),'mainValue',''])
		WidgetInfo.append([str(subvalueLabel),title,subvalueLabel.winfo_geometry(),'subValue',''])

class MainWindow(Tk.Tk):
	def __init__(self):
		self.root = Tk.Tk()
		StaticFlow_title = Tk.Entry(self.root, textvariable="Main Supply Air Flow (L/s): ")
		StaticFlow_title.pack(side=Tk.LEFT)
		self.StaticFlowWidget = str(StaticFlow_title)
		StaticFlow_title.bind('<Return>', lambda event: self.refresh_values(self.StaticFlowWidget))
		UpstreamFlow = 0

		#Tk.Button(self.root, text="Create another note", command=self.create_a_new_note).pack(side=Tk.LEFT)
		Tk.Button(self.root, text="Save configuration", command=self.save_locations).pack(side=Tk.LEFT)
		Tk.Button(self.root, text="Load configuration", command=self.load_locations).pack(side=Tk.LEFT)
		Tk.Button(self.root, text="Start recording", command=self.start_rec).pack(side=Tk.LEFT)
		Tk.Button(self.root, text="Stop recording", command=self.stop_rec).pack(side=Tk.LEFT)
		# photo = Tk.PhotoImage(file="FloorPlate.gif")
		# w = Tk.Label(self.root, image=photo)
		# w.photo = photo
		# w.pack(side=Tk.BOTTOM)

		length = len(WindowConfiguration)
		for i in range(0,length):
			config = WindowConfiguration[i]
			self.create_a_new_note(config)

		#for i in range(0,3):
		#	self.title = Tk.StringVar()
		#	self.title.set(Titles[i])
		#	self.create_a_new_note()
		#	#print self.title

	def refresh_values(self,widgetName):
		w = self.root.nametowidget(widgetName)
		StaticFlowString = str(w.get())
		UpstreamFlow = float(StaticFlowString)
		print UpstreamFlow

	def create_a_new_note(self,config):
		New_note = DesktopNote(self.root, config)
		#New_note.text_box.focus()

	def start_rec(self):
		self.StartStop = 1
		self.update_clock()

	def stop_rec(self):
		self.StartStop = 0
		#New_note.text_box.focus()


	def save_locations(self):
		#print self.title
		# for i in range(0,3):
		# 	titlename = Titles[i]
		# 	label = getattr(self, titlename)
		# 	print label.winfo_geometry()
		self.regenerateInfoTables()
		name=asksaveasfilename(initialfile="WindowLocations.txt")
		length = len(WidgetInfo)
		if name == "":
			return;
		file = open(name, "w")
		for i in range(0,length):
			StringToWrite = str(WidgetInfo[i][0]) + ','
			StringToWrite += str(WidgetInfo[i][1]) + ','
			StringToWrite += str(WidgetInfo[i][2]) + ','
			StringToWrite += str(WidgetInfo[i][3]) + ','
			StringToWrite += str(WidgetInfo[i][4])
			file.write(StringToWrite + '\n')
		file.close()

		#print frameID[0]
		#self.root.focus()
		# w = self.root.nametowidget(frameID[0])
		# print w.winfo_geometry()
		# w.wm_geometry("+%s+%s" % (100, 100))
		#w.place(x=5,y=5)
		#print self.MORTIMER.winfo_geometry()
		#New_note = DesktopNote(self.root, self.title.get())
		#New_note.text_box.focus()

	def load_locations(self):
		# Head of file
		self.filename = askopenfilename(message="Select file with window locations")
		readData = csv.reader(open(self.filename,"rU"), delimiter=',')
		loadedWidgetInfo = list(readData)
		lengthWI = len(WidgetInfo)
		lengthLWI = len(loadedWidgetInfo)
		for i in range(0,lengthWI):
			if WidgetInfo[i][3]=='window':
				for j in range(0,lengthLWI):
					if loadedWidgetInfo[j][1]==WidgetInfo[i][1] and loadedWidgetInfo[j][3]=='window':
						w = self.root.nametowidget(WidgetInfo[i][0])
						w.wm_geometry(loadedWidgetInfo[i][2])
						w.update_idletasks()
			if WidgetInfo[i][3]=='configLabel':
				for j in range(0,lengthLWI):
					if loadedWidgetInfo[j][1]==WidgetInfo[i][1] and loadedWidgetInfo[j][3]=='configLabel':
						w = self.root.nametowidget(WidgetInfo[i][0])
						w.delete(0,5)
						w.insert(0,str(loadedWidgetInfo[i][4]))
						w.pack()
						w.update_idletasks()

	def regenerateInfoTables(self):
		length = len(WidgetInfo)
		for i in range(0,length):
			w = self.root.nametowidget(WidgetInfo[i][0])
			WidgetInfo[i][2] = w.winfo_geometry()
			if WidgetInfo[i][3] == 'configLabel':
				WidgetInfo[i][4] = str(w.get())

	def run(self):
		self.root.mainloop()

	def update_clock(self):
		w = self.root.nametowidget(self.StaticFlowWidget)
		StaticFlowString = str(w.get())
		UpstreamFlow = float(StaticFlowString)
		flowValues = calculateValues(UpstreamFlow)
		length = len(WidgetInfo)
		length2 = len(WindowConfiguration)
		for i in range(0,length):
			if WidgetInfo[i][3]=='mainValue':
				if hasattr(flowValues,WidgetInfo[i][1]+'flow'):
					value = getattr(flowValues,WidgetInfo[i][1]+'flow')
					w = self.root.nametowidget(WidgetInfo[i][0])
					w['text']=str(round(value,1)) + ' L/s'
			if WidgetInfo[i][3]=='subValue':
				if hasattr(flowValues,WidgetInfo[i][1]+'pressure'):
					value = getattr(flowValues,WidgetInfo[i][1]+'pressure')
					w = self.root.nametowidget(WidgetInfo[i][0])
					w['text']=str(round(value,2)) + ' Pa'
				else:
					w = self.root.nametowidget(WidgetInfo[i][0])
					w['text']=""

		if self.StartStop == 1:
			self.root.after(2000, self.update_clock)

if __name__ == '__main__':
	MainWindow().run()