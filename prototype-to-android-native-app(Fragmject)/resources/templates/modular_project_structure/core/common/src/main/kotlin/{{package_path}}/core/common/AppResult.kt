package {{package_name}}.core.common

sealed interface AppResult<out T> {
    data class Success<T>(val value: T) : AppResult<T>
    data class Failure(val cause: Throwable) : AppResult<Nothing>
}
