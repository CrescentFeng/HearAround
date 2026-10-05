class HearAroundPcmCapture extends AudioWorkletProcessor {
  process(inputs) {
    const channels = inputs[0];
    if (!channels || !channels.length || !channels[0].length) return true;
    const mono = new Float32Array(channels[0].length);
    for (const channel of channels) {
      for (let index = 0; index < mono.length; index += 1) {
        mono[index] += channel[index] / channels.length;
      }
    }
    this.port.postMessage({ samples: mono }, [mono.buffer]);
    return true;
  }
}

registerProcessor('hearound-pcm-capture', HearAroundPcmCapture);
