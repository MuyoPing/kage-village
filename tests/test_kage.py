from pathlib import Path
import json,math
import numpy as np
from collections import deque
from lupa import LuaRuntime
base=Path(__file__).resolve().parents[1];world=json.loads((base/'assets/village.json').read_text(encoding='utf-8'))
# Conservative 2D player-clearance grid at the movement collider's height.
xs=np.arange(-360,361,2);zs=np.arange(-380,381,2);X,Z=np.meshgrid(xs,zs);blocked=np.zeros(X.shape,dtype=bool)
for p in world['parts']:
 if not p['collide']:continue
 pos=np.array(p['cf'][:3]);R=np.array(p['cf'][3:]).reshape(3,3);size=np.array(p['size'])
 extent=np.abs(R)@(size/2)
 if pos[1]+extent[1]<1.75 or pos[1]-extent[1]>3.85:continue
 # Local coordinates for rotated solid; conservative expanded rectangle.
 dx=X-pos[0];dz=Z-pos[2]
 lx=dx*R[0,0]+dz*R[2,0];lz=dx*R[0,2]+dz*R[2,2]
 blocked|=(np.abs(lx)<size[0]/2+1.05)&(np.abs(lz)<size[2]/2+1.05)
start=(int((-302-zs[0])/2),int((0-xs[0])/2));assert not blocked[start]
seen={start};q=deque([start])
while q:
 z,x=q.popleft()
 for dz,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
  zz,xx=z+dz,x+dx
  if 0<=zz<len(zs) and 0<=xx<len(xs) and not blocked[zz,xx] and (zz,xx) not in seen:seen.add((zz,xx));q.append((zz,xx))
for name,(x,z),radius in [('inn',(-60,-185),10),('tea',(180,-65),10),('well',(-220,45),10),('grave',(200,310),10),('shrine',(0,330),10),('bell',(0,318),13)]:
 assert any((xs[i]-x)**2+(zs[j]-z)**2<radius**2 for j,i in seen),name
print('PASS: all five seals and bell reachable from entrance on conservative collision grid')
source=(base/'KageVillage.luau').read_text(encoding='utf-8')
lua=LuaRuntime()
lua.execute('''
Vector3={}
local mt={}
mt.__index=function(v,k) if k=='Magnitude' then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end end
mt.__sub=function(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
function Vector3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end
nodes={}
for _,z in ipairs({-240,-120,0,120,240}) do for _,x in ipairs({-240,-120,0,120,240}) do nodes[#nodes+1]=Vector3.new(x,4.8,z) end end
''')
a=source.index('local function nearestNode');b=source.index('local bellPosition',a)
lua.execute(source[a:b]+'\nrouteTest=route')
lua.execute('''
for i,a in ipairs(nodes) do for j,b in ipairs(nodes) do
 local path=routeTest(a,b)
 assert(path[1]==a and path[#path]==b)
 for k=2,#path do assert(math.abs((path[k]-path[k-1]).Magnitude-120)<.01) end
end end
''')
print('PASS: all 625 monster road routes have valid endpoints and adjacent waypoints')
