"""Original implicit-surface creatures: joined anatomy, carved faces, no shared mask."""
import numpy as np
from skimage.measure import marching_cubes
import fast_simplification

def build_creatures(Scene, Mesh, cf):
    result=[]
    names=['The Uninvited','The Starved Listener','The Shrine Husk','The Drowned Mother','The Antlered Mourner']
    palettes=[(158,150,133),(93,99,91),(119,86,70),(116,136,125),(69,75,71)]
    for kind in range(5):
        scene=Scene(names[kind]); step=.065
        lo=np.array([-6.,-.3,-3.8]); hi=np.array([6.,12.,4.2])
        axes=[np.arange(lo[i],hi[i],step,dtype=np.float32) for i in range(3)]
        X,Y,Z=np.meshgrid(*axes,indexing='ij'); field=np.full(X.shape,100,dtype=np.float32)
        def merge(d,k=.18):
            nonlocal field
            h=np.clip(.5+.5*(d-field)/k,0,1);field=d*(1-h)+field*h-k*h*(1-h)
        def ball(p,r,subtract=False):
            nonlocal field
            d=(np.sqrt(((X-p[0])/r[0])**2+((Y-p[1])/r[1])**2+((Z-p[2])/r[2])**2)-1)*min(r)
            if subtract: field=np.maximum(field,-d)
            else:merge(d)
        def bone(a,b,r1,r2):
            a=np.array(a);b=np.array(b);v=b-a
            t=np.clip(((X-a[0])*v[0]+(Y-a[1])*v[1]+(Z-a[2])*v[2])/np.dot(v,v),0,1)
            d=np.sqrt((X-a[0]-v[0]*t)**2+(Y-a[1]-v[1]*t)**2+(Z-a[2]-v[2]*t)**2)-(r1+(r2-r1)*t)
            merge(d,.14)
        h=[7.3,9.1,7.6,4.8,8.5][kind];head=(0,h,-.28)
        if kind==3:
            ball((0,3.0,.9),(1.0,.75,1.7));bone((0,3.2,0),head,.45,.35)
            for s in [-1,1]:
                for j in range(2):
                    a=(s*.7,3.3,.2+j*1.4);b=(s*(2.4+j*.3),3.7-j,.1+j*1.7);c=(s*(3.3+j*.3),.28,-1.2+j*3)
                    bone(a,b,.28,.17);bone(b,c,.17,.09)
                    for f in range(3):bone(c,(c[0]+s*(.3+f*.16),.13,c[2]-.6+f*.2),.07,.025)
        else:
            torso=h-2.1
            ball((0,torso,0),([.92,.72,1.28,.9,1.0][kind],1.05,.52))
            ball((0,torso-1.3,.08),(.57,.75,.44))
            bone((0,torso+.6,0),head,.31,.25)
            for s in [-1,1]:
                hip=(s*.42,torso-1.6,.08);knee=(s*.62,1.65,.35);ankle=(s*.75,.3,-.1)
                bone(hip,knee,.30,.19);bone(knee,ankle,.18,.095);ball((s*.75,.22,-.38),(.19,.18,.48))
                shoulder=(s*.78,torso+.4,0);elbow=(s*(1.5 if kind!=1 else 1.85),torso-1.1,.2)
                wrist=(s*(1.8 if kind!=1 else 2.2),.9 if kind==1 else torso-2.8,-.25)
                bone(shoulder,elbow,.3,.16);bone(elbow,wrist,.17,.10)
                ball(wrist,(.2,.3,.15))
                for f in range(4):
                    a=(wrist[0]+(f-1.5)*.115,wrist[1]-.12,wrist[2]);b=(a[0]+s*.11,a[1]-.48-abs(f-1.5)*.08,a[2]-.13)
                    bone(a,b,.055,.032);bone(b,(b[0]-s*.08,b[1]-.24,b[2]-.18),.035,.017)
        # Anatomical skull, continuous jaw and neck. Open cavities cut through skin.
        ball(head,([.67,.51,.75,.78,.62][kind],[.91,1.13,.9,.85,1.05][kind],.59))
        ball((0,h-.49,-.34),(.43,.59,.47))
        ball((0,h+.03,-.81),(.14,.32,.19))
        for s in [-1,1]:
            ball((s*.44,h-.12,-.55),(.28,.33,.22))
            ball((s*.27,h+.22,-.77),(.24,.235,.31),True)
        mouthWidth=[.26,.18,.38,.43,.21][kind];mouthHeight=[.4,.64,.3,.35,.63][kind]
        ball((0,h-.4,-.77),(mouthWidth,mouthHeight,.41),True)
        # Fine asymmetry and surface ridges are sculpted, never a photograph panel.
        field+=.009*np.sin(X*31+Y*11)*np.sin(Z*28-Y*7)+.008*np.sin(Y*49+X*5)
        verts,faces,normals,_=marching_cubes(field,0,spacing=(step,step,step),allow_degenerate=False)
        verts+=lo
        if len(faces)>18000:verts,faces=fast_simplification.simplify(verts,faces,target_count=18000)
        body=Mesh();body.vertices=np.round(verts,4).tolist();body.faces=(faces+1).tolist();body.smooth=set(range(1,len(verts)+1))
        centers=verts[faces].mean(axis=1);base=np.array(palettes[kind])
        for x,y,z in centers:
            mottling=.84+.10*np.sin(x*15+y*9)*np.sin(z*17)+.07*np.sin(y*27+x*3)
            body.colors.append(np.clip(base*mottling,0,255).astype(int).tolist())
        scene.part('Voice anchor',[.1,.1,.1],cf(0,h,0),alpha=1,collide=False)
        key=f'creature{kind}_continuous_anatomy';scene.register(key,body);scene.inst(key,cf())
        detail=Mesh();teeth=Mesh();shadow=Mesh()
        shadow.ellipsoid((0,h-.4,-.42),(mouthWidth*1.6,mouthHeight*1.7,.22),(13,17,16),20,14)
        for s in [-1,1]:
            shadow.ellipsoid((s*.27,h+.22,-.49),(.34,.32,.16),(12,16,15),16,10)
            if kind in [0,2,4]:teeth.ellipsoid((s*.27,h+.22,-.59),(.065,.07,.06),(172,167,133),10,6)
        for i in range(9):
            a=i/8*np.pi;x=np.cos(a)*mouthWidth*.79;y=np.sin(a)*mouthHeight*.82
            for s in [-1,1]:teeth.beam((x,h-.4+s*y,-.72),(x*.85,h-.4+s*(y-.13),-.76),.038,(180,174,143),7,.012)
        if kind==0:
            # Thin torn shroud follows the ribcage; strands taper rather than cylinders.
            for j in range(26):
                a=j*np.pi*2/26
                if np.sin(a)<-.4:continue
                detail.loft([(np.cos(a)*.72,h+.5,np.sin(a)*.62,.09,.07),(np.cos(a)*.83,h-1,np.sin(a)*.75,.12,.08),(np.cos(a),h-3.5-(j%3)*.3,np.sin(a)*.8,.005,.005)],(29,32,30),6)
        elif kind==1:
            for s in [-1,1]:
                for j in range(7):
                    y=h-1.5-j*.19
                    detail.beam((s*.12,y,-.52),(s*.61,y-.18,-.38),.045,(133,135,116),7,.025)
            for s in [-1,1]:detail.ellipsoid((s*.54,h+.05,.03),(.17,.85,.43),(102,107,91),16,12)
        elif kind==2:
            for s in [-1,1]:
                detail.loft([(s*.45,h+.65,-.02,.2,.2),(s*.7,h+1.1,0,.16,.16),(s*.62,h+1.8,.25,.002,.002)],(70,62,49),16)
            for j in range(7):detail.beam((-.95,h-1.5-j*.16,-.52),(.95,h-1.5-j*.16,-.52),.07,(56,48,36),8)
        elif kind==3:
            for j in range(22):
                a=j*np.pi*2/22
                if np.sin(a)<-.35:continue
                detail.loft([(np.cos(a)*.66,h+.5,np.sin(a)*.6,.07,.06),(np.cos(a)*.9,h-.9,np.sin(a)*.8,.09,.06),(np.cos(a)*1.2,1.0,np.sin(a),.003,.003)],(25,39,33),6)
        else:
            for s in [-1,1]:
                prev=(s*.4,h+.7,0)
                for j in range(4):
                    end=(s*(.7+j*.36),h+1+j*.37,.15+j*.13)
                    detail.beam(prev,end,.15-j*.03,(102,103,86),10,.11-j*.025)
                    detail.beam(end,(end[0]-s*.15,end[1]+.65,end[2]-.35),.08,(102,103,86),8,.005);prev=end
        for label,m,mat in [('details',detail,'SmoothPlastic'),('teeth',teeth,'SmoothPlastic'),('cavities',shadow,'SmoothPlastic')]:
            if m.faces:
                key=f'creature{kind}_{label}';scene.register(key,m,mat);scene.inst(key,cf())
        data=scene.data();data['headHeight']=h;result.append(data)
    return result
