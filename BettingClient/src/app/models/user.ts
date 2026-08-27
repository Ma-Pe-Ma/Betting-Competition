interface User {
  role: number | null
  hash: string | null 
  username: string | null
  messages: Alert[] | null
  timezone: string | null
  maintenance: boolean | null
}