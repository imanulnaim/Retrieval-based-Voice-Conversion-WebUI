# Builds the 10s soundtrack: humming nasheed (Hijaz on D, voice only) + Malay VO, with ducking and reverb.
# Usage: python3 audio.py <vo_dir> out.wav   (vo_dir holds l1.wav l2.wav l3.wav from tts.py)
import numpy as np, soundfile as sf, sys
from scipy.signal import fftconvolve, butter, sosfilt, resample_poly
SR=44100; DUR=10.0; N=int(SR*DUR); t=np.arange(N)/SR
rng=np.random.default_rng(11)

def bp(x,lo,hi,o=2): return sosfilt(butter(o,[lo,hi],'band',fs=SR,output='sos'),x)
def lpf(x,f,o=2): return sosfilt(butter(o,f,'low',fs=SR,output='sos'),x)
def hpf(x,f,o=2): return sosfilt(butter(o,f,'high',fs=SR,output='sos'),x)

def hum(f0,amp,bright=1.0):
    """Voiced 'mmm' hum: band-limited glottal pulse train through nasal formants."""
    ph=np.cumsum(f0)/SR; src=np.zeros(N)
    for k in range(1,26):
        src+=np.sin(2*np.pi*k*ph)/(k**1.25)*(f0*k<9000)
    src+=rng.standard_normal(N)*0.012*bright                     # breath
    v=bp(src,180,420)*1.0+bp(src,900,1250)*0.18*bright+bp(src,2100,2700)*0.06*bright+lpf(src,300)*0.6
    return v*amp

def contour(notes,start,beat,base_shift=0):
    """Piecewise pitch with portamento + delayed vibrato; returns f0 and amplitude envelopes."""
    f=np.full(N,np.nan); a=np.zeros(N); tt=start
    for m,d in notes:
        i,j=int(tt*SR),int((tt+d*beat)*SR); j=min(j,N)
        f[i:j]=440*2**((m+base_shift-69)/12)
        n=j-i; x=np.arange(n)/SR
        env=np.minimum(1,x/0.09)*np.minimum(1,(n-np.arange(n))/SR/0.07)*0.25+0.75
        a[i:j]=env; tt+=d*beat
    end=tt
    idx=np.where(~np.isnan(f))[0]; f[:idx[0]]=f[idx[0]]; f[idx[-1]:]=f[idx[-1]]
    f=np.exp(lpf(np.log(f)-np.log(f[0]),14,1)+np.log(f[0]))   # glide
    # vibrato grows within sustained notes
    vib=1+0.011*np.sin(2*np.pi*5.2*t)*np.clip((t-start)/1.5,0,1)
    a=lpf(a,20,1)
    ramp=np.clip((t-start)/0.6,0,1)*np.clip((end+1.2-t)/1.2,0,1)
    return f*vib,a*ramp,end

beat=0.6
mel=[(62,1),(63,.5),(66,1.5),(67,1),(66,.5),(63,.5),(62,2),
     (69,1),(67,.5),(66,.5),(67,1),(66,.5),(63,.5),(62,3)]
f0,amp,end=contour(mel,0.25,beat)
lead=hum(f0,amp)
# harmony voice a fourth/fifth below following slowly (thirds avoided in Hijaz), and a deep drone
f1,a1,_=contour([(m-5,d) for m,d in mel],0.25,beat)
harm=hum(f1*1.003,a1*0.35,0.7)
drone_f=np.full(N,440*2**((38-69)/12))*(1+0.004*np.sin(2*np.pi*.3*t))
dr_amp=np.clip(t/1.2,0,1)*np.clip((DUR-t)/1.0,0,1)
drone=hum(drone_f,dr_amp*0.55,0.5)+hum(drone_f*1.5,dr_amp*0.18,0.5)
music=lead+harm+drone

# reverb: stereo exponentially decaying noise IR
def ir(sec,seed):
    r=np.random.default_rng(seed); n=int(sec*SR); x=r.standard_normal(n)*np.exp(-np.arange(n)/SR/0.55)
    return lpf(x,5000)/np.sqrt(np.sum(x**2))
wetL=fftconvolve(music,ir(2.6,1))[:N]; wetR=fftconvolve(music,ir(2.6,2))[:N]
mL=music*0.55+wetL*1.1; mR=music*0.55+wetR*1.1
M=np.stack([mL,mR],1); M/=np.abs(M).max()

# VO
vo=np.zeros(N); placements=[('l1.wav',0.3),('l2.wav',1.65),('l3.wav',5.6)]
for fn,st in placements:
    x,sr=sf.read(f'{sys.argv[1]}/{fn}'); x=resample_poly(x,SR,sr)
    nz=np.where(np.abs(x)>0.02*np.abs(x).max())[0]; x=x[max(0,nz[0]-400):nz[-1]+2000]
    print(fn,'starts',st,'len %.2fs'%(len(x)/SR),'ends %.2f'%(st+len(x)/SR))
    i=int(st*SR); vo[i:i+len(x)]+=x[:N-i]
vo=hpf(vo,90); vo=vo+0.25*lpf(vo,350)          # warmth
vo/=np.abs(vo).max()
voW=fftconvolve(vo,ir(1.2,3))[:N]*0.35
duck=lpf((np.abs(vo)>0.02).astype(float),3,1); duck=1-0.55*np.clip(duck*3,0,1)
out=M*0.42*duck[:,None]+np.stack([vo+voW,vo+voW*.9],1)*0.8
out*=np.clip((DUR-t)/0.35,0,1)[:,None]
out/=np.abs(out).max()/0.95
sf.write(sys.argv[2],out,SR)
