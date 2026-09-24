# 15s tense editorial sound bed: sub pulse, clock ticks, whoosh + hit on every cut.
import numpy as np, wave, sys
SR=44100; DUR=15.1; N=int(SR*DUR); t=np.arange(N)/SR
rng=np.random.default_rng(5); L=np.zeros(N); R=np.zeros(N)
def add(x,st,g=1,pan=0):
    i=int(st*SR)
    if i>=N: return
    j=min(N,i+len(x)); x=x[:j-i]*g; L[i:j]+=x*(1-pan); R[i:j]+=x*(1+pan)
def lp(x,a):
    y=np.empty_like(x); acc=0; a=np.broadcast_to(a,x.shape)
    for i in range(len(x)): acc+=a[i]*(x[i]-acc); y[i]=acc
    return y
# drone (D minor-ish) with slow swell
dr=sum(np.sin(2*np.pi*f*t+ph)*g for f,g,ph in [(36.7,.5,0),(73.4,.35,1),(110,.18,2),(146.8,.08,3),(174.6,.06,1.5)])
dr*=np.minimum(1,t/1.0)*(0.6+0.4*np.sin(2*np.pi*t/7.5-1.5)**2)
add(dr,0,.5)
# heartbeat-ish sub pulse at 100 bpm
beat=0.6
for k in range(int(DUR/beat)):
    tb=k*beat
    if tb>14.2: break
    n=int(.3*SR); tt=np.arange(n)/SR; x=np.sin(2*np.pi*(45+70*np.exp(-tt*35))*tt)*np.exp(-tt*10)
    add(x,tb,.8); 
    if k%2==0: add(x*.5,tb+.18,.5)
    # clock tick
    m=int(.03*SR); tick=rng.standard_normal(m)*np.exp(-np.arange(m)/SR/.004); add(np.diff(tick,prepend=0),tb+beat/2,.35,pan=(-.4 if k%2 else .4))
# whoosh + impact at cuts
for c in [0.84,2.95,6.25,7.98,9.71,11.45,13.2]:
    n=int(.5*SR); x=rng.standard_normal(n); tt=np.arange(n)/SR; sw=(tt/.5)**2
    add(lp(x,.02+.3*sw)*sw,c-.5,.9)
    m=int(1.2*SR); tt=np.arange(m)/SR
    hit=np.sin(2*np.pi*(38+80*np.exp(-tt*25))*tt)*np.exp(-tt*3.5)+lp(rng.standard_normal(m),.15)*np.exp(-tt*12)*.6
    add(hit,c,1.0)
# typewriter clicks during headline words
for k in range(4): add(np.diff(rng.standard_normal(int(.02*SR))*np.exp(-np.arange(int(.02*SR))/SR/.003),prepend=0),.2+k*.16,.5)
mix=np.stack([L,R],1)*np.minimum(1,(DUR-t)/.4)[:,None]
mix/=np.abs(mix).max()/0.9
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes())
