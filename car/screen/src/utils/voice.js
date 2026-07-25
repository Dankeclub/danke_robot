import presets from '../data/chat-presets.json'

let recognition = null
let synth = window.speechSynthesis
let speaking = false

export function initRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) return null
  const rec = new SpeechRecognition()
  rec.lang = 'zh-CN'
  rec.interimResults = true
  rec.continuous = true
  return rec
}

export function startListening({ onResult, onEnd, onError }) {
  if (!recognition) {
    recognition = initRecognition()
  }
  if (!recognition) return false

  recognition.onresult = (event) => {
    let transcript = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript
    }
    onResult(transcript)
  }

  recognition.onend = () => {
    onEnd()
  }

  recognition.onerror = (e) => {
    onError(e)
  }

  recognition.start()
  return true
}

export function stopListening() {
  if (recognition) {
    recognition.stop()
  }
}

export function matchReply(text) {
  const lower = text.toLowerCase()
  for (const item of presets) {
    for (const kw of item.keywords) {
      if (lower.includes(kw)) {
        return item.reply
      }
    }
  }
  return '哈哈，有意思！虽然我没太听懂，但跟你聊天好开心呀~ 要不要再说一遍？'
}

export function speak(text, { onStart, onEnd } = {}) {
  if (!synth) return

  synth.cancel()
  speaking = true

  const utter = new SpeechSynthesisUtterance(text)
  utter.lang = 'zh-CN'
  utter.rate = 0.95
  utter.pitch = 1.15

  const voices = synth.getVoices()
  const zhVoice = voices.find(v => v.lang.startsWith('zh-CN') || v.lang.startsWith('zh-TW'))
  if (zhVoice) utter.voice = zhVoice

  utter.onstart = () => {
    speaking = true
    onStart && onStart()
  }
  utter.onend = () => {
    speaking = false
    onEnd && onEnd()
  }
  utter.onerror = () => {
    speaking = false
    onEnd && onEnd()
  }

  synth.speak(utter)
}

export function stopSpeaking() {
  if (synth) {
    synth.cancel()
    speaking = false
  }
}

export function isSpeaking() {
  return speaking
}
