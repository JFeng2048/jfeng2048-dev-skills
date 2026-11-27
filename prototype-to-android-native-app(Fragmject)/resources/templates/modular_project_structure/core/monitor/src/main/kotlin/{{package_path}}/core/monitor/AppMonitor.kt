package {{package_name}}.core.monitor

interface AppMonitor {
    fun recordDuration(name: String, durationMillis: Long)
    fun recordFailure(name: String, throwable: Throwable)
}
