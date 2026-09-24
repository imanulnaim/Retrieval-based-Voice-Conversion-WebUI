# Synthesises a 60s tech-promo soundtrack (124 BPM) with whooshes on scene cuts.
import numpy as np, wave, sys
SR=44100; DUR=60.5; BPM=124; beat=60/BPM
N=int(SR*DUR); L=np.zeros(N); R=np.zeros(N)
t=np.arange(N)/SR
rng=np.random.default_rng(3)
def add(sig,start,pan=0.0,g=1.0):
    i=int(start*SR)
    if i>=N: return
    j=min(N,i+len(sig)); s=sig[:j-i]*g
    L[i:j]+=s*(1-pan)*0.5*2**.5; R[i:j]+=s*(1+pan)*0.5*2**.5
def env(n,a,d):
    e=np.ones(n); ai=int(a*SR); e[:ai]=np.linspace(0,1,ai) if ai else 1
    return e*np.exp(-np.arange(n)/SR/d)
def kick():
    n=int(.35*SR); tt=np.arange(n)/SR; f=50+90*np.exp(-tt*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*9)
def hat(o=False):
    n=int((.18 if o else .05)*SR); return rng.standard_normal(n)*np.exp(-np.arange(n)/SR/(0.05 if o else .012))*np.linspace(1,1,n)
def clap():
    n=int(.2*SR); x=rng.standard_normal(n)*np.exp(-np.arange(n)/SR/.05); return np.convolve(x,[1,-.9])[:n]
def saw(f,n): tt=np.arange(n)/SR; return 2*((tt*f)%1)-1
def lp(x,a): # one-pole lowpass
    y=np.empty_like(x); acc=0; a=np.broadcast_to(a,x.shape)
    for i in range(len(x)): acc+=a[i]*(x[i]-acc); y[i]=acc
    return y
midi=lambda m:440*2**((m-69)/12)
prog=[(57,[57,60,64]),(53,[53,57,60]),(48,[48,52,55]),(55,[55,59,62])]   # Am F C G
bar=4*beat; nbars=int(DUR/bar)+1
# pads
for b in range(nbars):
    root,ch=prog[b%4]; n=int(bar*SR)
    pad=sum(saw(midi(m+12),n)+saw(midi(m+12)*1.004,n) for m in ch)/6
    pad=lp(pad,0.03)*np.minimum(1,np.arange(n)/SR/.3)*np.minimum(1,(n-np.arange(n))/SR/.2)
    add(pad,b*bar,g=.22)
    # bass (8ths) from bar 3 on
    if b*bar>=2.6:
        for k in range(8):
            m=int(beat/2*SR); x=lp(saw(midi(root-12),m),.08)*env(m,.005,.18); add(x,b*bar+k*beat/2,g=.35)
    # arp
    if b*bar>=6:
        notes=[ch[0]+24,ch[1]+24,ch[2]+24,ch[1]+24]
        for k in range(16):
            m=int(beat/4*SR*1.5); f=midi(notes[k%4]); tt=np.arange(m)/SR
            x=(np.sign(np.sin(2*np.pi*f*tt))*.5+np.sin(2*np.pi*f*2*tt)*.3)*env(m,.002,.07)
            add(x,b*bar+k*beat/4,pan=.4*np.sin(k),g=.07)
# drums: intro sparse (0-2.6), full after
nb=int(DUR/beat)
for k in range(nb):
    tb=k*beat
    if tb>=59.2: break
    if tb<2.6:
        if k%4==0: add(kick(),tb,g=.5)
        continue
    add(kick(),tb,g=.9)
    add(hat(),tb+beat/2,pan=.3,g=.18); add(hat(),tb+beat/4*3,pan=-.3,g=.08)
    if k%2==1: add(clap(),tb,g=.3)
# whoosh + impact at cuts
for c in [2.6,6.2,14.2,20.2,38.2,50.1]:
    n=int(1.2*SR); x=rng.standard_normal(n); tt=np.arange(n)/SR
    sw=np.minimum(tt/1.0,1)**2; w=lp(x,0.02+0.25*sw)*sw*np.exp(-np.maximum(tt-1.0,0)*25)
    add(w,c-1.0,g=.9)
    m=int(.6*SR); tt=np.arange(m)/SR; add(np.sin(2*np.pi*(40+60*np.exp(-tt*20))*tt)*np.exp(-tt*5),c,g=.6)
# riser into CTA + final hit
fade=np.minimum(1,np.maximum(0,(60.2-t)/1.0))
mix=np.stack([L,R],1)*fade[:,None]
mix/=np.abs(mix).max()/0.89
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes())
