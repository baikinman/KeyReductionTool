'''
keyReductionTool
Version 1.1.0, December 2016
@author = Wataru Neoi

'''


import maya.cmds as cmds
import math

#------------------------------------------------------------------------------------------------------------------------------------
##functions
def getKeyable_attrs(obj):
	keyable_attrs = cmds.listAttr(obj,keyable=True,sn=True)
	if keyable_attrs == None:
		return []
	return keyable_attrs

def fixedKey(key_tangentTypes,key_numbers):
	#define index
	fixed_index = []
	for (num,key_tangentType) in enumerate(key_tangentTypes):
		#define fixedKeyNumber and index
		fixedKeyNumber = num + key_numbers[0]
		if key_tangentType == 'step':
			continue
		else:
			fixed_index.append((fixedKeyNumber,))
	return fixed_index

def lockedKeyframe(L_KeyNameLists):
	#define index
	L_Name = []
	L_keyTimes = []
	L_keyValues = []
	L_keyOutTangents = []
	L_keyTangentTypes = []

	if L_KeyNameLists != None:
		for L_keyName in L_KeyNameLists:
			keyTC = cmds.keyframe(L_keyName,q=True,sl=True,tc=True)
			keyVC = cmds.keyframe(L_keyName,q=True,sl=True,vc=True)
			KOT = []
			KTT = []
			if keyTC != None:
				L_Name.append(L_keyName)
				L_keyTimes.append(keyTC)
				L_keyValues.append(keyVC)
				for TC in keyTC:
					KOT.append(cmds.keyTangent(L_keyName,q=True,time=(TC,TC),outAngle=True))
					KTT.append(cmds.keyTangent(L_keyName,q=True,time=(TC,TC),ott=True))
				
				KOT = [e2 for e1 in KOT for e2 in e1]
				KTT = [e2 for e1 in KTT for e2 in e1]

				L_keyOutTangents.append(KOT)
				L_keyTangentTypes.append(KTT)
			else:
				L_Name = []
				L_keyTimes = []
				L_keyValues = []
				L_keyOutTangents = []
				L_keyTangentTypes = []
	else:
		L_Name = []
		L_keyTimes = []
		L_keyValues = []
		L_keyOutTangents = []
		L_keyTangentTypes = []

	return [L_Name,L_keyTimes,L_keyValues,L_keyOutTangents,L_keyTangentTypes]
		
def common(obj,channelCheck,channelBox_attrs,appliedChannels,start,end):
	#define lists
	channels = []

	#list keyable_attrs
	keyable_attrs = getKeyable_attrs(obj)

	if channelBox_attrs == None:
		cmds.error("Select Channel")
		pass
	elif len(channelBox_attrs) == 0:
		if channelCheck =='AllKeyable':
			keyable_channels = keyable_attrs
		elif channelCheck == 'FromAttributes':
			keyable_channels = list(set(keyable_attrs)&set(appliedChannels))
	else:
		keyable_channels = list(set(keyable_attrs)&set(channelBox_attrs))

	for keyable_channel in keyable_channels:
		#append channels
		if cmds.keyframe('{0}.{1}'.format(obj,keyable_channel),q=True,t=(start,end),timeChange=True) != None:
			channels.append(keyable_channel)
		else:
			continue
	return [keyable_channels,channels]

def getReduct_index(key_outTangents,key_values,key_numbers,key_times):
	#define reduct_index list
	reduct_index = []
	r_sample = (cmds.floatSliderGrp('ReductKeySample',q=True,value=True))*30
	a = -1
	for (i,key_outTangent) in enumerate(key_outTangents):
		#define cutKeyNumber
		cutKeyNumber = i + key_numbers[0]

		if i == 0:
			#pass the first keyframe
			continue
		elif i == len(key_outTangents)-1:
			#pass the last keyframe
			continue
		else:
			if 1 < i < len(key_outTangents)-2:
				AT = key_times[i-2] - key_times[i-1]
				AV = key_values[i-2] - key_values[i-1]
				BT = key_times[i] - key_times[i-1]
				BV = key_values[i] - key_values[i-1]
				CT = -BT
				CV = -BV
				DT = key_times[i+1] - key_times[i]
				DV = key_values[i+1] - key_values[i]
				ET = -DT
				EV = -DV
				FT = key_times[i+2] - key_times[i+1]
				FV = key_values[i+2] - key_values[i+1]

				f_de = math.sqrt(AT*AT+AV*AV)*math.sqrt(BT*BT+BV*BV)
				c_de = math.sqrt(CT*CT+CV*CV)*math.sqrt(DT*DT+DV*DV)
				b_de = math.sqrt(ET*ET+EV*EV)*math.sqrt(FT*FT+FV*FV)

				f_rad = round(math.degrees(math.acos(round((AT*BT + AV*BV)/f_de,10))),2)
				c_rad = round(math.degrees(math.acos(round((CT*DT + CV*DV)/c_de,10))),2)
				b_rad = round(math.degrees(math.acos(round((ET*FT + EV*FV)/b_de,10))),2)
			else:
				f_rad = 0
				c_rad = 0
				b_rad = 0

			#except peakKey
			if (round(abs(key_outTangents[i-1]),2) - round(abs(key_outTangent),2)) * (round(abs(key_outTangent),2) - round(abs(key_outTangents[i+1]),2)) < 0:
				a = i

			elif (round(key_outTangents[i-1],4)) * (round(key_outTangents[i+1],4)) < 0:
				a = i

			elif abs((key_values[i-1] + key_values[i+1])/2 - key_values[i]) >= 1:
				continue

			elif abs(key_outTangents[i-1] - key_outTangent) < 0.01 and abs(key_outTangent - key_outTangents[i+1]) > 0.1:
				continue
			elif abs(key_outTangents[i-1] - key_outTangent) > 0.1 and abs(key_outTangent - key_outTangents[i+1]) < 0.01:
				continue

			#cut linearKey
			elif abs(key_outTangents[i-1] - key_outTangent) < 0.01 and abs(key_outTangent - key_outTangents[i+1]) < 0.01:
				if key_outTangent == 0.0:
					if abs(key_values[i-1] - key_values[i]) < 0.001 and abs(key_values[i] - key_values[i+1]) < 0.001:
						reduct_index.append((cutKeyNumber,))
					else:
						continue
				else:
					reduct_index.append((cutKeyNumber,))

			elif c_rad < f_rad and c_rad < b_rad:
				if a == i-1:
					reduct_index.append((cutKeyNumber,))
				else:
					a = i
	
			else:
				if abs(key_outTangents[i-1] - key_outTangent) < r_sample and abs(key_outTangent - key_outTangents[i+1]) < r_sample:
					reduct_index.append((cutKeyNumber,))
				else:
					continue
	return reduct_index

def getstatic_index(key_outTangents,key_values,key_numbers,static_index):
	f_sample = cmds.floatSliderGrp('DelstaticSample',q=True,value=True)
	for (i,key_outTangent) in enumerate(key_outTangents):
		#define cutKeyNumber
		cutKeyNumber = i + key_numbers[0]

		if i == 0:
			if key_values[i] == key_values[i+1]:
				static_index.append((cutKeyNumber,))
			else:
				continue
		elif i == len(key_outTangents)-1:
			if key_values[i] == key_values[i-1]:
				static_index.append((cutKeyNumber,))
			else:
				continue
		else:
			if abs(key_outTangents[i-1] - key_outTangent) < 0.01 and abs(key_outTangent - key_outTangents[i+1]) < 0.01:
				if key_outTangent == 0.0:
					if abs(key_values[i-1] - key_values[i]) < f_sample and abs(key_values[i] - key_values[i+1]) < f_sample:
						static_index.append((cutKeyNumber,))
					else:
						continue
				else:
					continue
			else:
				continue

	return static_index

def bake_channel(channelCheck,channelBox_attrs,appliedChannels):
	if channelCheck == 'FromChannelBox':
		bake_channels = channelBox_attrs
	elif channelCheck == 'FromAttributes':
		bake_channels = appliedChannels
	else:
		bake_channels = []
	return bake_channels

#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
##key Reduction
def ReductKeyFunction():
	cmds.commandEcho(ln=False)

	#define UI information
	channelCheck = getChannelCheck()
	channelBox_attrs = channelBoxList(channelCheck)
	appliedChannels = appliedChannelList(channelCheck)
	[start,end] = defineTimeRange()

	#create objLists
	objLists = cmds.ls(sl=True)

	if cmds.checkBox('LockSelectedKey',q=True,value=True) == True:
		#create L_KeyNameLists
		L_KeyNameLists = cmds.keyframe(q=True,n=True)
		[L_Name,L_keyTimes,L_keyValues,L_keyOutTangents,L_keyTangentTypes] = lockedKeyframe(L_KeyNameLists)
	else:
		L_Name = []
		L_keyTimes = []
		L_keyValues = []
		L_keyOutTangents = []
		L_keyTangentTypes = []

	#undo
	cmds.undoInfo(openChunk=True)

	for obj in objLists:
		#define channels
		[keyable_channels,channels] = common(obj,channelCheck,channelBox_attrs,appliedChannels,start,end)

		if len(channels) != 0:
			for channel in channels:
				#get key information
				key_times =  cmds.keyframe('{0}.{1}'.format(obj,channel),q=True,t=(start,end),timeChange=True)
				key_values = cmds.keyframe('{0}.{1}'.format(obj,channel),q=True,t=(start,end),valueChange=True)
				key_numbers = cmds.keyframe('{0}.{1}'.format(obj,channel),q=True,t=(start,end),iv=True)
				key_outTangents = cmds.keyTangent('{0}.{1}'.format(obj,channel),q=True,t=(start,end),outAngle=True)
				key_tangentTypes = cmds.keyTangent('{0}.{1}'.format(obj,channel),q=True,t=(start,end),ott=True)

				#fixed keyTangent
				fixed_index = fixedKey(key_tangentTypes,key_numbers)
				if len(fixed_index) !=0:
					cmds.keyTangent('{0}.{1}'.format(obj,channel),e=True,index=fixed_index,itt='fixed',ott='fixed')
				else:
					continue
					
				if len(key_outTangents) == 1:
					continue
				else:
					reduct_index = getReduct_index(key_outTangents,key_values,key_numbers,key_times)
					
				if len(reduct_index) != 0:
					cmds.cutKey(obj,at=channel,clear=True,index=reduct_index)
				else:
					continue
		else:
			continue

	if cmds.checkBox('LockSelectedKey',q=True,value=True) == True:
		if len(L_Name) != 0:
			for (i,L_name) in enumerate(L_Name):
				L_Times = L_keyTimes[i]
				L_values = L_keyValues[i]
				L_OutTangents = L_keyOutTangents[i]
				L_TangentTypes = L_keyTangentTypes[i]

				for (j,L_Time) in enumerate(L_Times):
					cmds.setKeyframe(L_name,t=(L_Time,L_Time),value=L_values[j])
					cmds.keyTangent(L_name,e=True,time=(L_Time,L_Time),ia=L_OutTangents[j],oa=L_OutTangents[j],itt=L_TangentTypes[j],ott=L_TangentTypes[j])

	cmds.undoInfo(closeChunk=True)
#------------------------------------------------------------------------------------------------------------------------------------
##Del Static
def DelStaticFunction():
	cmds.commandEcho(ln=False)

	#define UI information
	channelCheck = getChannelCheck()
	channelBox_attrs = channelBoxList(channelCheck)
	appliedChannels = appliedChannelList(channelCheck)
	[start,end] = defineTimeRange()

	#create objLists
	objLists = cmds.ls(sl=True)

	#undo
	cmds.undoInfo(openChunk=True)

	for obj in objLists:
		#define channels
		[keyable_channels,channels] = common(obj,channelCheck,channelBox_attrs,appliedChannels,start,end)

		if len(channels) != 0:
			for channel in channels:
				#get key information
				key_values = cmds.keyframe('{0}.{1}'.format(obj,channel),q=True,t=(start,end),valueChange=True)
				key_numbers = cmds.keyframe('{0}.{1}'.format(obj,channel),q=True,t=(start,end),iv=True)
				key_outTangents = cmds.keyTangent('{0}.{1}'.format(obj,channel),q=True,t=(start,end),outAngle=True)

				#define static_index list
				static_index = []
									
				if len(key_values) == 1:
					static_index.append((0,))
				else:
					static_index = getstatic_index(key_outTangents,key_values,key_numbers,static_index)
					
				if len(static_index) != 0:
					cmds.cutKey(obj,at=channel,clear=True,index=static_index)
				else:
					continue
		else:
			continue

	cmds.undoInfo(closeChunk=True)
#------------------------------------------------------------------------------------------------------------------------------------
##Bake Simulation
def BakeFunction():
	cmds.commandEcho(ln=False)

	#define UI information
	channelCheck = getChannelCheck()
	channelBox_attrs = channelBoxList(channelCheck)
	appliedChannels = appliedChannelList(channelCheck)
	[start,end] = defineTimeRange()
	b_sample = cmds.floatField('bakeSample',q=True,value=True)

	#create objLists
	objLists = cmds.ls(sl=True)

	#undo
	cmds.undoInfo(openChunk=True)

	bake_channels = bake_channel(channelCheck,channelBox_attrs,appliedChannels)

	if cmds.checkBox('Euler',q=True,value=True) == True:
		if cmds.checkBox('Sim',q=True,value=True) == True:
			cmds.bakeResults(objLists,at=bake_channels,simulation=True,t=(start,end),sb=b_sample,pok=True)
			cmds.setKeyframe(objLists,t=(-10000,-10000))
			cmds.setKeyframe(objLists,t=(-10001,-10001),value=0)
			cmds.filterCurve(objLists)
			cmds.cutKey(obj,at=bake_channels,t=(-10001,-10000))
		else:
			cmds.bakeResults(objLists,at=bake_channels,t=(start,end),sb=b_sample,pok=True)
			cmds.setKeyframe(objLists,t=(-10000,-10000))
			cmds.setKeyframe(objLists,t=(-10001,-10001),value=0)
			cmds.filterCurve(objLists)
			cmds.cutKey(objLists,at=bake_channels,t=(-10001,-10000))
	else:
		if cmds.checkBox('Sim',q=True,value=True) == True:
			cmds.bakeResults(objLists,at=bake_channels,simulation=True,t=(start,end),sb=b_sample,pok=True)
		else:
			cmds.bakeResults(objLists,at=bake_channels,t=(start,end),sb=b_sample,pok=True)
	if cmds.checkBox('POK',q=True,value=True) == False:
		cmds.cutKey(objLists,at=bake_channels,clear=True,t=(-100000,start-1))
		cmds.cutKey(objLists,at=bake_channels,clear=True,t=(end+1,100000))
	else:
		pass

	cmds.undoInfo(closeChunk=True)
#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
##UI attributes function
def getChannelCheck():
	if cmds.radioButton('AllKeyable',q=True,sl=True) == True:
		channelCheck = 'AllKeyable'
	elif cmds.radioButton('FromAttributes',q=True,sl=True) == True:
		channelCheck = 'FromAttributes'
	elif cmds.radioButton('FromChannelBox',q=True,sl=True) == True:
		channelCheck = 'FromChannelBox'
	return channelCheck

def appliedChannelList(channelCheck):
	#define List
	appliedChannels = []
	if channelCheck == 'FromAttributes':
		appliedChannels = checkBoxLists(appliedChannels)
		return appliedChannels
	else:
		return []

def channelBoxList(channelCheck):
	if channelCheck == 'FromChannelBox':
		channelBox_attrs = cmds.channelBox('mainChannelBox',q=True,sma=True)
		return channelBox_attrs
	else:
		return []

def checkBoxLists(appliedChannels):
	for t in ['x','y','z']:
		if cmds.checkBox('trans_'+t,q=True,value=True) == True:
			appliedChannels.append('t'+t)
		else:
			continue

	for r in ['x','y','z']:
		if cmds.checkBox('rot_'+r,q=True,value=True) == True:
			appliedChannels.append('r'+r)
		else:
			continue

	for s in ['x','y','z']:
		if cmds.checkBox('scl_'+s,q=True,value=True) == True:
			appliedChannels.append('s'+s)
		else:
			continue
	return appliedChannels

def defineTimeRange():
	if cmds.radioButton('TimeSlider',q=True,sl=True) == True:
		start = cmds.playbackOptions(q=True,minTime=True)
		end = cmds.playbackOptions(q=True,maxTime=True)
	elif cmds.radioButton('StartEnd',q=True,sl=True) == True:
		start = cmds.floatField('StartTime',q=True,value=True)
		end = cmds.floatField('EndTime',q=True,value=True)
	return [start,end]

#------------------------------------------------------------------------------------------------------------------------------------
##UI control
##checkBoxStatus
def checkBoxStatus(Status,Event):
	if "T" == Status:
		cmds.checkBox('trans_x',e=True,value=Event)
		cmds.checkBox('trans_y',e=True,value=Event)
		cmds.checkBox('trans_z',e=True,value=Event)
		
	elif "R" == Status:
		cmds.checkBox('rot_x',e=True,value=Event)
		cmds.checkBox('rot_y',e=True,value=Event)
		cmds.checkBox('rot_z',e=True,value=Event)
		
	elif "S" == Status:
		cmds.checkBox('scl_x',e=True,value=Event)
		cmds.checkBox('scl_y',e=True,value=Event)
		cmds.checkBox('scl_z',e=True,value=Event)

	elif "TAll" == Status:
		cmds.checkBox('trans_All',e=True,value=Event)
	
	elif "RAll" == Status:
		cmds.checkBox('rot_All',e=True,value=Event)
	
	elif "SAll" == Status:
		cmds.checkBox('scl_All',e=True,value=Event)

##radioButtonStatus
def radioButtonStatus(Status):
	if "AllKeyable" == Status:
		cmds.checkBox('trans_x',e=True,value=True,enable=False)
		cmds.checkBox('trans_y',e=True,value=True,enable=False)
		cmds.checkBox('trans_z',e=True,value=True,enable=False)
		cmds.checkBox('trans_All',e=True,value=True,enable=False)

		cmds.checkBox('rot_x',e=True,value=True,enable=False)
		cmds.checkBox('rot_y',e=True,value=True,enable=False)
		cmds.checkBox('rot_z',e=True,value=True,enable=False)
		cmds.checkBox('rot_All',e=True,value=True,enable=False)

		cmds.checkBox('scl_x',e=True,value=True,enable=False)
		cmds.checkBox('scl_y',e=True,value=True,enable=False)
		cmds.checkBox('scl_z',e=True,value=True,enable=False)
		cmds.checkBox('scl_All',e=True,value=True,enable=False)

	elif "FromAttributes" == Status:
		cmds.checkBox('trans_x',e=True,enable=True)
		cmds.checkBox('trans_y',e=True,enable=True)
		cmds.checkBox('trans_z',e=True,enable=True)
		cmds.checkBox('trans_All',e=True,enable=True)

		cmds.checkBox('rot_x',e=True,enable=True)
		cmds.checkBox('rot_y',e=True,enable=True)
		cmds.checkBox('rot_z',e=True,enable=True)
		cmds.checkBox('rot_All',e=True,enable=True)

		cmds.checkBox('scl_x',e=True,enable=True)
		cmds.checkBox('scl_y',e=True,enable=True)
		cmds.checkBox('scl_z',e=True,enable=True)
		cmds.checkBox('scl_All',e=True,enable=True)

	elif "FromChannelBox" == Status:
		cmds.checkBox('trans_x',e=True,enable=False)
		cmds.checkBox('trans_y',e=True,enable=False)
		cmds.checkBox('trans_z',e=True,enable=False)
		cmds.checkBox('trans_All',e=True,enable=False)

		cmds.checkBox('rot_x',e=True,enable=False)
		cmds.checkBox('rot_y',e=True,enable=False)
		cmds.checkBox('rot_z',e=True,enable=False)
		cmds.checkBox('rot_All',e=True,enable=False)

		cmds.checkBox('scl_x',e=True,enable=False)
		cmds.checkBox('scl_y',e=True,enable=False)
		cmds.checkBox('scl_z',e=True,enable=False)
		cmds.checkBox('scl_All',e=True,enable=False)

	elif "TimeSlider"  == Status:
		cmds.floatField('StartTime',e=True,enable=False)
		cmds.floatField('EndTime',e=True,enable=False)

	elif "StartEnd" == Status:
		cmds.floatField('StartTime',e=True,enable=True)
		cmds.floatField('EndTime',e=True,enable=True)

#------------------------------------------------------------------------------------------------------------------------------------
## mainGUI
class GUI(object):

	def __init__(self):
		self.windowName = 'KeyReducrionTool'
		self.checkUI()
		self.window = self.createWindow()
		self.createUI()

	##create window
	def createWindow(self):
		window = cmds.window(self.windowName,title='KeyReducrionTool Ver.1.1.0',widthHeight=(290,420))
		return window

	##create UI
	def createUI(self):
		cmds.setParent(self.window)
		cmds.columnLayout('columnLayout01',width=290,height=470,adjustableColumn=False)
		cmds.columnLayout(parent='columnLayout01',adjustableColumn=True)
		cmds.frameLayout(label='Channels',width=288,borderStyle='in')
		ChannelsRadioCollection = cmds.radioCollection()
		cmds.rowLayout(nc=4)
		cmds.text(label='',width=2,align='left')
		cmds.radioButton('AllKeyable',label=u'AllKeyable',sl=True,onc='radioButtonStatus("AllKeyable")')
		cmds.radioButton('FromAttributes',label=u'FromAttributes',onc='radioButtonStatus("FromAttributes")')
		cmds.radioButton('FromChannelBox',label=u'FromChannelBox',onc='radioButtonStatus("FromChannelBox")')
		cmds.setParent('..')
		cmds.setParent('..')


		cmds.frameLayout(label='Select Attributes',width=288,borderStyle='in',collapse=True,collapsable=True,parent='columnLayout01')
		cmds.rowLayout(nc=6)
		cmds.text(label='    Translate:',width=80,align='left')
		cmds.checkBox('trans_x',label=u'X',value=True,enable=False,ofc='checkBoxStatus("TAll",False)')
		cmds.checkBox('trans_y',label=u'Y',value=True,enable=False,ofc='checkBoxStatus("TAll",False)')
		cmds.checkBox('trans_z',label=u'Z',value=True,enable=False,ofc='checkBoxStatus("TAll",False)')
		cmds.checkBox('trans_All',label=u'All',value=True,enable=False,onc='checkBoxStatus("T",True)',ofc='checkBoxStatus("T",False)')
		cmds.setParent('..')

		cmds.columnLayout(adjustableColumn=True)
		cmds.separator(st='in')
		cmds.setParent('..')

		cmds.rowLayout(nc=5)
		cmds.text(label='    Rotate:',width=80,align='left')
		cmds.checkBox('rot_x',label=u'X',value=True,enable=False,ofc='checkBoxStatus("RAll",False)')
		cmds.checkBox('rot_y',label=u'Y',value=True,enable=False,ofc='checkBoxStatus("RAll",False)')
		cmds.checkBox('rot_z',label=u'Z',value=True,enable=False,ofc='checkBoxStatus("RAll",False)')
		cmds.checkBox('rot_All',label=u'All',value=True,enable=False,onc='checkBoxStatus("R",True)',ofc='checkBoxStatus("R",False)')
		cmds.setParent('..')

		cmds.columnLayout(adjustableColumn=True)
		cmds.separator(st='in')
		cmds.setParent('..')

		cmds.rowLayout(nc=5)
		cmds.text(label='    Scale:',width=80,align='left')
		cmds.checkBox('scl_x',label=u'X',value=True,enable=False,ofc='checkBoxStatus("SAll",False)')
		cmds.checkBox('scl_y',label=u'Y',value=True,enable=False,ofc='checkBoxStatus("SAll",False)')
		cmds.checkBox('scl_z',label=u'Z',value=True,enable=False,ofc='checkBoxStatus("SAll",False)')
		cmds.checkBox('scl_All',label=u'All',value=True,enable=False,onc='checkBoxStatus("S",True)',ofc='checkBoxStatus("S",False)')
		cmds.setParent('..')

		cmds.columnLayout(adjustableColumn=True)
		cmds.separator(st='in')
		cmds.setParent('..')
		
		cmds.columnLayout(parent='columnLayout01',width=288,adjustableColumn=True)
		cmds.frameLayout(label='Time Range',borderStyle='in')
		TimeRangeRadioCollection = cmds.radioCollection()
		cmds.rowLayout(nc=5)
		cmds.text(label='',width=2,align='left')
		cmds.radioButton('TimeSlider',label='TimeSlider',sl=True,onc='radioButtonStatus("TimeSlider")')
		cmds.radioButton('StartEnd',label='Start/End:',width=80,onc='radioButtonStatus("StartEnd")')
		cmds.floatField('StartTime',value=0,precision=3,step=1,enable=False)
		cmds.floatField('EndTime',value=10,precision=3,step=1,enable=False)
		cmds.setParent('..')

		cmds.columnLayout(parent='columnLayout01',width=288,adjustableColumn=True)
		cmds.frameLayout(label='Bake Simulation',borderStyle='in')

		cmds.rowLayout(nc=4)
		cmds.text(label='',width=5)
		cmds.checkBox('POK',label=u'Keep Unbaked',value=True)
		cmds.checkBox('Euler',label=u'Euler Filter',value=False)
		cmds.checkBox('Sim',label=u'Simulation',value=False)
		cmds.setParent('..')

		cmds.rowLayout(nc=4)
		cmds.text(label='    SampleBy:',width=70,align='left')
		cmds.floatField('bakeSample',value=1,precision=3,step=1,width=60)
		cmds.text(label='',width=45,align='left')
		cmds.button('Key Bake',width=100,label='Key Bake',c='BakeFunction()')
		cmds.setParent('..')

		cmds.columnLayout(parent='columnLayout01',width=288,adjustableColumn=True,cal='left')
		cmds.frameLayout(label='Delete static Key',borderStyle='in')
		cmds.rowLayout(nc=2)
		cmds.text(label='    Sample:',width=70,align='left')
		cmds.floatSliderGrp('DelstaticSample',field=True,min=0,max=0.1,precision=3,step=0.001,value=0.01,width=210,cw=(1,60),cal=(1,'left'))
		cmds.setParent('..')
		
		cmds.rowLayout(nc=2)
		cmds.text(label='',width=180,align='left')
		cmds.button('DelStaticKey',width=100,label='Del Static Key',c='DelStaticFunction()')
		cmds.setParent('..')

		cmds.columnLayout(parent='columnLayout01',width=288,adjustableColumn=True)
		cmds.frameLayout(label='Key Reduction (0= flat and linear only)',borderStyle='in')
		cmds.rowLayout(nc=2)
		cmds.text(label='',width=5)
		cmds.checkBox('LockSelectedKey',label=u'Lock Selected Key',value=False)
		cmds.setParent('..')

		cmds.rowLayout(nc=2)
		cmds.text(label='    Sample:',width=70,align='left')
		cmds.floatSliderGrp('ReductKeySample',field=True,min=0.00,max=1.00,precision=3,step=0.01,value=0.5,width=210,cw=(1,60),cal=(1,'left'))
		cmds.setParent('..')

		cmds.rowLayout(nc=2)
		cmds.text(label='',width=180,align='left')
		cmds.button('ReductKey',width=100,label='Key Reduction',c='ReductKeyFunction()')
		cmds.setParent('..')

	##check UI
	def checkUI(self):
		if cmds.window(self.windowName,exists=True):
			cmds.deleteUI(self.windowName)

	##show window
	def show(self):
		cmds.showWindow(self.window)

#------------------------------------------------------------------------------------------------------------------------------------

def keyReductionTool():
	w = GUI()
	w.show()

keyReductionTool()