"""Original triangulated Japanese village and spirits. No external model assets.

Mesh libraries are instanced by the client; simple invisible colliders keep movement
independent of visual tessellation. Run after build_assets.py to preserve audio.
"""
from pathlib import Path
import math, random, json, hashlib
import numpy as np

BASE = Path(__file__).resolve().parent
R = random.Random(140026)
PI = math.pi
WOOD=(105,65,42); TRIM=(48,35,32); PLASTER=(186,170,137)
TILE=(65,85,94); STONE=(112,124,119); RED=(147,46,34)

def cf(x=0,y=0,z=0,ry=0):
    c,s=math.cos(ry),math.sin(ry)
    return [x,y,z,c,0,s,0,1,0,-s,0,c]

def tint(color,f): return [min(255,max(0,round(v*f))) for v in color]

class Mesh:
    def __init__(self): self.vertices=[]; self.faces=[]; self.colors=[]
    def vert(self,v):
        self.vertices.append([round(float(x),4) for x in v]); return len(self.vertices)
    def tri(self,a,b,c,color):
        self.faces.append([a,b,c]); self.colors.append(list(color))
    def quad(self,a,b,c,d,color):
        self.tri(a,b,c,color); self.tri(a,c,d,color)
    def box(self,center,size,color,ry=0):
        x,y,z=center; w,h,d=[v/2 for v in size]; co,si=math.cos(ry),math.sin(ry)
        ids=[self.vert((x+co*dx+si*dz,y+dy,z-si*dx+co*dz)) for dx,dy,dz in
             [(-w,-h,-d),(w,-h,-d),(w,h,-d),(-w,h,-d),(-w,-h,d),(w,-h,d),(w,h,d),(-w,h,d)]]
        for face,shade in [((0,3,2,1),.94),((4,5,6,7),.88),((0,4,7,3),.9),((1,2,6,5),1),((3,7,6,2),1.08),((0,1,5,4),.75)]:
            self.quad(*[ids[i] for i in face],tint(color,shade))
    def loft(self,rings,color,n=16,phase=0,pleat=0):
        # Rings: x,y,z, radiusX,radiusZ. Consistent winding and capped ends.
        ids=[]
        for row,(x,y,z,rx,rz) in enumerate(rings):
            ids.append([self.vert((x+math.cos(a)*rx*(1+pleat*math.cos(a*8)),y,z+math.sin(a)*rz*(1+pleat*math.cos(a*8)))) for a in [phase+i*math.tau/n for i in range(n)]])
        for j in range(len(ids)-1):
            for i in range(n):
                k=(i+1)%n
                self.quad(ids[j][i],ids[j+1][i],ids[j+1][k],ids[j][k],tint(color,1+.07*math.cos(i*1.7)))
        for row,reverse in [(0,True),(-1,False)]:
            c=self.vert(rings[row][:3])
            for i in range(n):
                a,b=ids[row][i],ids[row][(i+1)%n]
                self.tri(c,a,b,color) if reverse else self.tri(c,b,a,color)
    def ellipsoid(self,center,size,color,n=12,rows=7):
        x,y,z=center; rx,ry,rz=[v/2 for v in size]
        self.loft([(x,y-ry*math.cos(t),z,max(.001,rx*math.sin(t)),max(.001,rz*math.sin(t))) for t in np.linspace(0,PI,rows)],color,n)
    def beam(self,a,b,r,color,n=7,r2=None):
        a,b=np.array(a,dtype=float),np.array(b,dtype=float); axis=b-a; axis/=np.linalg.norm(axis)
        ref=np.array([0,1,0]) if abs(axis[1])<.95 else np.array([1,0,0])
        u=np.cross(axis,ref);u/=np.linalg.norm(u);v=np.cross(axis,u)
        ids=[]
        for p,radius in [(a,r),(b,r if r2 is None else r2)]:
            ids.append([self.vert(p+radius*(math.cos(t)*u+math.sin(t)*v)) for t in np.linspace(0,math.tau,n,endpoint=False)])
        for i in range(n):
            k=(i+1)%n;self.quad(ids[0][i],ids[1][i],ids[1][k],ids[0][k],color)
        for j in [0,1]:
            center=self.vert(a if j==0 else b)
            for i in range(n):
                k=(i+1)%n
                self.tri(center,ids[j][i],ids[j][k],color) if j==0 else self.tri(center,ids[j][k],ids[j][i],color)
    def data(self): return {'vertices':self.vertices,'faces':self.faces,'colors':self.colors}

class Scene:
    def __init__(self,name):self.name=name;self.parts=[];self.lights=[];self.signs=[];self.meshes={};self.instances=[]
    def part(self,name,size,transform,color=STONE,material='Slate',collide=True,alpha=0,shape='Block'):
        self.parts.append(dict(name=name,size=size,cf=transform,color=color,material=material,collide=collide,alpha=alpha,shape=shape));return len(self.parts)
    def collider(self,name,size,transform):return self.part(name,size,transform,collide=True,alpha=1)
    def register(self,key,mesh,material='SmoothPlastic'):
        self.meshes[key]=dict(**mesh.data(),material=material)
    def inst(self,key,transform):self.instances.append(dict(mesh=key,cf=transform))
    def data(self):return dict(schema=2,name=self.name,parts=self.parts,lights=self.lights,signs=self.signs,meshes=self.meshes,instances=self.instances)

world=Scene('Kage Village — Moonlit Cedar / mesh edition')

def roof(mesh,w,d,base,rise,color):
    # Sweeping eaves and individually curved barrel tiles. Ridge runs along X.
    for side in [-1,1]:
        cols=max(8,round(w/1.1)); rows=7
        for j in range(rows):
            t0=j/rows;t1=min(1,(j+1)/rows+.015)
            for i in range(cols):
                x=-w/2+(i+.5)*w/cols
                ids=[]
                for t in [t0,t1]:
                    z=side*t*d/2
                    y=base+rise*(1-t)**1.45+.72*t**9
                    ids.append([mesh.vert((x+(k/4-.5)*(w/cols+.045),y+.10+.16*math.sin(k*PI/4),z)) for k in range(5)])
                col=tint(color,R.uniform(.88,1.14))
                for k in range(4):
                    a,b,c,e=ids[0][k],ids[1][k],ids[1][k+1],ids[0][k+1]
                    if side>0:mesh.quad(a,b,c,e,col)
                    else:mesh.quad(e,c,b,a,col)
        # Heavy curved fascia follows roof profile along gables.
        for x in [-w/2,w/2]:
            for j in range(10):
                t0=j/10;t1=(j+1)/10
                a=(x,base+rise*(1-t0)**1.45+.72*t0**9,side*t0*d/2)
                b=(x,base+rise*(1-t1)**1.45+.72*t1**9,side*t1*d/2)
                mesh.beam(a,b,.19,TRIM,6)
        mesh.beam((-w/2,base+.68,side*d/2),(w/2,base+.68,side*d/2),.24,TRIM,8)
    mesh.beam((-w/2-.3,base+rise+.1,0),(w/2+.3,base+rise+.1,0),.42,tint(color,1.25),10)
    for x in [-w/2,w/2]:
        mesh.ellipsoid((x,base+rise+.45,0),(.8,1.15,.8),tint(color,1.2),8,5)

def make_house(variant):
    wood=Mesh(); plaster=Mesh(); tiles=Mesh(); stone=Mesh(); decor=Mesh(); glass=Mesh()
    height=[11,14,10,12][variant]; wall=[PLASTER,(161,155,134),(177,158,127),(133,149,145)][variant]
    stone.box((0,-.25,0),(29,.8,23),STONE)
    for side in [-1,1]:
        plaster.box((side*13,height/2,0),(.5,height,20),wall)
        # Timber framing, inset lower panels and narrow rain battens.
        for z in [-10,-5,0,5,10]:wood.box((side*13.35,height/2,z),(.55,height,.55),TRIM)
        for y in [.8,3.2,height-.2]:wood.box((side*13.4,y,0),(.55,.35,20.8),WOOD)
        for k in range(19):wood.box((side*13.38,1.8,-9+k),(.16,2.5,.85),tint(WOOD,R.uniform(.75,1.2)))
        plaster.box((side*8.8,height/2,-10),(8.5,height,.5),wall)
        for x in [side*4.6,side*13]:wood.box((x,height/2,-10.4),(.55,height,.7),TRIM)
        # Glowing inset shoji with a deep frame, lattice and shutter rails.
        glass.box((side*8.7,6,-10.36),(6.8,5,.10),(207,164,94))
        for k in range(8):wood.box((side*8.7-3.4+k*.97,6,-10.55),(.09,5.2,.16),TRIM)
        for y in [3.4,4.7,6,7.3,8.6]:wood.box((side*8.7,y,-10.55),(7,.10,.18),TRIM)
    plaster.box((0,height/2,10),(26,height,.5),wall)
    for x in [-13,-6.5,0,6.5,13]:wood.box((x,height/2,10.3),(.5,height,.55),TRIM)
    for z in [-10.4,10.4]:wood.box((0,height-.3,z),(27.5,.5,.6),TRIM)
    # Floor and veranda are below the virtual movement collider.
    for i in range(22):wood.box((-13+i*1.24,.35,0),(1.19,.2,24.5),tint(WOOD,R.uniform(.8,1.1)))
    for i in range(3):stone.box((0,-.03+i*.12,-14+i*.75),(9,.22,1.2),tint(STONE,1-i*.08))
    for x in [-12,12]:
        wood.box((x,height/2,-13),(.45,height,.45),WOOD)
        for z in [-13,-11]:wood.box((x,1.8,z),(.16,2,.16),TRIM)
    roof(tiles,31,28,height+.1,5.4,TILE if variant!=2 else (91,100,82))
    # Secondary shop canopy and ornamental gable, distinct silhouette per type.
    if variant in (1,2):
        roof(tiles,28,7,8.4,1.4,TILE)
        # Cloth panels hang above, leaving doorway clear.
        for x in [-3,-1,1,3]:decor.box((x,8.4,-12.2),(1.8,2.8,.10),[(47,87,107),(111,51,45)][variant==2])
    if variant==1:
        for x in [-7,7]:
            glass.box((x,11,-10.4),(6,2.2,.1),(194,143,75))
            for k in range(7):wood.box((x-3+k,11,-10.6),(.13,2.4,.2),TRIM)
    for x in [-9,9]:
        decor.loft([(x,.4,-14.8,1.05,1.05),(x,.7,-14.8,1.2,1.2),(x,2.6,-14.8,.9,.9),(x,2.9,-14.8,.6,.6)],(105,73,55),12)
        decor.ellipsoid((x,3.1,-14.8),(2,.6,2),(72,101,71),10,4)
    # Readable, furnished interiors.
    for x in [-7.5,0,7.5]:
        for z in [-3.5,4.5]:
            decor.box((x,.6,z),(7.1,.14,7.5),(133,135,87))
            decor.box((x-3.4,.7,z),(.2,.08,7.5),(56,77,62))
    wood.box((0,1.7,3),(5,.3,3),tint(WOOD,.75))
    for x in [-2,2]:
        for z in [2,4]:wood.box((x,1, z),(.25,1.2,.25),TRIM)
    for x in [-4,4]:decor.ellipsoid((x,.95,3),(2.6,.45,2.5),(116,57,49),8,4)
    decor.ellipsoid((0,2.1,3),(.9,.55,.9),(192,183,151),10,5)
    for name,m,mat in [('wood',wood,'Wood'),('walls',plaster,'Plaster'),('roof',tiles,'Slate'),('base',stone,'Slate'),('detail',decor,'SmoothPlastic'),('windows',glass,'Neon')]:
        world.register(f'house{variant}_{name}',m,mat)

for variant in range(4):make_house(variant)

def place_house(x,z,angle,variant):
    for name in ['wood','walls','roof','base','detail','windows']:world.inst(f'house{variant}_{name}',cf(x,0,z,angle))
    c,s=math.cos(angle),math.sin(angle)
    def at(px,y,pz):return cf(x+c*px+s*pz,y,z-s*px+c*pz,angle)
    for px in [-13,13]:world.collider('House side',[.7,11,20],at(px,5.5,0))
    world.collider('House rear',[26,11,.7],at(0,5.5,10))
    for px in [-8.8,8.8]:world.collider('House front',[8.5,11,.7],at(px,5.5,-10))
    p=world.part('Warm window light',[.1,.1,.1],at(0,7,-7),alpha=1,collide=False)
    world.lights.append(dict(part=p,position=at(0,7,-7)[:3],color=[255,190,112],range=23,brightness=1.0))
    p=world.part('Shop sign',[3,3,.25],at(4.7,8.3,-11.1),WOOD,'Wood',False)
    world.signs.append(dict(part=p,text=['灯','宿','茶','雨'][variant]))

world.part('Village earth',[760,3,800],cf(0,-1.5,0),(66,81,70),'Ground')
world.part('Main street',[22,.12,740],cf(0,.02,0),(109,116,112),'Cobblestone')
for z in [-240,-120,0,120,240]:world.part('Cross street',[590,.12,15],cf(0,.04,z),(101,110,106),'Cobblestone')
for x in [-240,-120,120,240]:world.part('Side street',[12,.12,550],cf(x,.04,0),(98,108,105),'Cobblestone')
for i,(z,x) in enumerate((z,x) for z in [-185,-65,65,185] for x in [-180,-60,60,180]):
    place_house(x,z,PI/2 if x<0 else -PI/2,i%4)

# Shrine is a unique triple-roof pavilion with a broad ceremonial gable.
shrine=Mesh(); sr=Mesh(); sw=Mesh()
for x in [-15,-8,8,15]:
    shrine.loft([(x,0,0,.8,.8),(x,1,0,.65,.65),(x,12,0,.5,.5)],RED,12)
    shrine.box((x,11,0),(3,.8,3),WOOD)
for z in [-9,9]:
    for x in [-15,15]:shrine.box((x,6,z),(1,12,1),RED)
    shrine.box((0,11,z),(33,1,1.4),WOOD)
roof(sr,39,31,12,7,(62,88,95));roof(sr,25,20,18,5,(69,94,100))
sw.box((0,5,9),(30,10,.8),(176,157,121))
for x in [-15,15]:sw.box((x,5,0),(.8,10,18),(176,157,121))
for x in [-8,8]:
    shrine.box((x,4,-9),(8,8,.5),WOOD)
    for k in range(9):shrine.box((x-4+k,4,-9.4),(.12,8,.15),tint(TRIM,1.3))
for j in range(5):shrine.box((0,.1*j,-13-j*1.1),(24,.25,1.2),STONE)
for name,m,mat in [('Shrine structure',shrine,'Wood'),('Shrine roofs',sr,'Slate'),('Shrine plaster',sw,'Plaster')]:world.register(name,m,mat);world.inst(name,cf(0,0,350))
world.collider('Shrine rear',[30,10,.8],cf(0,5,359))
for x in [-15,15]:world.collider('Shrine side',[.8,10,18],cf(x,5,350))

# Carved stone lanterns, curved torii, mossy rocks, detailed cedar silhouettes.
lantern=Mesh(); glow=Mesh()
lantern.loft([(0,0,0,1.7,1.7),(0,.45,0,1.7,1.7),(0,.9,0,1.1,1.1),(0,1.2,0,.5,.5),(0,5.4,0,.45,.45),(0,5.9,0,1.25,1.25)],STONE,8)
lantern.box((0,6.1,0),(2.6,.35,2.6),tint(STONE,1.15))
for x in [-.9,.9]:
    for z in [-.9,.9]:lantern.box((x,7,z),(.22,1.8,.22),STONE)
lantern.loft([(0,7.8,0,1.1,1.1),(0,8,0,1.8,1.8),(0,8.5,0,1.3,1.3),(0,9,0,.4,.4),(0,9.45,0,.1,.1)],tint(STONE,.8),8)
glow.box((0,7,0),(1.5,1.5,1.5),(255,194,109))
world.register('Stone lantern',lantern,'Slate');world.register('Lantern light',glow,'Neon')
def place_lantern(x,z):
    world.inst('Stone lantern',cf(x,0,z));world.inst('Lantern light',cf(x,0,z))
    p=world.part('Lantern emitter',[.1,.1,.1],cf(x,7,z),alpha=1,collide=False)
    world.lights.append(dict(part=p,position=[x,7,z],color=[255,196,127],range=32,brightness=1.8))
for z in range(-300,301,40):place_lantern(-15,z);place_lantern(15,z+18)
for z in [-240,-120,0,120,240]:
    for x in [-230,-110,110,230]:place_lantern(x,z-12)

torii=Mesh()
for x in [-7,7]:
    torii.loft([(x,0,0,1,1),(x,1,0,1,1),(x,1.1,0,.7,.7),(x,15,0,.6,.6)],RED,12)
    torii.loft([(x,0,0,1.1,1.1),(x,1.3,0,1,1)],TRIM,12)
torii.box((0,11.7,0),(18,.85,1.1),RED)
torii.box((0,13,0),(.8,4,.8),RED)
for j in range(20):
    x=-10+j; y=15.6+.9*(abs(x)/10)**4
    torii.box((x+.5,y,0),(1.06,.6,2.5),TRIM)
    torii.box((x+.5,y-.65,0),(1.06,.6,1.8),RED)
world.register('Curved torii',torii,'Wood')
world.inst('Curved torii',cf(0,0,-310))
for z in [270,290,310]:world.inst('Curved torii',cf(0,0,z))

for variant in range(4):
    tree=Mesh();leaves=Mesh(); height=25+variant*4
    tree.beam((0,0,0),(.5,height,0),.75,WOOD,9,.2)
    for level in range(6):
        y=8+level*(height-8)/6;radius=8*(1-level/7)
        for j in range(5):
            a=j*math.tau/5+level*.7
            tip=(math.cos(a)*radius,y+.6,math.sin(a)*radius)
            tree.beam((0,y-1,0),tip,.22,WOOD,5,.06)
            leaves.loft([(tip[0]*.5,y-1,tip[2]*.5,radius*.65,radius*.65),(tip[0]*.45,y+.5,tip[2]*.45,radius*.58,radius*.58),(tip[0]*.3,y+5,tip[2]*.3,.04,.04)],tint((62,100,84),R.uniform(.8,1.2)),7,phase=a)
    world.register('Cedar trunk'+str(variant),tree,'Wood');world.register('Cedar crown'+str(variant),leaves,'Grass')
for i in range(100):
    a=R.uniform(0,math.tau);x=math.cos(a)*R.uniform(285,350);z=math.sin(a)*R.uniform(335,380)
    if abs(x)<30 and z<0:continue
    for name in ['Cedar trunk','Cedar crown']:world.inst(name+str(i%4),cf(x,0,z,R.uniform(0,math.tau)))

for variant in range(5):
    rock=Mesh();size=R.uniform(3,7)
    rock.loft([(0,-.5,0,size*.7,size*.5),(.2,1,0,size*.65,size*.55),(-.4,size*.6,.2,size*.45,size*.4),(0,size*.8,0,.1,.1)],tint(STONE,R.uniform(.7,1)),7,phase=variant)
    world.register('Moss rock'+str(variant),rock,'Rock')
for i in range(85):
    x=R.choice([-1,1])*R.uniform(275,355);z=R.uniform(-365,365)
    world.inst('Moss rock'+str(i%5),cf(x,0,z,R.random()*math.tau))

# Curving bundles of meadow grass and ferns, placed away from road corridors.
grass=Mesh()
for i in range(18):
    a=R.random()*math.tau;r=R.random()*1.7;h=R.uniform(.5,1.6)
    p=np.array([math.cos(a)*r,0,math.sin(a)*r]); side=np.array([math.sin(a)*.11,0,-math.cos(a)*.11])
    ids=[grass.vert(p-side),grass.vert(p+side),grass.vert(p+np.array([math.cos(a)*.5,h,math.sin(a)*.5]))]
    grass.tri(*ids,tint((105,127,80),R.uniform(.8,1.1)))
world.register('Meadow grass',grass,'Grass')
for i in range(420):
    x,z=R.uniform(-265,265),R.uniform(-270,270)
    if min(abs(x-a) for a in [-240,-120,0,120,240])<15 or min(abs(z-a) for a in [-240,-120,0,120,240])<12:continue
    world.inst('Meadow grass',cf(x,.1,z,R.random()*math.tau))

# Paving edges, irregular stepping stones, drainage channels and garden walls.
road=Mesh()
for z in range(-360,361,6):
    for x in [-12.5,12.5]:road.box((x,.1,z),(1.2,.4,5.7),tint(STONE,R.uniform(.75,1.15)))
    for x in [-7,-2,3,8]:road.box((x+R.uniform(-.25,.25),.09,z+R.uniform(-.2,.2)),(4.6,.08,5.5),tint(STONE,R.uniform(.85,1.2)),R.uniform(-.02,.02))
world.register('Main street paving',road,'Slate');world.inst('Main street paving',cf())
wall=Mesh()
for z in range(-320,321,6):
    for x in [-269,269]:
        wall.box((x,1.1,z),(1.8,2.2,5.8),tint(STONE,R.uniform(.75,1.1)))
        wall.box((x,2.3,z),(2.2,.3,5.9),tint(TILE,.9))
world.register('Garden boundary',wall,'Slate');world.inst('Garden boundary',cf())

grave=Mesh()
grave.box((0,.35,0),(3.4,.7,3.2),STONE);grave.box((0,.9,0),(2.7,.45,2.5),STONE)
grave.loft([(0,1.1,0,1,.7),(0,4.8,0,.85,.65),(0,5.3,0,.55,.5)],STONE,4,PI/4)
for y in [2,2.6,3.2,3.8]:grave.box((0,y,-.67),(.16,.32,.035),TRIM)
world.register('Carved gravestone',grave,'Slate')
for x in range(160,241,16):
    for z in range(280,341,18):world.inst('Carved gravestone',cf(x,0,z,R.uniform(-.08,.08)))
well=Mesh()
for level in range(3):
    for i in range(14):
        a=(i+level*.5)*math.tau/14
        well.box((math.cos(a)*4,.5+level*.9,math.sin(a)*4),(1.9,.85,1.1),tint(STONE,R.uniform(.85,1.15)),-a)
for x in [-5,5]:well.box((x,5,0),(.6,10,.6),WOOD)
well.box((0,9,0),(12,.8,.8),WOOD);roof(well,13,9,9,2.4,TILE)
world.register('Roofed stone well',well,'Slate');world.inst('Roofed stone well',cf(-220,0,40))
world.part('Well water',[6,.06,6],cf(-220,.15,40),(28,66,68),'Glass',False)
bell=Mesh()
for x in [-4,4]:bell.box((x,5,0),(.9,10,.9),RED)
bell.box((0,10,0),(10,1,1.4),WOOD)
bell.loft([(0,5.3,0,1.8,1.8),(0,5.6,0,1.85,1.85),(0,6,0,1.5,1.5),(0,8.7,0,1.3,1.3),(0,9,0,.7,.7)],(123,133,100),20)
for y in [6,7.8]:
    for i in range(20):
        a=i*math.tau/20;bell.ellipsoid((math.cos(a)*1.45,y,math.sin(a)*1.45),(.18,.18,.18),(161,153,103),6,3)
bell.beam((0,6,-5),(0,6,-1),.3,WOOD,10)
world.register('Bronze temple bell',bell,'Metal');world.inst('Bronze temple bell',cf(0,0,318))
for x in [-369,369]:world.collider('Boundary',[6,35,790],cf(x,15,0))
for z in [-389,389]:world.collider('Boundary',[740,35,6],cf(0,15,z))
mountain=Mesh()
for i in range(32):
    a=i*math.tau/32;x,z=math.cos(a)*470,math.sin(a)*500;h=R.uniform(65,130)
    mountain.loft([(x,-5,z,100,90),(x+15,h*.4,z,70,65),(x-10,h,z+15,.1,.1)],(58,83,87),7)
world.register('Distant mountain ridges',mountain,'Rock');world.inst('Distant mountain ridges',cf())

monsters=[]
for variant in range(3):
    scene=Scene(['The Veiled Widow','The Hollow Monk','The Red Keeper'][variant])
    cloth=Mesh();skin=Mesh();dark=Mesh();accent=Mesh()
    robes=[(190,189,164),(58,69,73),(130,47,38)];robe=robes[variant]
    # Continuous tailored silhouette with irregular pleated hem and narrow waist.
    cloth.loft([(0,.2,0,1.75,1.1),(.1,.7,0,1.8,1.1),(-.1,2,0,1.45,.85),(0,3.6,0,1,.65),(0,4.7,0,.85,.55),(0,5.4,0,1.55,.6),(0,5.8,0,.75,.5)],robe,32,pleat=.10)
    cloth.loft([(0,3.8,0,1.06,.7),(0,4.3,0,1.05,.69)],(87,72,51),24)
    skin.loft([(0,5.6,0,.35,.3),(0,6.8,-.1,.3,.28)],(167,157,128),12)
    # Asymmetric hunched pose and individually jointed long fingers.
    for side in [-1,1]:
        elbow=(side*1.9,3.8,-.15);hand=(side*2.1,2.1,-.5)
        cloth.beam((side*1.15,5.25,0),elbow,.55,robe,12,.38)
        cloth.beam(elbow,(side*2.05,2.8,-.4),.38,robe,12,.24)
        skin.beam((side*2.05,2.9,-.4),hand,.19,(169,160,137),9,.16)
        skin.ellipsoid((side*2.1,1.95,-.5),(.5,.65,.3),(169,160,137),10,6)
        for finger in range(4):
            x=side*2.1+(finger-1.5)*.135;y=1.7-abs(finger-1.5)*.07
            mid=(x,1.05,-.65);tip=(x,.65,-.87)
            skin.beam((x,y,-.5),mid,.065,(171,160,132),6,.05)
            skin.beam(mid,tip,.05,(171,160,132),6,.025)
            dark.beam(tip,(x,.45,-1),.035,TRIM,5,.002)
    # Sculpted porcelain noh mask: pronounced cheeks, brow and nose.
    skin.loft([(0,6.25,-.24,.25,.26),(0,6.5,-.23,.55,.42),(0,7,-.2,.72,.5),(0,7.55,-.15,.7,.49),(0,7.95,-.08,.45,.35),(0,8.08,0,.08,.08)],(222,216,187),20)
    for side in [-1,1]:
        dark.ellipsoid((side*.33,7.4,-.635),(.48,.17,.13),(28,30,30),12,5)
        accent.ellipsoid((side*.33,7.4,-.71),(.065,.055,.04),(245,163,83),8,4)
        skin.beam((side*.1,7.58,-.64),(side*.58,7.65,-.54),.10,(205,199,171),8,.07)
        for j in range(3):dark.beam((side*(.32+j*.04),7.15-j*.2,-.65),(side*(.36+j*.04),7-j*.2,-.64),.018,(98,77,66),4)
    skin.loft([(0,6.99,-.72,.11,.12),(0,7.12,-.75,.14,.16),(0,7.5,-.59,.055,.06)],(207,198,166),8)
    dark.ellipsoid((0,6.7,-.62),(.25,.36,.10),(47,31,30),12,5)
    if variant==0:
        # Flowing separate hair locks; face remains visible through the silhouette.
        for j in range(15):
            a=j*math.tau/15
            if math.sin(a)<-.45:continue
            x,z=math.cos(a)*.7,math.sin(a)*.55
            dark.loft([(x,4.7,z,.07,.07),(x*1.25,5.6,z*1.25,.16,.13),(x*1.2,7.4,z*1.2,.18,.15),(x*.65,8.1,z*.65,.12,.12)],(25,33,36),7)
        cloth.loft([(0,7.8,.1,.65,.55),(0,8.22,.2,.55,.4),(0,8.3,.2,.1,.1)],(192,193,177),16)
        for side in [-1,1]:cloth.loft([(side*.9,4.6,.35,.13,.2),(side*.95,6.4,.35,.25,.35),(side*.65,7.9,.18,.25,.3)],(184,189,173),12)
    elif variant==1:
        # Broad woven kasa hat, ragged collar and substantial prayer beads.
        cloth.loft([(0,7.7,0,2.1,2.1),(0,7.9,0,2.15,2.15),(0,8.7,0,.3,.3),(0,8.8,0,.02,.02)],(136,120,75),28)
        for i in range(28):
            a=i*math.tau/28;dark.beam((math.cos(a)*2.1,7.83,math.sin(a)*2.1),(math.cos(a)*.25,8.71,math.sin(a)*.25),.025,(88,79,54),4)
        for i in range(18):
            a=i*math.tau/18;accent.ellipsoid((math.cos(a)*1.05,5+math.sin(a)*.6,-.62),(.28,.28,.28),(126,88,54),8,5)
    else:
        for side in [-1,1]:
            skin.loft([(side*.52,7.8,.02,.24,.23),(side*.8,8.25,.05,.20,.19),(side*.98,8.8,.13,.12,.11),(side*.9,9.35,.2,.005,.005)],(210,190,142),10)
        for i in range(5):accent.box((0,4.5+i*.2,-.68),(1.8,.12,.18),(163,130,63))
        dark.loft([(0,7.7,.2,.8,.6),(0,8.1,.2,.65,.5),(0,8.3,.2,.2,.2)],(34,31,30),16)
    # Invisible anchor for spatial sound, followed by separate material meshes.
    scene.part('Voice anchor',[.1,.1,.1],cf(0,6,0),alpha=1,collide=False)
    for name,m,mat in [('Cloth',cloth,'Fabric'),('Porcelain',skin,'SmoothPlastic'),('Hair and inlays',dark,'SmoothPlastic'),('Ornaments',accent,'Metal')]:
        key=f'spirit{variant}_{name}';scene.register(key,m,mat);scene.inst(key,cf())
    monsters.append(scene.data())

assets=BASE/'assets'
for name,data in [('village.json',world.data()),('monsters.json',dict(schema=2,models=monsters))]:
    (assets/name).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
manifest=dict(schema=1,title='Kage Village',version='2.0.0',files={})
for p in sorted(assets.rglob('*')):
    if p.is_file():manifest['files'][p.relative_to(BASE).as_posix()]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(BASE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Village:',len(world.meshes),'unique meshes,',len(world.instances),'instances,',sum(len(v['faces']) for v in world.meshes.values()),'unique triangles')
print('Monsters:',[sum(len(v['faces']) for v in s['meshes'].values()) for s in monsters],'triangles')
