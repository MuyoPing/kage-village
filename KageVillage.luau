-- 影の里 / KAGE VILLAGE — original triangulated mesh edition, v2.0
-- Standalone client script. E interact, WASD move, mouse look, Shift sprint,
-- F lantern, M volume, Q quality, Backspace leave, Delete unload (outside).
-- Models are original JSON geometry loaded from GitHub or the local workspace.
-- No asset scripts are executed. The map and virtual camera remain local.
-- Original geometry/audio authored in build_assets.py; see README-KO.md.
local Config = {
    Language = "ko", Quality = "High", Volume = 0.55, Seed = 140026,
    BaseUrl = "", -- GitHub raw root, supplied by the GitHub loader.
    LocalFolder = "KageVillage", -- For testing from executor workspace.
    AudioIds = {}, -- Optional SoundId overrides.
    AutoKunai = true,
    Development = false,
    PortalOffset = CFrame.new(0,0,-22),
}

local env = (getgenv and getgenv()) or _G
if env.KageVillage and env.KageVillage.Destroy then env.KageVillage:Destroy() end
local sourceConfig=env.KageVillageSource or {}
for _,key in ipairs({"BaseUrl","LocalFolder","Language","Quality","Volume","AutoKunai","Development"}) do if sourceConfig[key]~=nil then Config[key]=sourceConfig[key] end end
local Players=game:GetService("Players")
local Run=game:GetService("RunService")
local Input=game:GetService("UserInputService")
local Lighting=game:GetService("Lighting")
local SoundService=game:GetService("SoundService")
local Tween=game:GetService("TweenService")
local player=Players.LocalPlayer
local character=player.Character or player.CharacterAdded:Wait()
local hrp=character:WaitForChild("HumanoidRootPart")
local rng=Random.new(Config.Seed)
local root=Instance.new("Folder"); root.Name="Ovitar_KageVillage_Local"; root.Parent=workspace
local map=Instance.new("Model"); map.Name="KageVillage"; map.Parent=root
local entrance=Instance.new("Model"); entrance.Name="KageVillage_Entrance"; entrance.Parent=root
local origin=Vector3.new(0,12000,0)
local alive,active,building,ready=true,false,false,false
local connections,postEffects,lights,sounds,hidden={},{},{},{},{}
local enemies,seals,nodes={},{},{}
local count,elapsed,stamina,flashlight,volume=0,0,100,true,Config.Volume
local position,yaw,pitch=Vector3.new(0,4.8,-310),0,0
local keys,snapshot={},nil
local messageUntil,modalUntil,stepTimer,aiTimer=0,0,0,0
local state="entrance"
local stage=1
local stageNames={{"첫째 밤 · 빈 여관","NIGHT I · THE EMPTY INN"},{"둘째 밤 · 찻집의 손님","NIGHT II · THE LAST GUEST"},{"셋째 밤 · 우물 아래","NIGHT III · BELOW THE WELL"},{"넷째 밤 · 이름 없는 묘","NIGHT IV · THE NAMELESS GRAVES"},{"다섯째 밤 · 마지막 종","NIGHT V · THE FINAL BELL"}}
local stageModels={1,2,4,3,5}
local stageStarts={Vector3.new(0,4.8,-240),Vector3.new(120,4.8,-120),Vector3.new(-120,4.8,0),Vector3.new(120,4.8,240),Vector3.new(0,4.8,240)}
local stageSpawns={Vector3.new(-120,4.8,-120),Vector3.new(240,4.8,0),Vector3.new(-240,4.8,120),Vector3.new(240,4.8,240),Vector3.new(-120,4.8,240)}
local scare,heartbeat,chaseSound,breathing
local hostGuis={}
local kunaiSession,kunaiStatus=nil,"idle"
local high=Config.Quality=="High"
local C={wood=Color3.fromRGB(49,36,32),dark=Color3.fromRGB(22,24,28),paper=Color3.fromRGB(176,155,117),red=Color3.fromRGB(105,28,24),stone=Color3.fromRGB(60,64,60),moss=Color3.fromRGB(37,49,38)}
local function tr(ko,en) return Config.Language=="ko" and ko or en end
local function connect(signal,fn) local c=signal:Connect(fn);table.insert(connections,c);return c end
local function make(class,props,parent)
    local o=Instance.new(class)
    for k,v in pairs(props or {}) do o[k]=v end
    o.Parent=parent;return o
end
local gui=make("ScreenGui",{Name="KageVillageHUD",ResetOnSpawn=false,IgnoreGuiInset=true,DisplayOrder=150},player:WaitForChild("PlayerGui"))
local function label(text,pos,size,font,fontsize)
    return make("TextLabel",{Text=text,Position=pos,Size=size,BackgroundTransparency=1,TextColor3=Color3.fromRGB(220,214,197),TextSize=fontsize or 16,Font=font or Enum.Font.Gotham,TextWrapped=true},gui)
end
local title=label("影 の 里",UDim2.fromScale(.05,.055),UDim2.fromScale(.45,.07),Enum.Font.Garamond,38);title.TextXAlignment=Enum.TextXAlignment.Left
local subtitle=label("K A G E  V I L L A G E",UDim2.fromScale(.052,.125),UDim2.fromScale(.4,.025),nil,11);subtitle.TextXAlignment=Enum.TextXAlignment.Left
local objective=label("",UDim2.fromScale(.05,.17),UDim2.fromScale(.6,.05),nil,15);objective.TextXAlignment=Enum.TextXAlignment.Left
local prompt=label("",UDim2.fromScale(.2,.73),UDim2.fromScale(.6,.08),nil,19)
local note=label(tr("네 앞에 붉은 문이 나타났다. 가까이 가서 E를 누르세요.","A red gate has appeared. Approach it and press E."),UDim2.fromScale(.18,.84),UDim2.fromScale(.64,.07),nil,17)
local controls=label(tr("WASD 이동 · Shift 달리기 · F 등불 · E 상호작용 · M 음량 · Q 그래픽 · Backspace 나가기","WASD move · Shift sprint · F lantern · E interact · M volume · Q graphics · Backspace leave"),UDim2.fromScale(.04,.95),UDim2.fromScale(.92,.035),nil,12)
local meter=make("Frame",{Position=UDim2.fromScale(.4,.92),Size=UDim2.fromScale(.2,.003),BackgroundColor3=C.paper,BorderSizePixel=0,Visible=false},gui)
local cross=label("·",UDim2.fromScale(.49,.48),UDim2.fromScale(.02,.04),nil,24);cross.Visible=false
local veil=make("Frame",{Size=UDim2.fromScale(1,1),BackgroundColor3=Color3.new(0,0,0),BackgroundTransparency=1,BorderSizePixel=0,ZIndex=20},gui)
local caption=make("TextLabel",{Position=UDim2.fromScale(.12,.38),Size=UDim2.fromScale(.76,.24),BackgroundTransparency=1,TextColor3=C.paper,Font=Enum.Font.Garamond,TextSize=34,TextWrapped=true,Text="",ZIndex=21},gui)
-- Soft edge shading, no external texture dependency.
for _,side in ipairs({0,1}) do
    local shade=make("Frame",{Position=UDim2.fromScale(side==0 and 0 or .8,0),Size=UDim2.fromScale(.2,1),BackgroundColor3=Color3.new(),BorderSizePixel=0},gui)
    make("UIGradient",{Rotation=side==0 and 0 or 180,Transparency=NumberSequence.new({NumberSequenceKeypoint.new(0,.2),NumberSequenceKeypoint.new(1,1)})},shade)
end
local function message(s,duration) note.Text=s;messageUntil=elapsed+(duration or 5) end
local function part(parent,name,size,cf,color,material,collide)
    return make("Part",{Name=name,Size=size,CFrame=cf,Color=color or C.wood,Material=material or Enum.Material.Wood,Anchored=true,CanCollide=collide~=false,CanTouch=false,TopSurface=Enum.SurfaceType.Smooth,BottomSurface=Enum.SurfaceType.Smooth},parent)
end
local function localPart(parent,name,size,cf,color,material,collide) return part(parent,name,size,CFrame.new(origin)*cf,color,material,collide) end
local function torii(parent,cf,scale)
    local function p(n,s,off,c) return part(parent,n,s*scale,cf*CFrame.new(off*scale),c,Enum.Material.Wood,true) end
    p("Left pillar",Vector3.new(1.2,16,1.2),Vector3.new(-7,8,0),C.red)
    p("Right pillar",Vector3.new(1.2,16,1.2),Vector3.new(7,8,0),C.red)
    p("Upper beam",Vector3.new(20,1.1,2.6),Vector3.new(0,16,0),C.dark)
    p("Red crossbeam",Vector3.new(17,.8,1.1),Vector3.new(0,12,0),C.red)
    p("Name plaque",Vector3.new(2.2,3,.3),Vector3.new(0,14,-.7),C.wood)
end
local portalCF
local function relocatePortal()
    local h=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not h or active then return end
    local target=(h.CFrame*Config.PortalOffset).Position
    local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Exclude;params.FilterDescendantsInstances={root,player.Character}
    local hit=workspace:Raycast(target+Vector3.new(0,15,0),Vector3.new(0,-80,0),params)
    local ground=hit and hit.Position or target-Vector3.new(0,3,0)
    local _,angle=h.CFrame:ToOrientation()
    portalCF=CFrame.new(ground)*CFrame.Angles(0,angle,0)
    entrance:ClearAllChildren();torii(entrance,portalCF,1)
    local door=part(entrance,"Threshold",Vector3.new(12,12,.15),portalCF*CFrame.new(0,6,0),Color3.fromRGB(6,7,10),Enum.Material.Glass,false)
    door.Transparency=.25
    make("PointLight",{Color=Color3.fromRGB(170,48,35),Brightness=1.5,Range=20},door)
end
relocatePortal()
local Http=game:GetService("HttpService")
local AssetService=game:GetService("AssetService")
local meshCache,editableMeshes,textureCache={},{},{}
local function assetBytes(path)
    assert(not path:find("..",1,true), "Invalid asset path")
    if Config.BaseUrl~="" then
        local base=Config.BaseUrl:gsub("/$", "")
        return game:HttpGet(base.."/"..path)
    end
    assert(readfile, "Set KageVillageSource.BaseUrl to your GitHub raw root, or enable readfile for local testing")
    return readfile(Config.LocalFolder.."/"..path)
end
local function assetJSON(path)
    local value=Http:JSONDecode(assetBytes(path))
    assert(type(value)=="table" and (value.schema==1 or value.schema==2),"Unsupported model format: "..path)
    return value
end
local audioAssets={}
local function prepareAudio()
    local custom=getcustomasset or getsynasset
    local missing=0
    for _,name in ipairs({"Wind","Drone","Step","Step2","Run1","Run2","Bell","Whisper","Stinger","Heartbeat","Chase","Breath","Transition"}) do
        if not alive then return end
        local id=Config.AudioIds[name]
        if not id and custom and writefile and makefolder then
            local ok,result=pcall(function()
                pcall(makefolder,"OvitarKageAudio")
                local path="OvitarKageAudio/"..name.."-v2.wav"
                writefile(path,assetBytes("assets/audio/"..name..".wav"))
                return custom(path)
            end)
            if ok then id=result else warn("Kage audio: "..tostring(result)) end
        end
        if id then audioAssets[name]=tostring(id):match("^%d+$") and "rbxassetid://"..id or id else missing=missing+1 end
        task.wait()
    end
    Config.MissingAudio=missing
end
local function sound(name,loop,gain,parent)
    local id=audioAssets[name];if not id then return nil end
    local s=make("Sound",{Name=name,SoundId=id,Looped=loop,Volume=volume*gain,RollOffMinDistance=8,RollOffMaxDistance=130},parent or SoundService)
    s:SetAttribute("KageGain",gain);sounds[s]=true;s:Play()
    if not loop then
        s.Ended:Once(function() sounds[s]=nil;s:Destroy() end)
        task.delay(12,function() if sounds[s] then sounds[s]=nil;s:Destroy() end end)
    end
    return s
end
local function stopSounds() for s in pairs(sounds) do s:Destroy() end;table.clear(sounds) end
local function objectivePoint(pos,name,description)
    local pedestal=localPart(map,name,Vector3.new(3,3,3),CFrame.new(pos+Vector3.new(0,1.5,0)),C.stone,Enum.Material.Slate)
    local seal=localPart(map,"Ofuda",Vector3.new(1.1,2,.12),CFrame.new(pos+Vector3.new(0,4,0)),C.paper,Enum.Material.Fabric,false)
    local h=make("PointLight",{Color=Color3.fromRGB(120,176,183),Brightness=.8,Range=12},seal)
    make("Decal",{Color3=Color3.fromRGB(120,35,26),Transparency=1},seal)
    local gui2=make("SurfaceGui",{Face=Enum.NormalId.Front,PixelsPerStud=40},seal)
    make("TextLabel",{Size=UDim2.fromScale(1,1),BackgroundTransparency=1,Text="封\n印",Font=Enum.Font.Garamond,TextSize=24,TextColor3=C.red},gui2)
    table.insert(seals,{position=pos+Vector3.new(0,4,0),part=seal,pedestal=pedestal,collected=false,name=name,story=description,light=h})
end
local monsterData
local function textureAsset(path)
    if textureCache[path] then return textureCache[path] end
    local custom=getcustomasset or getsynasset
    if not custom or not writefile or not makefolder then Config.MissingTextures=true;return nil end
    local ok,id=pcall(function()
        pcall(makefolder,"OvitarKageTextures")
        local localPath="OvitarKageTextures/"..path:match("([^/]+)$")
        writefile(localPath,assetBytes(path));return custom(localPath)
    end)
    if ok then textureCache[path]=id;return id end
    Config.MissingTextures=true;warn("Kage texture: "..tostring(id));return nil
end
local function meshTemplate(key,data)
    if meshCache[key] then return meshCache[key] end
    assert(type(data.vertices)=="table" and #data.vertices<=60000,"Invalid mesh vertices")
    assert(type(data.faces)=="table" and #data.faces<=20000,"Invalid mesh triangles")
    local editable=AssetService:CreateEditableMesh()
    assert(editable,"3D mesh memory unavailable. Close other mesh experiences and retry.")
    editableMeshes[#editableMeshes+1]=editable
    local low,highBound=Vector3.new(math.huge,math.huge,math.huge),Vector3.new(-math.huge,-math.huge,-math.huge)
    local positions={}
    for i,v in ipairs(data.vertices) do
        assert(#v==3,"Invalid mesh vertex")
        for _,n in ipairs(v) do assert(type(n)=="number" and n==n and math.abs(n)<10000,"Invalid mesh coordinate") end
        local p=Vector3.new(v[1],v[2],v[3]);positions[i]=p
        low=low:Min(p);highBound=highBound:Max(p)
    end
    local center=(low+highBound)*.5
    local vertices,uvs,colors,normals,vertexNormals={},{},{},{},{}
    for i,p in ipairs(positions) do
        vertices[i]=editable:AddVertex(p-center)
        local uv=data.uvs and data.uvs[i]
        uvs[i]=editable:AddUV(type(uv)=="table" and Vector2.new(uv[1],uv[2]) or Vector2.new((p.X+p.Y)*.12,(p.Z+p.Y)*.12))
        local n=data.normals and data.normals[i]
        if type(n)=="table" then vertexNormals[i]=editable:AddNormal(Vector3.new(n[1],n[2],n[3])) end
    end
    for i,f in ipairs(data.faces) do
        assert(#f==3 and vertices[f[1]] and vertices[f[2]] and vertices[f[3]],"Invalid mesh face")
        local n=(positions[f[2]]-positions[f[1]]):Cross(positions[f[3]]-positions[f[1]])
        if n.Magnitude>.000001 then
            local face=editable:AddTriangle(vertices[f[1]],vertices[f[2]],vertices[f[3]])
            local c=data.colors[i];local ck=table.concat(c,",")
            if not colors[ck] then colors[ck]=editable:AddColor(Color3.fromRGB(c[1],c[2],c[3]),1) end
            editable:SetFaceColors(face,{colors[ck],colors[ck],colors[ck]})
            editable:SetFaceUVs(face,{uvs[f[1]],uvs[f[2]],uvs[f[3]]})
            n=n.Unit;local nk=string.format("%.3f,%.3f,%.3f",n.X,n.Y,n.Z)
            if not normals[nk] then normals[nk]=editable:AddNormal(n) end
            editable:SetFaceNormals(face,{vertexNormals[f[1]] or normals[nk],vertexNormals[f[2]] or normals[nk],vertexNormals[f[3]] or normals[nk]})
        end
        if i%400==0 then task.wait();if not alive then error("Loading cancelled") end end
    end
    -- Fixed topology uses less client memory; keep the content alive for clones.
    local compactOk,compact=pcall(function() return AssetService:CreateEditableMeshAsync(Content.fromObject(editable),{FixedSize=true}) end)
    if compactOk and compact then
        editable:Destroy();editableMeshes[#editableMeshes]=compact;editable=compact
    end
    local template=AssetService:CreateMeshPartAsync(Content.fromObject(editable),{CollisionFidelity=Enum.CollisionFidelity.Box,RenderFidelity=Enum.RenderFidelity.Precise})
    if not alive then template:Destroy();editable:Destroy();error("Loading cancelled") end
    template.Name=key;template.Anchored=true;template.CanCollide=false;template.CanTouch=false;template.CanQuery=false
    template.DoubleSided=true;template.Color=Color3.new(1,1,1)
    template.Material=Enum.Material[data.material] or Enum.Material.SmoothPlastic
    if data.texture then local id=textureAsset(data.texture);if id then template.TextureID=id end end
    local result={part=template,center=center};meshCache[key]=result
    return result
end
local function buildGeometry(data,parent,offset)
    assert(type(data.parts)=="table" and #data.parts<=20000,"Invalid geometry count")
    local parts={}
    for i,d in ipairs(data.parts) do
        assert(type(d.cf)=="table" and #d.cf==12 and #d.size==3 and #d.color==3,"Invalid part record")
        for _,v in ipairs(d.cf) do assert(type(v)=="number" and v==v and math.abs(v)<100000,"Invalid transform") end
        for _,v in ipairs(d.size) do assert(type(v)=="number" and v>.01 and v<=2048,"Invalid size") end
        local transform=CFrame.new(offset)*CFrame.new(table.unpack(d.cf))
        local material=Enum.Material.SmoothPlastic
        pcall(function() material=Enum.Material[d.material] end)
        local piece
        if d.shape=="Wedge" then
            piece=make("WedgePart",{Name=d.name,Size=Vector3.new(table.unpack(d.size)),CFrame=transform,Color=Color3.fromRGB(table.unpack(d.color)),Material=material,Anchored=true,CanCollide=d.collide~=false,CanTouch=false},parent)
        else
            piece=part(parent,d.name,Vector3.new(table.unpack(d.size)),transform,Color3.fromRGB(table.unpack(d.color)),material,d.collide)
            if d.shape=="Ball" then piece.Shape=Enum.PartType.Ball
            elseif d.shape=="CylinderY" then
                piece.Shape=Enum.PartType.Cylinder
                piece.Size=Vector3.new(d.size[2],d.size[1],d.size[3])
                piece.CFrame=transform*CFrame.Angles(0,0,math.pi/2)
            end
        end
        piece.Transparency=d.alpha or 0
        piece.CanQuery=d.collide~=false
        parts[i]=piece
        if i%160==0 then
            if not alive then error("Loading cancelled") end
            caption.Text=tr("影の里\n마을 불러오는 중 ","KAGE VILLAGE\nLoading village ")..math.floor(i/#data.parts*100).."%"
            task.wait()
        end
    end
    for i,d in ipairs(data.instances or {}) do
        if not alive then error("Loading cancelled") end
        local definition=assert(data.meshes[d.mesh],"Missing mesh definition")
        local cached=meshTemplate(d.mesh,definition)
        local piece=cached.part:Clone()
        piece.CFrame=CFrame.new(offset)*CFrame.new(table.unpack(d.cf))*CFrame.new(cached.center)
        piece.Parent=parent
        if i%20==0 then
            caption.Text=tr("影の里\n3D 마을 조립 중 ","KAGE VILLAGE\nAssembling 3D village ")..math.floor(i/#data.instances*100).."%"
            task.wait()
        end
    end
    return parts
end
local function buildMap()
    building=true;state="loading";veil.BackgroundTransparency=0
    caption.Text=tr("影の里\n모델 다운로드 중…","KAGE VILLAGE\nDownloading models…")
    local world=assetJSON("assets/village.json")
    monsterData=assetJSON("assets/monsters.json")
    assert(type(monsterData.models)=="table" and #monsterData.models>=5,"Missing five stage monsters")
    if not alive then return end
    map:ClearAllChildren();table.clear(lights);table.clear(nodes);table.clear(seals)
    local parts=buildGeometry(world,map,origin)
    for _,d in ipairs(world.lights or {}) do
        local l=make("PointLight",{Color=Color3.fromRGB(table.unpack(d.color)),Brightness=d.brightness,Range=d.range,Shadows=false},parts[d.part])
        lights[#lights+1]={light=l,position=Vector3.new(table.unpack(d.position)),phase=rng:NextNumber(0,6),brightness=d.brightness}
    end
    for _,d in ipairs(world.signs or {}) do
        local surface=make("SurfaceGui",{Face=Enum.NormalId.Front,PixelsPerStud=32},parts[d.part])
        make("TextLabel",{Size=UDim2.fromScale(1,1),BackgroundTransparency=1,Text=d.text,Font=Enum.Font.Garamond,TextSize=38,TextColor3=C.paper},surface)
    end
    for _,z in ipairs({-240,-120,0,120,240}) do for _,x in ipairs({-240,-120,0,120,240}) do nodes[#nodes+1]=Vector3.new(x,4.8,z) end end
    objectivePoint(Vector3.new(-60,0,-185),tr("빈 여관","Empty inn"),tr("여관의 기록: 밤에 이름을 불러도 대답하지 마라.","Inn record: Do not answer when your name is called at night."))
    objectivePoint(Vector3.new(180,0,-65),tr("찻집","Tea house"),tr("찻잔은 따뜻했다. 주인은 돌아오지 않았다.","The tea was still warm. Its owner never returned."))
    objectivePoint(Vector3.new(-220,0,45),tr("우물","The well"),tr("우물 아래에서 들리는 것은 메아리가 아니다.","What you hear below the well is not an echo."))
    objectivePoint(Vector3.new(200,0,310),tr("묘지","Cemetery"),tr("비석마다 같은 날짜가 새겨져 있다.","Every stone bears the same date."))
    objectivePoint(Vector3.new(0,0,330),tr("신사","Shrine"),tr("다섯 봉인을 모아 종을 울려라. 뒤돌아보지 마라.","Gather five seals and ring the bell. Do not look back."))
    prepareAudio()
    if not alive then return end
    ready=true;building=false
end
local monsterFolder=make("Folder",{Name="Apparitions"},root)
local function monster(start,index)
    local definition=monsterData.models[index]
    local m=make("Model",{Name=definition.name},monsterFolder)
    local parts=buildGeometry(definition,m,Vector3.zero)
    m.WorldPivot=CFrame.new()
    m:PivotTo(CFrame.new(origin+Vector3.new(start.X,0,start.Z)))
    return {model=m,voice=parts[1],position=start,index=index,mode="patrol",memory=0,target=nodes[(index*7)%#nodes+1],path={},pathIndex=1,planTime=0}
end
local collision=RaycastParams.new();collision.FilterType=Enum.RaycastFilterType.Include;collision.FilterDescendantsInstances={map};collision.RespectCanCollide=true
local function clearLine(a,b)
    local delta=b-a
    return delta.Magnitude<.01 or not workspace:Raycast(origin+a,delta,collision)
end
local function slide(pos,delta)
    if delta.Magnitude<.001 then return pos end
    local center=origin+Vector3.new(pos.X,2.8,pos.Z)
    local hit=workspace:Spherecast(center,1.05,delta,collision)
    if not hit then return pos+delta end
    local traveled=delta.Unit*math.max(0,hit.Distance-.08)
    local rest=delta-traveled;rest=rest-hit.Normal*rest:Dot(hit.Normal)
    local p=pos+traveled
    if rest.Magnitude>.001 and not workspace:Spherecast(origin+Vector3.new(p.X,2.8,p.Z),1.05,rest,collision) then p=p+rest end
    return p
end
local function nearestNode(p)
    local best,d=1,math.huge
    for i,n in ipairs(nodes) do local v=(n-p).Magnitude;if v<d then best,d=i,v end end
    return best
end
local function route(from,to)
    local first,last=nearestNode(from),nearestNode(to)
    local queue,seen,parent={first},{[first]=true},{}
    local cursor=1
    while cursor<=#queue do
        local current=queue[cursor];cursor=cursor+1
        if current==last then break end
        for j,n in ipairs(nodes) do
            if not seen[j] and math.abs((n-nodes[current]).Magnitude-120)<.01 then
                seen[j]=true;parent[j]=current;queue[#queue+1]=j
            end
        end
    end
    if not seen[last] then return {nodes[first]} end
    local result={};local n=last
    while n do table.insert(result,1,nodes[n]);if n==first then break end;n=parent[n] end
    return result
end
local bellPosition=Vector3.new(0,4.8,318)
local gatePosition=Vector3.new(0,4.8,-310)
local leave,enter
local function stopKunai()
    local session=kunaiSession;kunaiSession=nil;kunaiStatus="idle"
    if session then
        session.cancelled=true
        if session.toy and session.toy.Parent and session.destroy then pcall(function() session.destroy:FireServer(session.toy) end) end
    end
end
local function startKunai()
    stopKunai()
    if not Config.AutoKunai then return end
    local storage=game:GetService("ReplicatedStorage")
    local menu=storage:FindFirstChild("MenuToys");local events=storage:FindFirstChild("PlayerEvents")
    local spawnRemote=menu and menu:FindFirstChild("SpawnToyRemoteFunction")
    local destroy=menu and menu:FindFirstChild("DestroyToy")
    local stickyRemote=events and events:FindFirstChild("StickyPartEvent")
    if not spawnRemote or not destroy or not stickyRemote then kunaiStatus="unsupported-game";return end
    local session={destroy=destroy,character=character};kunaiSession=session;kunaiStatus="spawning"
    task.spawn(function()
        local hitbox=character and character:FindFirstChild("RagdollTouchedHitbox",true)
        local h=character and character:FindFirstChild("HumanoidRootPart")
        if not hitbox or not h then kunaiStatus="missing-hitbox";return end
        local folder=workspace:FindFirstChild(player.Name.."SpawnedInToys")
        local before={};if folder then for _,toy in ipairs(folder:GetChildren()) do before[toy]=true end end
        local finished,result=false,nil
        local requestTask=task.spawn(function()
            local ok,value=pcall(function() return spawnRemote:InvokeServer("NinjaKunai",h.CFrame*CFrame.new(0,3,5),Vector3.zero) end)
            finished=true;result=ok and value or "request-failed"
        end)
        local deadline=os.clock()+5
        repeat
            folder=workspace:FindFirstChild(player.Name.."SpawnedInToys")
            if folder then for _,toy in ipairs(folder:GetChildren()) do
                if toy.Name=="NinjaKunai" and not before[toy] then session.toy=toy;break end
            end end
            if session.toy or (finished and (result=="YouDontOwnToy" or result=="LeaveThePlot" or result=="request-failed")) then break end
            task.wait(.05)
        until os.clock()>deadline
        pcall(task.cancel,requestTask)
        if session.cancelled or not active or player.Character~=session.character then
            if session.toy then pcall(function() destroy:FireServer(session.toy) end) end;return
        end
        if not session.toy then kunaiStatus="unavailable";message(tr("닌자 쿠나이를 생성하지 못했습니다. 보유 여부와 장난감 제한을 확인하세요.","Ninja Kunai unavailable. Check ownership and the toy limit."),8);return end
        local sticky=session.toy:WaitForChild("StickyPart",2)
        if not sticky or not sticky:IsA("BasePart") then kunaiStatus="unsupported-toy";return end
        local offset=CFrame.new(.1,-.3,.3)*CFrame.Angles(math.pi/2,0,0)
        while not session.cancelled and active and alive and player.Character==session.character and sticky.Parent and hitbox.Parent do
            local weld=sticky:FindFirstChild("StickyWeld")
            if not weld or weld.Part1~=hitbox then
                local grab=storage:FindFirstChild("GrabEvents");local owner=grab and grab:FindFirstChild("SetNetworkOwner")
                if owner then owner:FireServer(sticky,CFrame.lookAt(h.Position,sticky.Position)) end
                session.toy:PivotTo(hitbox.CFrame*offset*sticky.CFrame:Inverse()*session.toy:GetPivot())
                sticky.AssemblyLinearVelocity=Vector3.zero;sticky.AssemblyAngularVelocity=Vector3.zero
                stickyRemote:FireServer(sticky,hitbox,offset);kunaiStatus="attaching"
            else kunaiStatus="attached" end
            for _,p in ipairs(session.toy:GetDescendants()) do if p:IsA("BasePart") then p.LocalTransparencyModifier=1 end end
            task.wait(1)
        end
    end)
end
local function restore()
    stopKunai()
    for object,enabled in pairs(hostGuis) do if object.Parent then object.Enabled=enabled end end;table.clear(hostGuis)
    if not snapshot then return end
    for k,v in pairs(snapshot.lighting) do pcall(function() Lighting[k]=v end) end
    for item,parent in pairs(snapshot.atmospheres) do item.Parent=parent end
    for item,value in pairs(snapshot.enabled) do if item.Parent then item.Enabled=value end end
    for _,effect in ipairs(postEffects) do effect:Destroy() end;table.clear(postEffects)
    for part,value in pairs(hidden) do if part.Parent then part.LocalTransparencyModifier=value end end;table.clear(hidden)
    if snapshot.humanoid and snapshot.humanoid.Parent then
        snapshot.humanoid.WalkSpeed=snapshot.speed;snapshot.humanoid.JumpPower=snapshot.jump;snapshot.humanoid.AutoRotate=snapshot.rotate
    end
    local camera=workspace.CurrentCamera
    if camera then
        camera.CameraType=snapshot.cameraType;camera.CameraSubject=snapshot.subject;camera.CFrame=snapshot.cameraCF;camera.FieldOfView=snapshot.fov
    end
    Input.MouseBehavior=snapshot.mouse;Input.MouseIconEnabled=snapshot.icon
    snapshot=nil
end
local lanternPart=part(root,"Player lantern light",Vector3.new(.1,.1,.1),CFrame.new(origin),C.paper,Enum.Material.SmoothPlastic,false);lanternPart.Transparency=1
local lantern=make("SpotLight",{Angle=82,Range=65,Brightness=1.5,Color=Color3.fromRGB(238,224,195),Shadows=true,Enabled=false,Face=Enum.NormalId.Front},lanternPart)
local function effects()
    snapshot={lighting={},enabled={},atmospheres={},humanoid=character:FindFirstChildOfClass("Humanoid")}
    local camera=workspace.CurrentCamera
    snapshot.cameraType=camera.CameraType;snapshot.subject=camera.CameraSubject;snapshot.cameraCF=camera.CFrame;snapshot.fov=camera.FieldOfView
    snapshot.mouse=Input.MouseBehavior;snapshot.icon=Input.MouseIconEnabled
    local settings={ClockTime=4.6,Brightness=2.1,Ambient=Color3.fromRGB(91,106,119),OutdoorAmbient=Color3.fromRGB(119,138,151),ExposureCompensation=.15,GlobalShadows=true,FogColor=Color3.fromRGB(94,123,137),FogStart=90,FogEnd=480}
    for k,v in pairs(settings) do snapshot.lighting[k]=Lighting[k];Lighting[k]=v end
    for _,o in ipairs(Lighting:GetChildren()) do
        if o:IsA("PostEffect") then snapshot.enabled[o]=o.Enabled;o.Enabled=false
        elseif o:IsA("Atmosphere") then snapshot.atmospheres[o]=o.Parent;o.Parent=nil end
    end
    local at=make("Atmosphere",{Density=.27,Offset=.15,Color=Color3.fromRGB(172,193,198),Decay=Color3.fromRGB(77,103,116),Glare=.08,Haze=1.4},Lighting)
    local cc=make("ColorCorrectionEffect",{Brightness=.015,Contrast=.12,Saturation=-.08,TintColor=Color3.fromRGB(230,240,246)},Lighting)
    local bloom=make("BloomEffect",{Intensity=.16,Size=20,Threshold=1.8},Lighting)
    local dof=make("DepthOfFieldEffect",{FarIntensity=.12,NearIntensity=0,FocusDistance=40,InFocusRadius=65,Enabled=high},Lighting)
    postEffects={at,cc,bloom,dof}
    local h=snapshot.humanoid
    if h then snapshot.speed=h.WalkSpeed;snapshot.jump=h.JumpPower;snapshot.rotate=h.AutoRotate;h.WalkSpeed=0;h.JumpPower=0;h.AutoRotate=false end
    for _,o in ipairs(character:GetDescendants()) do if o:IsA("BasePart") then hidden[o]=o.LocalTransparencyModifier;o.LocalTransparencyModifier=1 end end
    Input.MouseBehavior=Enum.MouseBehavior.LockCenter;Input.MouseIconEnabled=false
    for _,g in ipairs(player.PlayerGui:GetChildren()) do
        if g:IsA("ScreenGui") and g~=gui then hostGuis[g]=g.Enabled;g.Enabled=false end
    end
end
local nextWhisper=15
local function beginStage(index)
    stage=index;scare=nil
    for _,enemy in ipairs(enemies) do enemy.model:Destroy() end;table.clear(enemies)
    enemies[1]=monster(stageSpawns[index],stageModels[index])
    position=stageStarts[index];yaw=math.pi;pitch=0;stamina=100;state="explore"
    nextWhisper=elapsed+12;stepTimer=0;aiTimer=0
    for i,s in ipairs(seals) do s.part.Transparency=i==stage and 0 or 1;s.light.Enabled=i==stage end
    caption.Text=tr(stageNames[index][1],stageNames[index][2]);modalUntil=elapsed+3
    veil.BackgroundTransparency=0;Tween:Create(veil,TweenInfo.new(2.5),{BackgroundTransparency=1}):Play()
    sound("Transition",false,.28)
end
leave=function(reason)
    active=false;state="entrance";scare=nil;table.clear(keys);stopSounds();heartbeat=nil;chaseSound=nil;breathing=nil;lantern.Enabled=false
    restore();cross.Visible=false;meter.Visible=false;objective.Text="";caption.Text="";veil.BackgroundTransparency=1
    if alive then message(reason or tr("문 밖으로 돌아왔다. E로 다시 입장할 수 있습니다.","You returned. Press E near the gate to enter again."),12) end
end
enter=function()
    if active or building or not alive then return end
    local ok,err=xpcall(function()
        if not ready then buildMap() end
        if not alive then return end
        character=player.Character
        if not character or not character:FindFirstChildOfClass("Humanoid") then leave();return end
        for _,e in ipairs(enemies) do e.model:Destroy() end;table.clear(enemies)
        count=0;stamina=100;elapsed=0;stepTimer=0;aiTimer=0;position=gatePosition+Vector3.new(0,0,8);yaw=math.pi;pitch=0;state="explore"
        for _,s in ipairs(seals) do s.collected=false;s.part.Transparency=0;s.light.Enabled=true end
        beginStage(1)
        effects();active=true;cross.Visible=true;meter.Visible=true
        startKunai()
        sound("Wind",true,.45);sound("Drone",true,.24)
        heartbeat=sound("Heartbeat",true,0);chaseSound=sound("Chase",true,0);breathing=sound("Breath",true,0)
        caption.Text=tr(stageNames[1][1].."\n여관의 봉인을 찾아라",stageNames[1][2].."\nFind the inn's seal")
        veil.BackgroundTransparency=0;modalUntil=3
        Tween:Create(veil,TweenInfo.new(3),{BackgroundTransparency=1}):Play()
        if (Config.MissingAudio or 0)>0 then
            message(tr("오디오 로딩 실패: getcustomasset/writefile 지원이 필요합니다.","Audio unavailable: getcustomasset/writefile support required."),12)
        else message(tr("등불을 따라가세요. 달리면 그들이 듣습니다.","Follow the lanterns. They can hear you running."),9) end
    end,debug.traceback)
    if not ok and alive then building=false;leave(tr("시작 오류: ","Start error: ")..tostring(err));warn(err) end
end
local function interact()
    if not active then
        local h=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
        if h and portalCF and (h.Position-portalCF.Position).Magnitude<18 then task.spawn(enter) end
        return
    end
    if state=="caught" then return end
    for _,s in ipairs(seals) do
        if s==seals[stage] and not s.collected and (s.position-position).Magnitude<10 then
            s.collected=true;s.part.Transparency=1;s.light.Enabled=false;count=count+1
            sound("Bell",false,.35);message(s.story,7)
            if stage<5 then beginStage(stage+1) else for _,e in ipairs(enemies) do e.memory=6;e.target=position end end
            return
        end
    end
    if count==5 and state=="explore" and (position-bellPosition).Magnitude<13 then
        state="escape";sound("Bell",false,.65)
        message(tr("종이 울렸다. 처음 들어온 붉은 문으로 돌아가라!","The bell has rung. Return to the red gate!"),9)
        for _,e in ipairs(enemies) do e.memory=120;e.target=position end
    elseif state=="escape" and (position-gatePosition).Magnitude<14 then
        leave(tr("탈출 성공 — 문 너머에는 아무도 없었다.","ESCAPED — There was nobody beyond the gate."))
    end
end
local function catch(e)
    if state=="caught" then return end
    state="caught";modalUntil=elapsed+2.8;table.clear(keys)
    stopSounds();heartbeat=nil;chaseSound=nil;breathing=nil
    scare={enemy=e,started=elapsed,camera=workspace.CurrentCamera.CFrame}
    sound("Stinger",false,.7)
    caption.Text="";objective.Text="";prompt.Text="";cross.Visible=false
    veil.BackgroundTransparency=1
end
local function stepAI(dt,sprinting)
    for _,e in ipairs(enemies) do
        local delta=position-e.position;local distance=delta.Magnitude
        local sees=distance<(flashlight and 80+stage*4 or 45+stage*4) and clearLine(e.position,position)
        if sees or (sprinting and distance<130) then e.memory=8;e.target=position;e.mode="chase"
        else e.memory=math.max(0,e.memory-dt) end
        if e.memory<=0 then
            e.mode="patrol"
            if (e.position-e.target).Magnitude<8 then e.target=nodes[rng:NextInteger(1,#nodes)] end
        end
        local target=e.target
        if not clearLine(e.position,target) then
            e.planTime=e.planTime-dt
            if e.planTime<=0 then e.path=route(e.position,target);e.pathIndex=1;e.planTime=1.5 end
            target=e.path[e.pathIndex] or target
            if (target-e.position).Magnitude<7 then e.pathIndex=e.pathIndex+1;target=e.path[e.pathIndex] or e.target end
        end
        local toward=Vector3.new(target.X-e.position.X,0,target.Z-e.position.Z)
        if toward.Magnitude>1 then
            local speed=e.mode=="chase" and (state=="escape" and 21 or 14+stage) or 6+stage*.35
            e.position=slide(e.position,toward.Unit*math.min(toward.Magnitude,speed*dt))
            e.model:PivotTo(CFrame.lookAt(origin+Vector3.new(e.position.X,.2+math.sin(elapsed*2+e.index)*.2,e.position.Z),origin+Vector3.new(target.X,.2,target.Z)))
        end
        if distance<5 and clearLine(e.position,position) then catch(e);return end
    end
end
connect(Input.InputBegan,function(event,processed)
    if processed or Input:GetFocusedTextBox() then return end
    local k=event.KeyCode
    keys[k]=true
    if k==Enum.KeyCode.E then interact()
    elseif k==Enum.KeyCode.F and active then flashlight=not flashlight
    elseif k==Enum.KeyCode.Backspace then if not building then leave() end
    elseif k==Enum.KeyCode.M then
        volume=volume>=.99 and 0 or math.min(1,volume+.25)
        for s in pairs(sounds) do if s.Parent then s.Volume=(s:GetAttribute("KageGain") or 1)*volume end end
        message(tr("음량: ","Volume: ")..math.floor(volume*100).."%",3)
    elseif k==Enum.KeyCode.Q then
        high=not high;lantern.Shadows=high
        for _,o in ipairs(postEffects) do if o:IsA("DepthOfFieldEffect") then o.Enabled=high end end
        message(high and tr("그래픽: 높음","Graphics: High") or tr("그래픽: 성능 우선","Graphics: Performance"),3)
    elseif k==Enum.KeyCode.R and not active and not building then relocatePortal();message(tr("입구를 현재 위치 앞으로 옮겼습니다.","Entrance moved in front of you."),4)
    elseif k==Enum.KeyCode.Delete and not active and not building then env.KageVillage:Destroy() end
end)
connect(Input.InputEnded,function(event) keys[event.KeyCode]=nil end)
connect(Input.WindowFocusReleased,function() table.clear(keys) end)
connect(Input.InputChanged,function(event)
    if active and state~="caught" and not (Config.Development and Config.Preview) and event.UserInputType==Enum.UserInputType.MouseMovement then
        yaw=yaw-event.Delta.X*.0023;pitch=math.clamp(pitch-event.Delta.Y*.0023,-1.35,1.35)
    end
end)
connect(player.CharacterAdded,function(newCharacter) if active then leave(tr("캐릭터가 재생성되어 마을에서 나왔습니다.","Character respawned. You left the village.")) end;character=newCharacter end)
local renderName="OvitarKageVillageCamera"
Run:BindToRenderStep(renderName,Enum.RenderPriority.Camera.Value+10,function(rawDt)
    if not alive then return end
    local dt=math.min(rawDt,.05);elapsed=elapsed+dt
    if not active then
        if not building then
            local h=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
            prompt.Text=h and portalCF and (h.Position-portalCF.Position).Magnitude<18 and tr("[E] 안개 너머로 들어가기","[E] Enter the mist") or ""
        end
        return
    end
    if state=="caught" then
        if scare then
            local t=Config.Development and Config.PreviewScareTime or elapsed-scare.started
            local camera=workspace.CurrentCamera
            local intensity=math.max(0,1-t/2.4)
            camera.CFrame=scare.camera*CFrame.Angles(math.sin(t*57)*.025*intensity,math.sin(t*43)*.035*intensity,math.sin(t*67)*.025*intensity)
            camera.FieldOfView=58+math.sin(t*18)*3*intensity
            -- All heads are authored at y=7.2; face the mask toward the lens.
            local distance=math.max(1.6,5.8-t*15)
            local face=camera.CFrame*CFrame.new(0,0,-distance)
            scare.enemy.model:PivotTo(CFrame.lookAt(face.Position,camera.CFrame.Position)*CFrame.new(0,-7.2,0))
            lanternPart.CFrame=camera.CFrame;lantern.Enabled=true;lantern.Brightness=.8
            veil.BackgroundTransparency=t>1.9 and math.max(0,1-(t-1.9)/.6) or 1
            if t>2.15 then caption.Text=tr("그것이 당신의 이름을 기억했다.","It remembers your name.") end
        end
        if elapsed>modalUntil and not (Config.Development and Config.PreviewScareTime) then leave(tr("마을에 붙잡혔다. 문에서 다시 도전할 수 있습니다.","The village caught you. Try again at the gate.")) end
        return
    end
    if elapsed>modalUntil then caption.Text="" end
    if elapsed>messageUntil then note.Text="" end
    local x=(keys[Enum.KeyCode.D] and 1 or 0)-(keys[Enum.KeyCode.A] and 1 or 0)
    local z=(keys[Enum.KeyCode.S] and 1 or 0)-(keys[Enum.KeyCode.W] and 1 or 0)
    if Config.Development and Config.Preview then x=0;z=0 end
    local moving=x~=0 or z~=0
    local sprint=moving and keys[Enum.KeyCode.LeftShift] and stamina>1
    stamina=math.clamp(stamina+(sprint and -19 or 12)*dt,0,100)
    if moving then
        local v=CFrame.Angles(0,yaw,0):VectorToWorldSpace(Vector3.new(x,0,z).Unit)*(sprint and 25 or 13)*dt
        position=slide(position,v)
        stepTimer=stepTimer+dt
        if stepTimer>(sprint and .28 or .50) then
            stepTimer=0
            local foot=sound(sprint and (rng:NextNumber()<.5 and "Run1" or "Run2") or (rng:NextNumber()<.5 and "Step" or "Step2"),false,sprint and .42 or .28)
            if foot then foot.PlaybackSpeed=rng:NextNumber(.94,1.06) end
        end
    end
    local bob=moving and math.sin(elapsed*(sprint and 14 or 9))*(sprint and .10 or .045) or 0
    local camera=workspace.CurrentCamera
    camera.CameraType=Enum.CameraType.Scriptable
    camera.CFrame=CFrame.new(origin+position+Vector3.new(0,bob,0))*CFrame.Angles(0,yaw,0)*CFrame.Angles(pitch,0,0)
    camera.FieldOfView=camera.FieldOfView+((sprint and 78 or 70)-camera.FieldOfView)*math.min(1,dt*5)
    Input.MouseBehavior=Enum.MouseBehavior.LockCenter
    lanternPart.CFrame=camera.CFrame*CFrame.new(.65,-.45,-.3);lantern.Enabled=flashlight;lantern.Brightness=1.5
    meter.Size=UDim2.fromScale(.2*stamina/100,.003)
    objective.Text=state=="escape" and tr("마지막 밤 · 남쪽 붉은 문으로 탈출","FINAL NIGHT · Escape through the southern red gate") or count==5 and tr("다섯째 밤 · 신사의 종을 울려라","NIGHT V · Ring the shrine bell") or tr(stageNames[stage][1],stageNames[stage][2]).."  ·  "..seals[stage].name
    prompt.Text=""
    local targetSeal=seals[stage]
    if not targetSeal.collected and (targetSeal.position-position).Magnitude<10 then prompt.Text=tr("[E] 봉인 회수 — ","[E] Take seal — ")..targetSeal.name end
    if count==5 and (position-bellPosition).Magnitude<13 and state=="explore" then prompt.Text=tr("[E] 종 울리기","[E] Ring the bell") end
    if state=="escape" and (position-gatePosition).Magnitude<14 then prompt.Text=tr("[E] 탈출","[E] Escape") end
    if elapsed>nextWhisper then
        nextWhisper=elapsed+rng:NextNumber(12,24)
        local e=enemies[rng:NextInteger(1,#enemies)]
        if e and (e.position-position).Magnitude<150 then sound("Whisper",false,.55,e.voice) end
    end
    aiTimer=aiTimer+dt
    if aiTimer>=.1 then if not Config.Development or not Config.Preview then stepAI(aiTimer,sprint) end;aiTimer=0 end
    local enemy=enemies[1];local threat=enemy and enemy.mode=="chase" and math.clamp(1-(enemy.position-position).Magnitude/110,0,1) or 0
    if heartbeat then heartbeat.Volume=volume*threat*.34;heartbeat.PlaybackSpeed=1+threat*.35 end
    if chaseSound then chaseSound.Volume=volume*threat*.32 end
    if breathing then breathing.Volume=volume*((sprint and .20 or 0)+(1-stamina/100)*.18) end
    for _,l in ipairs(lights) do
        l.light.Enabled=(l.position-position).Magnitude<(high and 140 or 75)
        if l.light.Enabled then l.light.Brightness=l.brightness+math.sin(elapsed*5+l.phase)*.07 end
    end
end)
local api={}
function api:Destroy()
    if not alive then return end
    alive=false;active=false
    Run:UnbindFromRenderStep(renderName)
    for _,c in ipairs(connections) do c:Disconnect() end
    stopSounds();restore();root:Destroy();gui:Destroy()
    for _,entry in pairs(meshCache) do entry.part:Destroy() end;table.clear(meshCache)
    for _,editable in ipairs(editableMeshes) do editable:Destroy() end;table.clear(editableMeshes)
    if env.KageVillage==self then env.KageVillage=nil end
end
function api:MoveEntrance() relocatePortal() end
function api:Leave() leave() end
function api:Enter() task.spawn(enter) end
function api:SetVolume(v) volume=math.clamp(v,0,1);for s in pairs(sounds) do if s.Parent then s.Volume=(s:GetAttribute("KageGain") or 1)*volume end end end
function api:SetLanguage(language) Config.Language=language=="en" and "en" or "ko" end
function api:GetStatus() return {active=active,building=building,ready=ready,stage=stage,state=state,monsters=#enemies,seals=count,kunai=kunaiStatus,meshes=(function() local n=0;for _ in pairs(meshCache) do n=n+1 end;return n end)()} end
if Config.Development then
    function api:PreviewStage(index) assert(active and index>=1 and index<=5);Config.Preview=true;beginStage(index) end
    function api:PreviewCamera(pos,angle) position=pos;yaw=angle or math.pi;pitch=0 end
    function api:PreviewCatch(holdTime) assert(active and enemies[1]);Config.PreviewScareTime=holdTime;catch(enemies[1]) end
    function api:PreviewInteract() interact() end
end
api.Config=Config
env.KageVillage=api
message(tr("붉은 문에 접근해 E · R로 입구 위치 변경 · Delete로 제거","Approach the red gate and press E · R relocates entrance · Delete unloads"),20)
return api
