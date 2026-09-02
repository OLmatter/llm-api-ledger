import DefaultTheme from 'vitepress/theme'
import LeaderBoard from '../components/LeaderBoard.vue'
import IntelBoard from '../components/IntelBoard.vue'

import './override.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('LeaderBoard', LeaderBoard)
    app.component('IntelBoard', IntelBoard)
  },
}
