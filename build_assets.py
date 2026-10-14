"""Original Kage Village model data. Rebuild with Python 3 + numpy.
Geometry is authored here, not copied from Roblox experiences or marketplaces.
"""
import json, math, random, wave, hashlib
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent
rng=random.Random(140026)
WOOD=[49,36,32]; DARK=[22,24,28]; PAPER=[176,155,117]; RED=[105,28,24]; STONE=[60,64,60]; MOSS=[37,49,38]
def cf(x=0,y=0,z=0,rx=0,ry=0,rz=0):
 a,b,c=rx,ry,rz
 X=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
 Y=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
 Z=np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
 m=np.eye(4);m[:3,:3]=X@Y@Z;m[:3,3]=[x,y,z];return m
class Model:
 def __init__(self,name):self.name=name;self.parts=[];self.lights=[];self.signs=[]
 def p(self,name,size,transform,color=WOOD,material='Wood',collide=True,shape='Block',alpha=0):
  data={'name':name,'size':size,'cf':list(transform[:3,3])+list(transform[:3,:3].flatten()),'color':color,'material':material,'collide':collide,'shape':shape}
  if alpha:data['alpha']=alpha
  data['cf']=[round(float(v),5) for v in data['cf']];self.parts.append(data);return len(self.parts)-1
 def sign(self,transform,text,width=5):
  n=self.p('Inscription',[width,2.7,.3],transform);self.signs.append({'part':n+1,'text':text})
 def lantern(self,x,z,y=7):
  self.p('Lantern post',[.6,y+1,.6],cf(x,(y+1)/2,z))
  n=self.p('Paper lantern',[1.7,2.3,1.7],cf(x,y,z),[255,169,94],'Neon',False)
  self.lights.append({'part':n+1,'position':[x,y,z],'color':[255,163,86],'range':24,'brightness':1.6})
  for h in [-1.2,1.2]:self.p('Lantern frame',[2.1,.25,2.1],cf(x,y+h,z),DARK)
  for dx,dz in [(-.9,-.9),(.9,-.9),(-.9,.9),(.9,.9)]:self.p('Lantern rib',[.12,2.3,.12],cf(x+dx,y,z+dz),DARK)
 def torii(self,x,z,scale=1):
  b=cf(x,0,z)
  for side in [-1,1]:
   self.p('Torii pillar',[1.3*scale,16*scale,1.3*scale],b@cf(side*7*scale,8*scale,0),RED)
   self.p('Torii foot',[2*scale,1.5*scale,2*scale],b@cf(side*7*scale,.75*scale,0),DARK,'Slate')
  for name,size,y,color in [('Cap',[20,1.1,2.6],16,DARK),('Crossbeam',[17,.8,1.1],12,RED),('Plaque',[2.2,3,.3],14,WOOD)]:self.p(name,[v*scale for v in size],b@cf(0,y*scale,0),color)
 def house(self,x,z,angle,index):
  b=cf(x,0,z,ry=angle)
  def p(n,s,t,c=WOOD,m='Wood',col=True,shape='Block'):return self.p(n,s,b@t,c,m,col,shape)
  p('Stone foundation',[29,1,23],cf(0,.1,0),STONE,'Slate')
  p('Rear wall',[27,11,.6],cf(0,6,10))
  for side in [-1,1]:
   p('Side wall',[.6,11,20],cf(side*13,6,0))
   p('Shoji paper',[9,10,.5],cf(side*9,5.8,-10),PAPER,'Plaster')
   for k in range(7):p('Shoji vertical',[.13,10,.65],cf(side*9-4+k*1.35,5.8,-10.3),DARK)
   for k in range(7):p('Shoji horizontal',[9,.13,.65],cf(side*9,1+k*1.5,-10.3),DARK)
   roof=cf(side*7.7,14,0,rz=side*math.radians(-23))
   p('Ceramic roof',[18,.65,27],roof,DARK,'Slate')
   for row in range(9):
    for column in range(10):
     color=[30+rng.randrange(10),32+rng.randrange(10),37+rng.randrange(10)]
     p('Kawara roof tile',[1.95,.22,2.62],roof@cf(-8+row*2,.48,-11.9+column*2.65),color,'Slate',False)
   for z1 in [-10,10]:p('Timber post',[.75,12,.75],cf(side*13,6,z1),DARK)
   for k in range(5):p('Wood siding',[.12,.18,20],cf(side*13.35,2+k*2,0),DARK)
  p('Roof ridge',[1.5,1.1,28],cf(0,17.5,0),DARK,'Slate')
  for k in range(12):p('Ridge tile',[1.8,1.2,2.1],cf(0,17.6,-12.5+k*2.25),STONE,'Slate',False)
  for i in range(3):
   for j in range(2):
    p('Tatami mat',[7.8,.15,8.2],cf(-8+i*8,.7,-4.2+j*8.4),[91,87,61],'Fabric')
    p('Tatami border',[.22,.18,8.2],cf(-11.8+i*8,.7,-4.2+j*8.4),[32,41,34],'Fabric')
  p('Low table',[5,.4,3],cf(0,1.6,2))
  for xx in [-2,2]:
   for zz in [1,3]:p('Table leg',[.3,1.1,.3],cf(xx,.9,zz))
  for xx in [-3.8,3.8]:p('Seat cushion',[2,.3,2],cf(xx,.95,2),[83,46,41],'Fabric',False)
  p('Tea bowl',[.6,.5,.6],cf(0,2.05,2),PAPER,'SmoothPlastic',False,'Ball')
  p('Hanging cloth',[3.2,2.3,.1],cf(0,9.5,-10.3),[50,61,64],'Fabric',False)
  self.sign(b@cf(8,9,-10.5),['霧','宿','茶','影','雨','灯'][index%6],3)
  for k in range(7):p('Engawa plank',[3.9,.25,3],cf(-12+k*4,.65,-12),[60,47,37])
  # Deterioration is geometry, no external texture IDs.
  for k in range(4):p('Weathered board',[.18,2,.15],cf(-11+k*7,7,-10.7,rz=rng.uniform(-.3,.3)),[59,46,33],'Wood',False)
 def tree(self,x,z,scale):
  self.p('Cedar trunk',[1.8*scale,23*scale,1.8*scale],cf(x,11.5*scale,z),WOOD,'Wood',True,'CylinderY')
  for level in range(4):
   radius=(7-level)*scale
   for j in range(5):
    a=j*math.tau/5+level*.7
    self.p('Cedar needles',[radius,4*scale,3*scale],cf(x+math.cos(a)*radius*.35,(13+level*4)*scale,z+math.sin(a)*radius*.35,ry=-a,rz=.35),MOSS,'Grass',False,'Wedge')
world=Model('Kage Village — original environment')
world.p('Village earth',[760,3,800],cf(0,-1.5,0),MOSS,'Ground')
world.p('Main street',[22,.12,740],cf(0,.02,0),STONE,'Cobblestone')
for z in [-240,-120,0,120,240]:world.p('Cross street',[590,.12,15],cf(0,.04,z),STONE,'Cobblestone')
for x in [-240,-120,120,240]:world.p('Side street',[12,.12,550],cf(x,.04,0),STONE,'Cobblestone')
for i,(z,x) in enumerate((z,x) for z in [-185,-65,65,185] for x in [-180,-60,60,180]):world.house(x,z,math.pi/2 if x<0 else -math.pi/2,i)
world.house(0,350,0,17);world.sign(cf(0,12,338),'帰らずの社',12)
world.torii(0,-310,1.2)
for z in range(270,321,15):world.torii(0,z,.85)
for z in range(-300,301,60):world.lantern(-15,z);world.lantern(15,z+20)
for z in [-240,0,240]:
 for x in [-230,-110,110,230]:world.lantern(x,z-12)
for i in range(125):
 x,z=rng.uniform(-355,355),rng.uniform(-375,375)
 if abs(x)>275 or abs(z)>280:world.tree(x,z,rng.uniform(.8,1.5))
for x in range(160,241,16):
 for z in range(280,341,18):
  world.p('Grave base',[5,.7,5],cf(x,.35,z),STONE,'Slate')
  world.p('Gravestone',[2.6,6,1.8],cf(x,3,z,rz=rng.uniform(-.07,.07)),STONE,'Slate')
  world.sign(cf(x,4,z-1),'無名',1.6)
for i in range(12):
 a=i*math.pi/6;world.p('Well stones',[2,3,2],cf(-220+math.cos(a)*4,1.5,40+math.sin(a)*4),STONE,'Slate')
world.p('Well darkness',[6,.1,6],cf(-220,.05,40),[7,11,13],'Glass',False)
for x in [-270,270]:
 for z in range(-340,321,20):
  world.p('Fence post',[.8,4,.8],cf(x,2,z));world.p('Fence rail',[.4,.5,20],cf(x,2.8,z+10))
for i in range(24):
 a=i*math.pi/12;world.p('Mountain',[150,rng.uniform(130,240),150],cf(math.cos(a)*470,35,math.sin(a)*500),[22,31,34],'Rock',True,'Ball')
for x in [-369,369]:world.p('Boundary',[6,35,790],cf(x,15,0),DARK,'Rock')
for z in [-389,389]:world.p('Boundary',[740,35,6],cf(0,15,z),DARK,'Rock')
# Actual bell visible at the interaction point.
for x in [-4,4]:world.p('Bell frame',[.8,10,.8],cf(x,5,318),RED)
world.p('Bell beam',[10,1,1.2],cf(0,10,318),WOOD)
world.p('Temple bell',[3,4,3],cf(0,7.5,318),[88,91,65],'Metal',True,'CylinderY')
world.p('Bell striker',[.6,.6,5],cf(0,6,315),WOOD)
monsters=[]
for variant in range(3):
 m=Model(['The Veiled Widow','The Hollow Monk','The Red Keeper'][variant]);robe=[[173,168,153],[17,18,22],[71,22,26]][variant]
 m.p('Body',[2.6,5,1.3],cf(0,4.1,0),robe,'Fabric',False)
 m.p('Mask',[1.5,2,.72],cf(0,7.3,-.25),[210,203,181],'SmoothPlastic',False,'Ball')
 m.p('Hair',[1.9,3.8,1.2],cf(0,6.4,.3),[9,10,13],'Fabric',False,'Ball')
 for i in range(14):
  a=i*math.tau/14
  m.p('Robe fold',[.5,4.5,.28],cf(math.cos(a)*1.25,2.8,math.sin(a)*.8,rz=math.cos(a)*.09),[max(0,v+rng.randint(-12,12)) for v in robe],'Fabric',False)
 for side in [-1,1]:
  m.p('Eye socket',[.43,.22,.18],cf(side*.37,7.55,-.67),[9,8,10],'SmoothPlastic',False,'Ball')
  m.p('Eye glint',[.07,.07,.05],cf(side*.37,7.57,-.77),[220,163,113],'Neon',False,'Ball')
  for i in range(3):m.p('Mask crack',[.045,.35,.04],cf(side*(.35+i*.03),7.2-i*.3,-.65,rz=side*.15),[71,52,49],'SmoothPlastic',False)
  m.p('Arm'+str(side),[.55,4.5,.55],cf(side*1.6,4.3,-.1,rz=side*.12),robe,'Fabric',False)
  m.p('Hand'+str(side),[.58,.9,.3],cf(side*1.85,1.75,-.1),[160,152,128],'SmoothPlastic',False)
  for finger in range(4):
   m.p('Finger',[.1,1.1,.12],cf(side*1.85+(finger-1.5)*.14,.95,-.12,rx=-.12),[160,152,128],'SmoothPlastic',False)
   m.p('Nail',[.09,.4,.09],cf(side*1.85+(finger-1.5)*.14,.3,-.23),DARK,'SmoothPlastic',False)
 if variant==0:
  for i in range(11):m.p('Veil strand',[.14,5,.12],cf(-.9+i*.18,5.6,-.66),[204,197,176],'Fabric',False,alpha=.35)
 elif variant==1:
  for i in range(15):
   a=i*math.tau/15;m.p('Prayer bead',[.22,.22,.22],cf(math.cos(a)*1.2,5.5+math.sin(a)*.5,-.8),[89,53,34],'Wood',False,'Ball')
 else:
  for side in [-1,1]:
   for j in range(4):m.p('Horn',[.38-j*.065,.65,.35-j*.06],cf(side*(.55+j*.15),8.25+j*.5,0,rz=-side*.25),[180,168,136],'SmoothPlastic',False)
 m.p('Mouth',[.4,.55,.1],cf(0,6.7,-.65),[20,12,14],'SmoothPlastic',False)
 monsters.append({'name':m.name,'parts':m.parts})
assets=BASE/'assets';assets.mkdir(exist_ok=True)
def save(name,data):
 p=assets/name;p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8');return p
save('village.json',{'schema':1,'name':world.name,'parts':world.parts,'lights':world.lights,'signs':world.signs})
save('monsters.json',{'schema':1,'models':monsters})
# Original synthesized ambience, no external audio licensing or private asset IDs.
sr=16000
np_rng=np.random.default_rng(140026)
for name,duration in [('Wind',8),('Drone',8),('Step',.28),('Bell',3),('Whisper',2.5),('Stinger',1.4)]:
 t=np.arange(int(sr*duration))/sr;noise=np_rng.normal(0,1,len(t));smooth=np.convolve(noise,np.ones(160)/160,'same')
 if name=='Wind':v=smooth*(.5+.2*np.sin(t*math.tau*.25))
 elif name=='Drone':v=.10*np.sin(t*math.tau*53)+.07*np.sin(t*math.tau*56)+.04*np.sin(t*math.tau*107)
 elif name=='Step':v=noise*.17*np.exp(-t*26)+.18*np.sin(t*math.tau*85)*np.exp(-t*30)
 elif name=='Bell':v=sum(.16/(i+1)*np.sin(t*math.tau*f)*np.exp(-t*(.7+i*.3)) for i,f in enumerate([220,561,1017,1593]))
 elif name=='Whisper':v=smooth*np.sin(t*math.tau*720)*(.25+.2*np.sin(t*math.tau*3))
 else:v=(.12*np.sin(math.tau*(180*t+180*t*t))+.08*noise)*np.sin(np.minimum(t/duration,1)*math.pi)
 fade=np.minimum(t/.05,1)*np.minimum((duration-t)/.12,1);v=np.clip(v*fade,-.7,.7)
 p=assets/'audio'/f'{name}.wav';p.parent.mkdir(exist_ok=True)
 with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((v*32767).astype('<i2').tobytes())
manifest={'schema':1,'title':'Kage Village','version':'1.0.0','files':{}}
for p in sorted(assets.rglob('*')):
 if p.is_file() and p.name!='manifest.json':manifest['files'][p.relative_to(BASE).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(BASE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('World parts:',len(world.parts),'monster parts:',[len(m['parts']) for m in monsters])
