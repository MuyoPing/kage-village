"""Original 44.1 kHz stereo foley and cinematic horror sound design.
No third-party recordings. Reproducible layered synthesis with short room tails.
"""
from pathlib import Path
import numpy as np
import wave, json, hashlib
BASE=Path(__file__).resolve().parent
SR=44100
rng=np.random.default_rng(140026)
def noise(n,low=30,high=15000,slope=0):
    f=np.fft.rfftfreq(n,1/SR);s=np.fft.rfft(rng.normal(0,1,n))
    shape=np.minimum(1,(f/max(low,1))**3)*np.minimum(1,(high/np.maximum(f,1))**4)
    shape*=np.maximum(f,40)**(-slope)
    y=np.fft.irfft(s*shape,n);return y/(np.std(y)+1e-8)
def tail(y,delays=(.027,.061,.097,.149),gains=(.20,.14,.09,.05)):
    out=y.copy()
    for d,g in zip(delays,gains):
        k=int(d*SR)
        if k<len(y):out[k:]+=y[:-k]*g
    return out
def write(name,y,loop=False,width=.12):
    y=np.tanh(y*1.2)
    n=len(y);fade=np.minimum(np.arange(n)/(SR*.008),1)*np.minimum(np.arange(n)[::-1]/(SR*.04),1)
    if not loop:y=y*fade
    else:
        # Gentle loop boundaries avoid clicks in Roblox's sample looping.
        y=y*np.minimum(np.arange(n)/(SR*.06),1)*np.minimum(np.arange(n)[::-1]/(SR*.06),1)
    right=y*(1-width)+np.roll(y,int(SR*.009))*width
    stereo=np.column_stack([y,right]);stereo*=.78/max(.78,np.max(np.abs(stereo)))
    p=BASE/'assets/audio'/f'{name}.wav';p.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(p),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes((stereo*32767).astype('<i2').tobytes())
    print(name,round(n/SR,2),'s',round(float(np.max(np.abs(stereo))),3),'peak')
def timeline(duration):return np.arange(int(duration*SR))/SR

for name,sprint,seed in [('Step',False,0),('Step2',False,1),('Run1',True,2),('Run2',True,3)]:
    t=timeline(.56);n=len(t)
    heel=np.sin(2*np.pi*(72*t-32*t*t))*np.exp(-t*(30 if sprint else 42))*(.52 if sprint else .32)
    contact=noise(n,180,4200)*np.exp(-t*55)*.16
    grit=noise(n,1100,10000)*np.exp(-t*14)*.035
    sole=noise(n,200,1800)*np.exp(-((t-.055)/.023)**2)*.10
    grains=np.zeros(n)
    for k in range(12):
        at=rng.uniform(.02,.18);grains+=noise(n,1600,7000)*np.exp(-np.maximum(t-at,0)*120)*(t>=at)*rng.uniform(.004,.015)
    write(name,tail(heel+contact+grit+sole+grains),width=.05)

t=timeline(12);n=len(t)
write('Wind',noise(n,90,2800,.7)*(.035+.015*np.sin(2*np.pi*t/6))+.012*noise(n,1800,6500)*(.5+.5*np.sin(t*.7)),True,.4)
write('Drone',sum(np.sin(2*np.pi*f*t+.9*np.sin(t*.4))*a for f,a in [(41,.065),(61.7,.025),(82.3,.024),(123.6,.012)])+.012*noise(n,100,500,.5),True,.3)
t=timeline(4.8);n=len(t)
bell=np.zeros(n)
for i,(f,decay) in enumerate([(168,.5),(335,.7),(456,.9),(677,1.1),(936,1.6),(1271,2.1),(1773,2.8),(2411,3.8)]):
    bell+=.26/(1+i*.5)*np.sin(2*np.pi*f*t+.2*np.sin(2*np.pi*2.7*t))*np.exp(-t*decay)
bell+=noise(n,400,6000)*np.exp(-t*65)*.15
write('Bell',tail(bell,(.11,.24,.41,.68),(.24,.18,.12,.08)),width=.28)
t=timeline(3.6);n=len(t)
breathy=noise(n,250,4500,.3)*(.16*np.exp(-((t-1.1)/.5)**2)+.12*np.exp(-((t-2.4)/.7)**2))
write('Whisper',tail(breathy*(.7+.3*np.sin(2*np.pi*27*t))),width=.45)

# Catch: short inhalation, layered impact, distorted vocal resonances, decay.
t=timeline(3.1);n=len(t)
attack=np.minimum(t/.022,1)*np.exp(-t*2.5)
f0=142+63*np.exp(-t*3)+18*np.sin(t*29)+5*noise(n,0,20)
phase=np.cumsum(f0)/SR*2*np.pi
voice=np.zeros(n)
for h in range(1,26):
    f=h*180
    formant=sum(np.exp(-((f-c)/bw)**2)*gain for c,bw,gain in [(730,280,1),(1460,400,.6),(2600,650,.3)])
    voice+=np.sin(phase*h+rng.uniform(0,1))*(.025+formant*.075)/np.sqrt(h)
voice=np.tanh(voice*2)*attack*(.75+.25*np.sin(t*51))
sub=np.sin(2*np.pi*(52*t+15*(1-np.exp(-t*12))))*np.exp(-t*7)*.55
impact=noise(n,80,3500,.3)*np.exp(-t*25)*.3
scrape=noise(n,650,5500)*np.exp(-t*3.5)*(.10+.08*np.sin(t*79))
write('Stinger',tail(voice+sub+impact+scrape,(.038,.083,.17,.31),(.25,.21,.15,.08)),width=.35)

t=timeline(4);n=len(t);beat=np.zeros(n)
for at in np.arange(.1,4,.8):
    for offset,g in [(0,.4),(.17,.27)]:
        q=t-at-offset;beat+=np.sin(2*np.pi*49*q)*np.exp(-np.maximum(q,0)*26)*(q>=0)*g
write('Heartbeat',beat,True,.06)
t=timeline(8);n=len(t)
pulse=(.5+.5*np.sin(2*np.pi*2.5*t))**5
chase=(np.sin(2*np.pi*56*t)*.15+noise(n,100,700,.5)*.035)*pulse
chase+=noise(n,1100,5000)*.018*(.5+.5*np.sin(t*31))
write('Chase',tail(chase),True,.25)
t=timeline(4);n=len(t)
env=sum(np.exp(-((t-c)/w)**2)*a for c,w,a in [(.7,.28,.09),(1.55,.38,.12),(2.6,.27,.1),(3.4,.38,.12)])
write('Breath',noise(n,180,3000,.2)*env,True,.06)
t=timeline(3.6);n=len(t)
sw=np.sin(np.minimum(t/1.3,1)*np.pi/2)*np.exp(-np.maximum(t-1.3,0)*3)
write('Transition',tail(noise(n,100,2600,.6)*sw*.12+np.sin(2*np.pi*61*t)*sw*.10),width=.4)

manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
for p in sorted((BASE/'assets').rglob('*')):
    if p.is_file():manifest['files'][p.relative_to(BASE).as_posix()]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(BASE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
