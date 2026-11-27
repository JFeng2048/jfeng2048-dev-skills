package {{package_name}}.core.ipc

data class IpcEnvelope(
    val protocolVersion: Int,
    val requestId: String,
) {
    init {
        require(protocolVersion > 0)
        require(requestId.isNotBlank())
    }
}
