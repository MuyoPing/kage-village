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
    def __init__(self): self.vertices=[]; self.faces=[]; self.colors=[]; self.smooth=set();self.uvs={}
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
            self.smooth.update(ids[-1])
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
            self.smooth.update(ids[-1])
        for i in range(n):
            k=(i+1)%n;self.quad(ids[0][i],ids[1][i],ids[1][k],ids[0][k],color)
        for j in [0,1]:
            center=self.vert(a if j==0 else b)
            for i in range(n):
                k=(i+1)%n
                self.tri(center,ids[j][i],ids[j][k],color) if j==0 else self.tri(center,ids[j][k],ids[j][i],color)
    def data(self):
        normals=np.zeros((len(self.vertices),3));verts=np.array(self.vertices)
        for a,b,c in self.faces:
            n=np.cross(verts[b-1]-verts[a-1],verts[c-1]-verts[a-1])
            for i in [a,b,c]:normals[i-1]+=n
        norms=[]
        for i,n in enumerate(normals):
            length=np.linalg.norm(n)
            norms.append([round(float(v),5) for v in n/length] if i+1 in self.smooth and length>1e-8 else False)
        return {'vertices':self.vertices,'faces':self.faces,'colors':self.colors,'normals':norms,'uvs':[self.uvs.get(i+1,False) for i in range(len(self.vertices))]}

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
for i,z in enumerate([-285,-175,-55,65,185]):
    place_house(-36,z,-PI/2,(i+1)%4)
    place_house(36,z,PI/2,(i+2)%4)

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
            leaves.ellipsoid((tip[0]*.65,y+.6,tip[2]*.65),(radius*1.25,2.4,radius*1.18),tint((62,100,84),R.uniform(.8,1.2)),10,5)
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

# Street dressing: hand-built maple trees, bamboo, gardens and shop objects.
for variant in range(3):
    trunk=Mesh();crown=Mesh();height=12+variant*2
    trunk.beam((0,0,0),(.5,height*.7,.2),.48,WOOD,10,.19)
    for j in range(7):
        a=j*math.tau/7+.4;reach=R.uniform(3.5,6);y=height+R.uniform(-2,2)
        tip=(math.cos(a)*reach,y,math.sin(a)*reach)
        trunk.beam((.3,height*.55,0),tip,.20,WOOD,7,.035)
        for k in range(3):
            center=(tip[0]+R.uniform(-1.5,1.5),tip[1]+R.uniform(-.4,1.2),tip[2]+R.uniform(-1.5,1.5))
            crown.ellipsoid(center,(R.uniform(3,5),R.uniform(1.5,2.8),R.uniform(3,5)),tint([(164,73,39),(190,102,42),(153,57,37)][variant],R.uniform(.8,1.2)),9,5)
    world.register('Maple trunk'+str(variant),trunk,'Wood');world.register('Maple leaves'+str(variant),crown,'Grass')
for i,(x,z) in enumerate([(x,z) for x in [-35,35] for z in [-260,-205,-150,-85,-25,45,105,165,225]]):
    for name in ['Maple trunk','Maple leaves']:world.inst(name+str(i%3),cf(x,0,z,R.random()*math.tau))
    world.inst('Moss rock'+str(i%5),cf(x+5,0,z+4,R.random()*6))
    for j in range(4):world.inst('Meadow grass',cf(x+R.uniform(-5,5),.1,z+R.uniform(-5,5),R.random()*6))

bamboo=Mesh()
for j in range(9):
    x,z=R.uniform(-3,3),R.uniform(-3,3);height=R.uniform(13,20)
    bamboo.beam((x,0,z),(x+.4,height,z),.17,(96,124,71),9,.12)
    for y in range(2,int(height),2):
        bamboo.loft([(x+.4*y/height,y,z,.20,.20),(x+.4*y/height,y+.13,z,.20,.20)],(133,143,87),9)
    for k in range(5):
        a=R.random()*math.tau;y=height-1-k*1.4
        tip=(x+math.cos(a)*2.5,y+1,z+math.sin(a)*2.5)
        bamboo.beam((x,y,z),tip,.045,(85,109,62),5,.01)
        for q in range(3):
            p=np.array(tip)+np.array([R.uniform(-.6,.6),R.uniform(-.5,.5),R.uniform(-.6,.6)])
            v=[bamboo.vert(p),bamboo.vert(p+np.array([.3,.1,.3])),bamboo.vert(p+np.array([math.cos(a),.3,math.sin(a)])*1.4)]
            bamboo.tri(*v,(75,115,67))
world.register('Bamboo grove',bamboo,'Grass')
for x in [-100,100,-260,260]:
    for z in [-190,-60,70,190]:world.inst('Bamboo grove',cf(x,0,z,R.random()*6))

props=Mesh()
# Stacked sake barrels with hoops, crates, firewood and woven baskets.
for x,y,z in [(-1.5,1.2,0),(1.5,1.2,0),(0,3.4,0)]:
    props.loft([(x,y-1,z,.9,.9),(x,y-.7,z,1.05,1.05),(x,y+.7,z,1.05,1.05),(x,y+1,z,.9,.9)],(169,137,89),16)
    for dy in [-.7,.7]:props.loft([(x,y+dy,z,1.07,1.07),(x,y+dy+.12,z,1.07,1.07)],TRIM,16)
for x in [-2,-1,0,1,2]:props.beam((x,.4,2),(x,.4,4),.37,tint(WOOD,1.2),9)
world.register('Sake barrels and firewood',props,'Wood')
for x in [-180,-60,60,180]:
    for z in [-185,-65,65,185]:world.inst('Sake barrels and firewood',cf(x+R.choice([-1,1])*10,0,z+14,R.random()*.3))

# A shallow water garden occupies unused east-side courtyard; no road crossings.
pond=Mesh();rim=Mesh()
pond.ellipsoid((0,-.12,0),(40,.4,30),(55,112,116),32,4)
for i in range(24):
    a=i*math.tau/24
    rim.ellipsoid((math.cos(a)*20,.4,math.sin(a)*15),(R.uniform(3,5),R.uniform(1,2.2),R.uniform(3,4)),tint(STONE,R.uniform(.7,1.15)),8,5)
world.register('Reflecting pond',pond,'Glass');world.register('Pond stones',rim,'Slate')
world.inst('Reflecting pond',cf(76,0,300));world.inst('Pond stones',cf(76,0,300))
bridge=Mesh()
for i in range(20):
    x=-11+i*1.15;y=.7+2.2*(1-(x/12)**2)
    bridge.box((x,y,0),(1.08,.25,7),WOOD)
    if i%3==0:
        for z in [-3.4,3.4]:bridge.box((x,y+1.7,z),(.24,3.4,.24),RED)
    if i>0:
        px=x-1.15;py=.7+2.2*(1-(px/12)**2)
        for z in [-3.4,3.4]:bridge.beam((px,py+3,z),(x,y+3,z),.15,RED,8)
world.register('Arched garden bridge',bridge,'Wood');world.inst('Arched garden bridge',cf(76,0,300))

# Hanging paper lanterns and sagging rope break up the empty main-street skyline.
string=Mesh();paper=Mesh()
for i in range(18):
    x=-17+i*2;nx=x+2;y=12.5+1.6*(x/18)**2;ny=12.5+1.6*(nx/18)**2
    string.beam((x,y,0),(nx,ny,0),.055,TRIM,5)
    if i%3==0:
        paper.loft([(x,y-2,0,.3,.3),(x,y-1.8,0,.65,.65),(x,y-.7,0,.7,.7),(x,y-.4,0,.35,.35)],(235,156,81),12)
        for dy in [-2,-.4]:string.loft([(x,y+dy,0,.38,.38),(x,y+dy+.15,0,.38,.38)],TRIM,12)
world.register('Lantern festival rope',string,'Fabric');world.register('Hanging paper lanterns',paper,'Neon')
for z in [-225,-105,15,135,255]:
    for key in ['Lantern festival rope','Hanging paper lanterns']:world.inst(key,cf(0,0,z))

# Courtyard enclosure: timber arcades, gardens, broken screens and debris.
enclosure=Mesh();roofline=Mesh();garden=Mesh();debris=Mesh()
for z in range(-40,41,4):
    for x in [-39,39]:
        enclosure.box((x,3.2,z),(1,6.4,3.9),(117,116,99))
        enclosure.box((x,6.6,z),(1.5,.35,4),(43,54,54))
        enclosure.box((x,2,z),(.2,4,3.8),(68,61,47))
for x in range(-36,37,4):
    for z in [-40,40]:
        if abs(x)<8:continue
        enclosure.box((x,3.2,z),(3.9,6.4,1),(117,116,99))
        enclosure.box((x,6.6,z),(4,.35,1.5),(43,54,54))
for x in [-24,24]:
    for z in range(-30,31,6):
        roofline.box((x,4,z),(.32,8,.32),TRIM)
        roofline.box((x,8.2,z),(6,.3,5.9),(61,67,59))
    roofline.box((x,.2,0),(6,.25,66),WOOD)
    roofline.box((x,7.7,0),(.4,.5,66),TRIM)
for i in range(32):
    x=R.choice([-1,1])*R.uniform(17,33);z=R.uniform(-33,33)
    garden.ellipsoid((x,.35,z),(R.uniform(1,3),R.uniform(.4,1.1),R.uniform(1,3)),tint(STONE,R.uniform(.6,.95)),7,5)
for i in range(24):
    debris.box((R.uniform(-5,5),.15,R.uniform(-4,4)),(R.uniform(.5,2),.12,.3),tint(WOOD,R.uniform(.6,1)),R.random()*6)
for key,m,mat in [('Courtyard walls',enclosure,'Plaster'),('Covered walkway',roofline,'Wood'),('Garden stonework',garden,'Slate'),('Broken planks',debris,'Wood')]:world.register(key,m,mat)
for x in [-180,-60,60,180]:
    for z in [-185,-65,65,185]:
        for key in ['Courtyard walls','Covered walkway','Garden stonework']:world.inst(key,cf(x,0,z))
        world.inst('Broken planks',cf(x+12,0,z-23,R.random()*6))
        for dx in [-29,29]:
            world.inst('Bamboo grove',cf(x+dx,0,z+27,R.random()*6))
        # Doorways remain open on both road-facing sides.
        for dx in [-39,39]:world.collider('Courtyard side',[1,6.4,81],cf(x+dx,3.2,z))
        for dz in [-40,40]:
            for dx in [-24,24]:world.collider('Courtyard facade',[31,6.4,1],cf(x+dx,3.2,z+dz))
# Close roadside silhouettes: crooked power poles, sagging cables and notices.
pole=Mesh();pole.beam((0,0,0),(.7,24,.2),.25,TRIM,10,.14)
pole.box((.7,21,.2),(7,.22,.25),TRIM)
for x in [-2.4,0,2.4]:pole.ellipsoid((x+.7,21.3,.2),(.4,.6,.4),(87,104,99),8,5)
world.register('Utility pole',pole,'Wood')
wire=Mesh()
for k in range(20):
    t=k/20;u=(k+1)/20
    for x in [-2.4,0,2.4]:wire.beam((x,21-3*math.sin(t*PI),t*60),(x,21-3*math.sin(u*PI),u*60),.035,(24,29,28),5)
world.register('Sagging cables',wire,'SmoothPlastic')
for z in range(-300,301,60):
    world.inst('Utility pole',cf(-18,0,z))
    if z<300:world.inst('Sagging cables',cf(-18,0,z))
from sculpt_creatures import build_creatures
monsters=build_creatures(Scene,Mesh,cf)

assets=BASE/'assets'
for name,data in [('village.json',world.data()),('monsters.json',dict(schema=2,models=monsters))]:
    (assets/name).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
manifest=dict(schema=1,title='Kage Village',version='2.0.0',files={})
for p in sorted(assets.rglob('*')):
    if p.is_file():manifest['files'][p.relative_to(BASE).as_posix()]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(BASE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Village:',len(world.meshes),'unique meshes,',len(world.instances),'instances,',sum(len(v['faces']) for v in world.meshes.values()),'unique triangles')
print('Monsters:',[sum(len(v['faces']) for v in s['meshes'].values()) for s in monsters],'triangles')
