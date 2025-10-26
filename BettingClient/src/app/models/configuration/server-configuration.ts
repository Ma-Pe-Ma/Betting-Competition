interface Language {
    key: string
    tr: string[]
}

interface ServerConfiguration {
    noftificationType?: string
    languages?: Language[]
    pushKey?: string
}