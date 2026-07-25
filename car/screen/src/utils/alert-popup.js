import { reactive } from 'vue'

const state = reactive({
  visible: false,
  type: 'attention',
  message: '',
})

export function useAlertPopup() {
  function show({ type = 'attention', message }) {
    state.type = type
    state.message = message
    state.visible = true
  }

  function dismiss() {
    state.visible = false
  }

  return { state, show, dismiss }
}
