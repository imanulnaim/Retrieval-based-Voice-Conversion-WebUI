import sherpa_onnx, soundfile as sf, sys
d='vits-piper-id_ID-news_tts-medium/'
cfg=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=d+'id_ID-news_tts-medium.onnx',tokens=d+'tokens.txt',data_dir=d+'espeak-ng-data',length_scale=float(sys.argv[3]) if len(sys.argv)>3 else 1.0),num_threads=4))
tts=sherpa_onnx.OfflineTts(cfg)
a=tts.generate(sys.argv[1],sid=int(sys.argv[2]),speed=1.0)
sf.write(sys.argv[4] if len(sys.argv)>4 else f'vo_{sys.argv[2]}.wav',a.samples,a.sample_rate); print(len(a.samples)/a.sample_rate, a.sample_rate)
