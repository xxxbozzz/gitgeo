import { getData } from './http'
import type { SystemStatusPayload } from '../types/system'

export function fetchSystemStatus() {
  return getData<SystemStatusPayload>('/system/status')
}
